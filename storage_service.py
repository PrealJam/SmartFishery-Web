#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传感器数据存储服务
Sensor Data Storage Service
"""

import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SensorDataStorage:
    """传感器数据存储服务"""
    
    def __init__(self, app, db, Pond, SensorData):
        """
        初始化存储服务
        
        Args:
            app: Flask应用实例
            db: SQLAlchemy数据库实例
            Pond: Pond模型
            SensorData: SensorData模型
        """
        self.app = app
        self.db = db
        self.Pond = Pond
        self.SensorData = SensorData
        self.default_pond_id = None
    
    def set_default_pond(self, pond_id: int):
        """设置默认鱼池ID"""
        self.default_pond_id = pond_id
        logger.info(f"默认鱼池已设为: {pond_id}")
    
    def store_raw_data(self, 
                       raw_bytes: bytes, 
                       timestamp: datetime,
                       pond_id: Optional[int] = None) -> bool:
        """
        存储原始数据到数据库
        
        Args:
            raw_bytes: 原始二进制数据
            timestamp: 时间戳
            pond_id: 鱼池ID（如果为None，使用默认值）
        
        Returns:
            True if success, False otherwise
        """
        try:
            # 使用应用上下文
            with self.app.app_context():
                # 使用默认鱼池ID
                if pond_id is None:
                    pond_id = self.default_pond_id
                
                if pond_id is None:
                    logger.warning("没有设置鱼池ID，无法存储数据")
                    return False
                
                # 先检查鱼池是否存在
                pond = self.Pond.query.get(pond_id)
                if not pond:
                    logger.error(f"鱼池{pond_id}不存在")
                    return False
                
                # 暂时先存储原始hex值到备注字段
                # 后续有了解析规则后再提取具体传感器值
                sensor_data = self.SensorData(
                    pond_id=pond_id,
                    temperature=0.0,  # 暂时使用0
                    ph_value=0.0,
                    dissolved_oxygen=0.0,
                    salinity=0.0,
                    ammonia_nitrogen=0.0,
                    nitrite_nitrogen=0.0,
                    recorded_at=timestamp
                )
                
                # TODO: 为SensorData模型添加raw_data字段存储原始hex
                
                self.db.session.add(sensor_data)
                self.db.session.commit()
                
                logger.debug(f"✓ 已保存数据到鱼池{pond_id}")
                return True
        
        except Exception as e:
            logger.error(f"✗ 数据存储失败: {e}")
            try:
                self.db.session.rollback()
            except:
                pass
            return False
    
    def store_parsed_data(self,
                         pond_id: int,
                         temperature: float = None,
                         ph_value: float = None,
                         dissolved_oxygen: float = None,
                         salinity: float = None,
                         ammonia_nitrogen: float = None,
                         nitrite_nitrogen: float = None,
                         timestamp: datetime = None) -> bool:
        """
        存储解析后的传感器数据（UPSERT 模式）
        - 如果该鱼池已有数据，则更新（UPDATE）
        - 如果该鱼池没有数据，则新增（INSERT）
        这样保保证每个鱼池只有一条最新数据记录
        
        Args:
            pond_id: 鱼池ID
            temperature: 温度
            ph_value: pH值
            dissolved_oxygen: 溶解氧
            salinity: 盐度
            ammonia_nitrogen: 氨氮
            nitrite_nitrogen: 亚硝酸盐
            timestamp: 时间戳
        
        Returns:
            True if success, False otherwise
        """
        try:
            with self.app.app_context():
                if timestamp is None:
                    timestamp = datetime.utcnow()
                
                # 检查鱼池
                pond = self.Pond.query.get(pond_id)
                if not pond:
                    logger.error(f"鱼池{pond_id}不存在")
                    return False
                
                # UPSERT 模式：先查询是否有这个鱼池的数据
                existing_record = self.SensorData.query.filter_by(pond_id=pond_id).first()
                
                if existing_record:
                    # 存在则更新（UPDATE）
                    existing_record.temperature = temperature
                    existing_record.ph_value = ph_value
                    existing_record.dissolved_oxygen = dissolved_oxygen
                    existing_record.salinity = salinity
                    existing_record.ammonia_nitrogen = ammonia_nitrogen
                    existing_record.nitrite_nitrogen = nitrite_nitrogen
                    existing_record.recorded_at = timestamp
                    
                    self.db.session.commit()
                    logger.info(f"♻️  已更新{pond.pond_name}的数据: T={temperature}°C, pH={ph_value}, DO={dissolved_oxygen}mg/L")
                else:
                    # 不存在则新增（INSERT）
                    sensor_data = self.SensorData(
                        pond_id=pond_id,
                        temperature=temperature,
                        ph_value=ph_value,
                        dissolved_oxygen=dissolved_oxygen,
                        salinity=salinity,
                        ammonia_nitrogen=ammonia_nitrogen,
                        nitrite_nitrogen=nitrite_nitrogen,
                        recorded_at=timestamp
                    )
                    
                    self.db.session.add(sensor_data)
                    self.db.session.commit()
                    logger.info(f"✨ 已新增{pond.pond_name}的数据: T={temperature}°C, pH={ph_value}, DO={dissolved_oxygen}mg/L")
                
                return True
        
        except Exception as e:
            logger.error(f"✗ 数据存储失败: {e}")
            try:
                self.db.session.rollback()
            except:
                pass
            return False


# 全局存储服务实例
_storage_service = None


def init_storage_service(app, db, Pond, SensorData) -> SensorDataStorage:
    """初始化全局存储服务"""
    global _storage_service
    
    if _storage_service is not None:
        logger.warning("存储服务已初始化")
        return _storage_service
    
    _storage_service = SensorDataStorage(app, db, Pond, SensorData)
    logger.info("✅ 存储服务已初始化")
    return _storage_service


def get_storage_service() -> Optional[SensorDataStorage]:
    """获取全局存储服务"""
    return _storage_service
