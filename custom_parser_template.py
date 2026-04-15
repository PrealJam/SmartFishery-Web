#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATK-LORA-01 文本协议解析器
处理格式: 温度值:0.1 PH值:7.0 食物值:46 Salinity:15.0
"""

import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class CustomATKLoraParser:
    """文本协议解析器 - 处理ATK-LORA-01的文本输出格式"""
    
    # 字段映射表 - 更新为7种参数
    FIELD_MAPPING = {
        '温度值': 'temperature',
        '温度': 'temperature',
        'PH值': 'ph_value',
        'pH值': 'ph_value',
        'PH': 'ph_value',
        'pH': 'ph_value',
        '食物值': 'food_value',
        '食物': 'food_value',
        'Food': 'food_value',
        'Salinity': 'salinity',
        '盐度': 'salinity',
        '氧气值': 'dissolved_oxygen',
        '溶解氧': 'dissolved_oxygen',
        'DO': 'dissolved_oxygen',
        'Oxygen': 'dissolved_oxygen',
        'NH3': 'ammonia_nitrogen',
        '氨氮': 'ammonia_nitrogen',
        'Ammonia': 'ammonia_nitrogen',
        'NO2': 'nitrite_nitrogen',
        '硝酸': 'nitrite_nitrogen',
        '亚硝': 'nitrite_nitrogen',
        'Nitrite': 'nitrite_nitrogen',
    }
    
    # 传感器数据的有效范围（用于验证）
    VALID_RANGES = {
        'temperature': (-10, 60),
        'ph_value': (0, 14),
        'food_value': (0, 100),
        'dissolved_oxygen': (0, 100),
        'salinity': (0, 40),
        'ammonia_nitrogen': (0, 100),
        'nitrite_nitrogen': (0, 100)
    }
    
    def __init__(self):
        self.frame_count = 0
        self.parse_errors = 0
    
    def parse(self, raw_bytes: bytes) -> Optional[Dict[str, float]]:
        """解析文本格式的硬件数据"""
        try:
            self.frame_count += 1
            
            # 将字节转换为字符串 - 支持 GB2312 和 UTF-8 双编码
            text = None
            for encoding in ['gb2312', 'gbk', 'utf-8']:
                try:
                    text = raw_bytes.decode(encoding).strip()
                    if text and len(text) > 3:
                        break
                except:
                    continue
            
            if not text:
                text = raw_bytes.decode('utf-8', errors='ignore').strip()
            
            if not text:
                logger.debug(f"[Frame {self.frame_count}] 空数据（可能硬件未发送）")
                return None
            
            # 显示原始十六进制和文本
            hex_str = raw_bytes.hex()
            logger.info(f"[Frame {self.frame_count}] 原始数据 HEX: {hex_str[:80]}")
            logger.info(f"[Frame {self.frame_count}] 原始文本: {text}")
            
            data = {}
            
            # 分割文本（以空格分隔）
            parts = text.split()
            
            for part in parts:
                if ':' not in part:
                    continue
                
                try:
                    key, value_str = part.split(':', 1)
                    value = float(value_str)
                    
                    # 查找映射的字段名
                    field_name = None
                    for hw_field, std_field in self.FIELD_MAPPING.items():
                        if hw_field in key:
                            field_name = std_field
                            break
                    
                    if field_name:
                        data[field_name] = value
                        logger.info(f"   ✓ {field_name} = {value}")
                
                except ValueError:
                    logger.debug(f"   无法解析字段值: {part}")
                    continue
            
            # 补充缺失的字段（用0填充）
            for field in ['temperature', 'ph_value', 'dissolved_oxygen', 'salinity', 'ammonia_nitrogen', 'nitrite_nitrogen']:
                if field not in data:
                    data[field] = 0
            
            # 检查是否有任何可识别的字段
            if len(data) == 0:
                logger.warning(f"⚠️  无法识别任何数据字段")
                self.parse_errors += 1
                return None
            
            # 验证数据范围
            for field, value in data.items():
                if field in self.VALID_RANGES:
                    min_v, max_v = self.VALID_RANGES[field]
                    margin = (max_v - min_v) * 1.0
                    if not ((min_v - margin) <= value <= (max_v + margin)):
                        logger.warning(f"⚠️  {field} 值 {value} 可能超出范围 ({min_v}~{max_v})")
            
            logger.info(f"✅ 解析成功: T={data.get('temperature')}°C, pH={data.get('ph_value')}, DO={data.get('dissolved_oxygen')}, 盐={data.get('salinity')}")
            return data
            
        except Exception as e:
            logger.error(f"❌ 解析失败: {e}")
            self.parse_errors += 1
            return None
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'frames_processed': self.frame_count,
            'parse_errors': self.parse_errors,
            'success_rate': (self.frame_count - self.parse_errors) / max(1, self.frame_count) if self.frame_count > 0 else 0
        }


# 全局实例
_custom_parser = None


def get_custom_parser() -> CustomATKLoraParser:
    """获取全局解析器实例"""
    global _custom_parser
    if _custom_parser is None:
        _custom_parser = CustomATKLoraParser()
    return _custom_parser


def parse_hardware_data(raw_bytes: bytes) -> Optional[dict]:
    """便捷函数：解析硬件数据"""
    parser = get_custom_parser()
    return parser.parse(raw_bytes)

