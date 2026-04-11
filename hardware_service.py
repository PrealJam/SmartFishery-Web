#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬件数据采集服务 - ATK-LORA-01 模块
Hardware Data Collection Service for ATK-LORA-01
"""

import serial
import threading
import time
import logging
from datetime import datetime
from typing import Optional, Callable

# 硬件协议解析器
try:
    from atk_lora_parser import parse_hardware_data
except ImportError:
    parse_hardware_data = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HardwareDataCollector:
    """硬件数据采集器 - 从COM12读取ATK-LORA-01数据"""
    
    def __init__(self, 
                 port='COM12', 
                 baudrate=9600,
                 data_callback: Optional[Callable] = None):
        """
        初始化采集器
        
        Args:
            port: COM端口
            baudrate: 波特率
            data_callback: 数据回调函数，签名 callback(raw_bytes, timestamp)
        """
        self.port = port
        self.baudrate = baudrate
        self.data_callback = data_callback
        
        self.ser = None
        self.running = False
        self.thread = None
        
        self.stats = {
            'total_bytes': 0,
            'frames_collected': 0,
            'last_frame_time': None,
            'errors': 0
        }
    
    def connect(self) -> bool:
        """连接到硬件设备"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=1
            )
            logger.info(f"✅ 已连接到 {self.port} @ {self.baudrate} baud")
            return True
        
        except serial.SerialException as e:
            logger.error(f"❌ 连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("✅ 串口已关闭")
    
    def start(self):
        """启动数据采集线程"""
        if self.running:
            logger.warning("采集已在运行")
            return
        
        # 尝试连接，最多重试3次
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            if self.connect():
                break
            retry_count += 1
            if retry_count < max_retries:
                logger.info(f"⏳ {retry_count}秒后重试连接...")
                time.sleep(retry_count)
        
        if not self.ser or not self.ser.is_open:
            logger.error("❌ 无法连接到硬件设备，采集未启动")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=False)
        self.thread.start()
        logger.info("📡 数据采集线程已启动")
    
    def stop(self):
        """停止数据采集"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️  数据采集已停止")
    
    def _read_loop(self):
        """数据读取循环"""
        frame_buffer = bytearray()
        last_log_time = datetime.now()
        debug_shown = False
        
        try:
            logger.info("🔍 开始监听 COM12 数据...")
            while self.running:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    try:
                        data = self.ser.read(self.ser.in_waiting)
                        if data:
                            frame_buffer.extend(data)
                            self.stats['total_bytes'] += len(data)
                            
                            # 首次收到数据时，显示原始数据用于诊断
                            if not debug_shown and len(frame_buffer) > 50:
                                hex_sample = frame_buffer[:100].hex()
                                logger.info(f"🔍 原始数据样本 (HEX): {hex_sample}")
                                # 尝试显示可打印字符
                                try:
                                    text_sample = frame_buffer[:100].decode('gb2312', errors='ignore')
                                    logger.info(f"🔍 原始数据样本 (文本): {repr(text_sample[:50])}")
                                except:
                                    pass
                                debug_shown = True
                            
                            # 每 10 秒输出一次统计
                            now = datetime.now()
                            if (now - last_log_time).total_seconds() > 10:
                                logger.info(f"📊 采集统计: 已收 {self.stats['total_bytes']} 字节, {self.stats['frames_collected']} 帧, 缓冲区: {len(frame_buffer)} 字节")
                                last_log_time = now
                            
                            # 尝试提取完整帧 - 支持多种分隔符
                            while len(frame_buffer) > 0:
                                # 查找多种可能的分隔符
                                newline_pos = frame_buffer.find(b'\n')
                                tab_pos = frame_buffer.find(b'\t')
                                cr_pos = frame_buffer.find(b'\r')
                                
                                # 找到最近的分隔符
                                delim_positions = []
                                if newline_pos >= 0:
                                    delim_positions.append(('\\n', newline_pos, 1))
                                if tab_pos >= 0:
                                    delim_positions.append(('\\t', tab_pos, 1))
                                if cr_pos >= 0:
                                    delim_positions.append(('\\r', cr_pos, 1))
                                
                                if not delim_positions:
                                    # 没有找到分隔符，如果缓冲区太长就认为可能是一帧坏数据
                                    if len(frame_buffer) > 500:
                                        logger.warning(f"⚠️  缓冲区超大 ({len(frame_buffer)} 字节)，未找到分隔符，可能数据格式不对")
                                        logger.warning(f"    首 50 字节: {frame_buffer[:50].hex()}")
                                        # 清空缓冲区
                                        frame_buffer.clear()
                                    break
                                
                                # 使用最近的分隔符
                                delim_type, delim_pos, delim_len = min(delim_positions, key=lambda x: x[1])
                                
                                # 提取一行数据
                                frame = bytes(frame_buffer[:delim_pos])
                                # 移除已处理的数据和分隔符
                                frame_buffer = frame_buffer[delim_pos+delim_len:]
                                
                                # 跳过空行
                                if not frame:
                                    continue
                                
                                self.stats['frames_collected'] += 1
                                self.stats['last_frame_time'] = datetime.now()
                                
                                logger.debug(f"[收到帧] {len(frame)} 字节")
                                
                                # 调用回调函数处理数据
                                if self.data_callback:
                                    try:
                                        self.data_callback(frame, datetime.now())
                                    except Exception as e:
                                        logger.error(f"回调函数错误: {e}")
                                        self.stats['errors'] += 1
                    
                    except serial.SerialException as e:
                        logger.error(f"串口读取错误: {e}")
                        self.stats['errors'] += 1
                        if self.running:
                            time.sleep(1)  # 重新连接前等待
                
                else:
                    time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"读取循环错误: {e}")
            self.stats['errors'] += 1
        
        finally:
            logger.info("📊 读取循环已结束")
    
    def get_stats(self) -> dict:
        """获取采集统计信息"""
        return {
            'status': 'running' if self.running else 'stopped',
            'port': self.port,
            'baudrate': self.baudrate,
            'total_bytes': self.stats['total_bytes'],
            'frames_collected': self.stats['frames_collected'],
            'last_frame_time': self.stats['last_frame_time'].isoformat() if self.stats['last_frame_time'] else None,
            'errors': self.stats['errors']
        }


# 全局采集器实例
_collector = None


def init_collector(port='COM12', baudrate=19200, data_callback=None) -> HardwareDataCollector:
    """初始化全局采集器"""
    global _collector
    
    if _collector is not None:
        logger.warning("采集器已初始化")
        return _collector
    
    _collector = HardwareDataCollector(port, baudrate, data_callback)
    return _collector


def get_collector() -> Optional[HardwareDataCollector]:
    """获取全局采集器实例"""
    return _collector


def start_collection():
    """启动全局采集"""
    if _collector:
        _collector.start()
    else:
        logger.error("采集器未初始化")


def stop_collection():
    """停止全局采集"""
    if _collector:
        _collector.stop()


def get_stats() -> dict:
    """获取采集统计"""
    if _collector:
        return _collector.get_stats()
    return {'status': 'not_initialized'}
