"""
智慧渔场管理系统增强版 - 带数据推送的Flask应用
Smart Fishery Management System v2.0 - Flask with Real-time Data
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import random
import logging

# 硬件服务导入
try:
    from hardware_service import init_collector, start_collection, stop_collection, get_stats as get_hardware_stats
    from storage_service import init_storage_service, get_storage_service
    from custom_parser_template import CustomATKLoraParser
    
    # 初始化解析器
    parser = CustomATKLoraParser()
    
    def parse_hardware_data(raw_bytes):
        """解析硬件数据"""
        return parser.parse(raw_bytes)
    
    def get_parser():
        """获取解析器实例"""
        return parser
    
    HARDWARE_SUPPORT = True
except ImportError as e:
    print(f"⚠️  硬件服务导入失败: {e}")
    HARDWARE_SUPPORT = False

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# Flask应用初始化
# ============================================================
app = Flask(__name__)

# 数据库配置
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_NAME = 'smart_fishery_db'

DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['JSON_AS_ASCII'] = False

db = SQLAlchemy(app)

# ============================================================
# 数据库模型
# ============================================================

class Pond(db.Model):
    __tablename__ = 'ponds'
    id = db.Column(db.Integer, primary_key=True)
    pond_name = db.Column(db.String(100), unique=True, nullable=False)
    fish_type = db.Column(db.String(50), nullable=False)
    fish_count = db.Column(db.Integer, default=0)
    volume = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='正常')
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'pond_name': self.pond_name,
            'fish_type': self.fish_type,
            'fish_count': self.fish_count,
            'volume': self.volume,
            'status': self.status,
            'location': self.location,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.BigInteger, primary_key=True)
    pond_id = db.Column(db.Integer, db.ForeignKey('ponds.id'), nullable=False)
    temperature = db.Column(db.Float)
    ph_value = db.Column(db.Float)
    dissolved_oxygen = db.Column(db.Float)
    salinity = db.Column(db.Float)
    ammonia_nitrogen = db.Column(db.Float)
    nitrite_nitrogen = db.Column(db.Float)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'pond_id': self.pond_id,
            'temperature': self.temperature,
            'ph_value': self.ph_value,
            'dissolved_oxygen': self.dissolved_oxygen,
            'salinity': self.salinity,
            'ammonia_nitrogen': self.ammonia_nitrogen,
            'nitrite_nitrogen': self.nitrite_nitrogen,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    pond_id = db.Column(db.Integer, db.ForeignKey('ponds.id'), nullable=False)
    device_name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)
    device_model = db.Column(db.String(100))
    status = db.Column(db.String(20), default='离线')
    power_consumption = db.Column(db.Float, default=0.0)
    last_active = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'pond_id': self.pond_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'device_model': self.device_model,
            'status': self.status,
            'power_consumption': self.power_consumption,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }


class DeviceLog(db.Model):
    __tablename__ = 'device_logs'
    id = db.Column(db.BigInteger, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    pond_id = db.Column(db.Integer, db.ForeignKey('ponds.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    operator = db.Column(db.String(100))
    previous_state = db.Column(db.String(20))
    current_state = db.Column(db.String(20))
    details = db.Column(db.Text)
    log_time = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# 硬件数据采集初始化
# ============================================================

def init_hardware_collection():
    """初始化硬件数据采集"""
    if not HARDWARE_SUPPORT:
        print("⚠️  硬件支持未启用")
        return
    
    try:
        # 初始化存储服务 (传递Flask应用对象)
        storage = init_storage_service(app, db, Pond, SensorData)
        
        # 硬件数据始终更新一号池（ID=1）
        pond_id = 1
        
        # 检查一号池是否存在
        with app.app_context():
            pond = Pond.query.get(1)
            if pond:
                logger.info(f"✅ 硬件采集已绑定到: {pond.pond_name} (ID=1)")
            else:
                logger.warning("⚠️  一号池（ID=1）不存在！")
        
        storage.set_default_pond(pond_id)
        
        # 数据回调函数 - 接收硬件数据后的处理
        def on_hardware_data(raw_bytes, timestamp):
            """硬件数据回调 - 解析并存储数据"""
            try:
                # 尝试解析硬件数据
                if parse_hardware_data is None:
                    logger.warning("解析器不可用")
                    return
                
                parsed_data = parse_hardware_data(raw_bytes)
                
                storage = get_storage_service()
                if storage and parsed_data:
                    # 成功解析数据，保存到数据库
                    storage.store_parsed_data(
                        pond_id=pond_id,
                        temperature=parsed_data.get('temperature'),
                        ph_value=parsed_data.get('ph_value'),
                        dissolved_oxygen=parsed_data.get('dissolved_oxygen'),
                        salinity=parsed_data.get('salinity'),
                        ammonia_nitrogen=parsed_data.get('ammonia_nitrogen'),
                        nitrite_nitrogen=parsed_data.get('nitrite_nitrogen'),
                        timestamp=timestamp
                    )
                    logger.debug(f"✓ 传感器数据已保存: T={parsed_data.get('temperature'):.2f}°C")
                
            except Exception as e:
                logger.error(f"数据回调处理失败: {e}")
        
        # 初始化采集器
        collector = init_collector(port='COM12', baudrate=9600, data_callback=on_hardware_data)
        
        # 启动采集
        collector.start()
        print("✅ 硬件数据采集已启动")
        
        # 输出解析器状态
        if HARDWARE_SUPPORT:
            parser = get_parser()
            print(f"📊 解析器就绪: {parser.__class__.__name__}")
        
    except Exception as e:
        print(f"❌ 硬件初始化失败: {e}")


# 应用启动事件
@app.before_request
def before_first_request():
    """首次请求前的初始化"""
    pass


def shutdown_hardware():
    """应用关闭时停止采集"""
    stop_collection()
    print("⏹️  硬件采集已停止")


app.teardown_appcontext(lambda exc: None)  # Placeholder

# ============================================================
# 页面路由
# ============================================================

@app.route('/')
def index():
    try:
        pond_count = Pond.query.count()
        total_fish_count = db.session.query(db.func.sum(Pond.fish_count)).scalar() or 0
        total_devices = Device.query.count()
        online_devices = Device.query.filter_by(status='在线').count()
        running_devices = Device.query.filter_by(status='运行中').count()
        
        devices_list = Device.query.all()
        devices = [{'device_name': d.device_name, 'device_type': d.device_type, 'status': d.status} for d in devices_list]
        
        # 从数据库获取最新的水质数据
        latest_sensor = SensorData.query.order_by(SensorData.recorded_at.desc()).first()
        if latest_sensor:
            water_quality_data = {
                'values': [
                    latest_sensor.temperature or 0,
                    latest_sensor.ph_value or 0,
                    latest_sensor.dissolved_oxygen or 0,
                    latest_sensor.salinity or 0
                ]
            }
        else:
            water_quality_data = {'values': [0, 0, 0, 0]}
        
        # 设备状态统计
        device_status_data = {
            'online': online_devices,
            'offline': max(0, total_devices - online_devices),
            'running': running_devices
        }
        
        # 从数据库获取最近12条传感器数据（如果有的话）
        recent_sensors = SensorData.query.order_by(SensorData.recorded_at.desc()).limit(12).all()
        if recent_sensors:
            recent_sensors.reverse()
            recent_data = {
                'temperature': [s.temperature or 0 for s in recent_sensors],
                'oxygen': [s.dissolved_oxygen or 0 for s in recent_sensors]
            }
        else:
            # 如果数据库中没有数据，使用演示数据
            recent_data = {
                'temperature': [24+i*0.5 for i in range(12)],
                'oxygen': [8.5-i*0.1 for i in range(12)]
            }
        
        return render_template('dashboard.html',
                             pond_count=pond_count,
                             total_fish_count=int(total_fish_count),
                             total_devices=total_devices,
                             online_devices=online_devices,
                             devices=devices[:8],
                             water_quality_data=water_quality_data,
                             device_status_data=device_status_data,
                             recent_data=recent_data,
                             now=datetime.now())
    except Exception as e:
        print(f'Dashboard error: {e}')
        return render_template('dashboard.html',
                             pond_count=0, total_fish_count=0, total_devices=0,
                             online_devices=0, devices=[], water_quality_data={'values': [0,0,0,0]},
                             device_status_data={'online': 0, 'offline': 0, 'running': 0},
                             recent_data={'temperature': [0]*12, 'oxygen': [0]*12},
                             now=datetime.now())


@app.route('/ponds')
def ponds_page():
    try:
        ponds = Pond.query.all()
        return render_template('ponds.html', ponds=ponds)
    except Exception as e:
        print(f'Ponds error: {e}')
        return render_template('ponds.html', ponds=[])


@app.route('/water-quality')
def water_quality_page():
    try:
        ponds = Pond.query.all()
        
        # 获取各鱼池的最新水质数据
        pond_quality_data = {}
        for pond in ponds:
            latest = SensorData.query.filter_by(pond_id=pond.id).order_by(SensorData.recorded_at.desc()).first()
            if latest:
                pond_quality_data[pond.id] = {
                    'temperature': latest.temperature or 0,
                    'ph_value': latest.ph_value or 0,
                    'dissolved_oxygen': latest.dissolved_oxygen or 0,
                    'salinity': latest.salinity or 0,
                    'ammonia_nitrogen': latest.ammonia_nitrogen or 0,
                    'nitrite_nitrogen': latest.nitrite_nitrogen or 0,
                    'recorded_at': latest.recorded_at.strftime('%Y-%m-%d %H:%M:%S') if latest.recorded_at else '未知'
                }
        
        return render_template('water_quality.html', 
                             ponds=ponds,
                             pond_quality_data=pond_quality_data)
    except Exception as e:
        print(f'Water quality error: {e}')
        return render_template('water_quality.html', ponds=[], pond_quality_data={})


@app.route('/devices')
def devices_page():
    try:
        devices = Device.query.all()
        return render_template('devices.html', devices=devices)
    except Exception as e:
        print(f'Devices error: {e}')
        return render_template('devices.html', devices=[])


# ============================================================
# API路由
# ============================================================

@app.route('/api/dashboard-refresh', methods=['GET'])
def dashboard_refresh():
    """刷新仪表板所有数据"""
    try:
        pond_count = Pond.query.count()
        total_fish_count = db.session.query(db.func.sum(Pond.fish_count)).scalar() or 0
        total_devices = Device.query.count()
        online_devices = Device.query.filter_by(status='在线').count()
        running_devices = Device.query.filter_by(status='运行中').count()
        
        # 获取最新水质数据
        latest_sensor = SensorData.query.order_by(SensorData.recorded_at.desc()).first()
        water_quality = None
        if latest_sensor:
            water_quality = {
                'temperature': latest_sensor.temperature or 0,
                'ph_value': latest_sensor.ph_value or 0,
                'dissolved_oxygen': latest_sensor.dissolved_oxygen or 0,
                'salinity': latest_sensor.salinity or 0
            }
        
        # 获取最新的设备列表
        devices_list = Device.query.limit(8).all()
        devices = [{'device_name': d.device_name, 'device_type': d.device_type, 'status': d.status} for d in devices_list]
        
        # 获取最近12条传感器数据
        recent_sensors = SensorData.query.order_by(SensorData.recorded_at.desc()).limit(12).all()
        recent_data = {
            'temperature': [s.temperature or 0 for s in reversed(recent_sensors)],
            'oxygen': [s.dissolved_oxygen or 0 for s in reversed(recent_sensors)]
        }
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'data': {
                'pond_count': pond_count,
                'total_fish_count': int(total_fish_count),
                'total_devices': total_devices,
                'online_devices': online_devices,
                'running_devices': running_devices,
                'water_quality': water_quality,
                'devices': devices,
                'recent_data': recent_data
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/water-quality-refresh/<int:pond_id>', methods=['GET'])
def water_quality_refresh(pond_id):
    """刷新指定鱼池的水质数据"""
    try:
        data = SensorData.query.filter_by(pond_id=pond_id).order_by(SensorData.recorded_at.desc()).first()
        if not data:
            return jsonify({'status': 'error', 'message': '该鱼池暂无数据'}), 404
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'data': {
                'temperature': data.temperature or 0,
                'ph_value': data.ph_value or 0,
                'dissolved_oxygen': data.dissolved_oxygen or 0,
                'salinity': data.salinity or 0,
                'ammonia_nitrogen': data.ammonia_nitrogen or 0,
                'nitrite_nitrogen': data.nitrite_nitrogen or 0,
                'recorded_at': data.recorded_at.strftime('%H:%M:%S') if data.recorded_at else '未知'
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ponds/add', methods=['POST'])
def add_pond():
    """添加新鱼池"""
    try:
        data = request.get_json()
        pond_name = data.get('pond_name')
        fish_type = data.get('fish_type')
        fish_count = data.get('fish_count', 0)
        volume = data.get('volume', 0)
        location = data.get('location', '')
        
        # 验证必填字段
        if not pond_name or not fish_type:
            return jsonify({'status': 'error', 'message': '鱼池名称和鱼类类型为必填项'}), 400
        
        # 检查鱼池名称是否已存在
        existing_pond = Pond.query.filter_by(pond_name=pond_name).first()
        if existing_pond:
            return jsonify({'status': 'error', 'message': '该鱼池名称已存在'}), 400
        
        pond = Pond(
            pond_name=pond_name,
            fish_type=fish_type,
            fish_count=int(fish_count),
            volume=float(volume),
            location=location,
            status='正常'
        )
        db.session.add(pond)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '鱼池添加成功',
            'data': pond.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ponds/<int:pond_id>/edit', methods=['POST'])
def edit_pond(pond_id):
    """编辑鱼池信息"""
    try:
        pond = Pond.query.get(pond_id)
        if not pond:
            return jsonify({'status': 'error', 'message': '鱼池不存在'}), 404
        
        data = request.get_json()
        pond.pond_name = data.get('pond_name', pond.pond_name)
        pond.fish_type = data.get('fish_type', pond.fish_type)
        pond.fish_count = int(data.get('fish_count', pond.fish_count))
        pond.volume = float(data.get('volume', pond.volume))
        pond.location = data.get('location', pond.location)
        
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': '鱼池信息更新成功',
            'data': pond.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ponds/<int:pond_id>/delete', methods=['DELETE'])
def delete_pond(pond_id):
    """删除鱼池"""
    try:
        pond = Pond.query.get(pond_id)
        if not pond:
            return jsonify({'status': 'error', 'message': '鱼池不存在'}), 404
        
        # 删除相关数据
        SensorData.query.filter_by(pond_id=pond_id).delete()
        Device.query.filter_by(pond_id=pond_id).delete()
        DeviceLog.query.filter_by(pond_id=pond_id).delete()
        db.session.delete(pond)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '鱼池删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'success', 'message': '系统正常运行'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ponds', methods=['GET'])
def get_ponds():
    try:
        ponds = Pond.query.all()
        return jsonify({'status': 'success', 'data': [p.to_dict() for p in ponds]}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ponds/<int:pond_id>', methods=['GET'])
def get_pond(pond_id):
    try:
        pond = Pond.query.get(pond_id)
        if not pond:
            return jsonify({'status': 'error', 'message': '鱼池不存在'}), 404
        return jsonify({'status': 'success', 'data': pond.to_dict()}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/sensor-data/<int:pond_id>', methods=['GET'])
def get_sensor_data(pond_id):
    try:
        data = SensorData.query.filter_by(pond_id=pond_id).order_by(SensorData.recorded_at.desc()).first()
        if not data:
            return jsonify({'status': 'success', 'data': None}), 200
        return jsonify({'status': 'success', 'data': data.to_dict()}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/devices/<int:pond_id>', methods=['GET'])
def get_devices(pond_id):
    try:
        devices = Device.query.filter_by(pond_id=pond_id).all()
        return jsonify({'status': 'success', 'data': [d.to_dict() for d in devices]}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/devices/<int:device_id>/control', methods=['POST'])
def control_device(device_id):
    try:
        action = request.json.get('action')
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'status': 'error', 'message': '设备不存在'}), 404
        
        device.status = '运行中' if action == 'start' else '停止'
        device.last_active = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'设备{action}成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    try:
        stats = {
            'pond_count': Pond.query.count(),
            'total_fish_count': db.session.query(db.func.sum(Pond.fish_count)).scalar() or 0,
            'total_devices': Device.query.count(),
            'online_devices': Device.query.filter_by(status='在线').count(),
            'running_devices': Device.query.filter_by(status='运行中').count()
        }
        return jsonify({'status': 'success', 'data': stats}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    try:
        stats = {
            'pond_count': Pond.query.count(),
            'total_fish_count': int(db.session.query(db.func.sum(Pond.fish_count)).scalar() or 0),
            'total_devices': Device.query.count(),
            'online_devices': Device.query.filter_by(status='在线').count()
        }
        return jsonify({'status': 'success', 'data': stats}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 硬件监控API
# ============================================================

@app.route('/api/hardware/status', methods=['GET'])
def get_hardware_status():
    """获取硬件采集状态"""
    try:
        if not HARDWARE_SUPPORT:
            return jsonify({'status': 'error', 'message': '硬件支持未启用'}), 500
        
        stats = get_hardware_stats()
        
        # 添加解析器统计
        if 'data' in stats and HARDWARE_SUPPORT:
            try:
                parser = get_parser()
                stats['data']['parser_stats'] = parser.get_stats()
            except:
                pass
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hardware/start', methods=['POST'])
def hardware_start():
    """启动硬件采集"""
    try:
        if not HARDWARE_SUPPORT:
            return jsonify({'status': 'error', 'message': '硬件支持未启用'}), 500
        
        start_collection()
        return jsonify({
            'status': 'success',
            'message': '硬件采集已启动'
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hardware/stop', methods=['POST'])
def hardware_stop():
    """停止硬件采集"""
    try:
        stop_collection()
        return jsonify({
            'status': 'success',
            'message': '硬件采集已停止'
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/sensor-data/latest/<int:pond_id>', methods=['GET'])
def get_latest_sensor_data(pond_id):
    """获取指定鱼池的最新传感器数据"""
    try:
        data = SensorData.query.filter_by(pond_id=pond_id).order_by(SensorData.recorded_at.desc()).first()
        if not data:
            return jsonify({'status': 'success', 'data': None}), 200
        
        return jsonify({
            'status': 'success',
            'data': data.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 主程序入口
# ============================================================

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print('数据库表已创建或已存在')
        except Exception as e:
            print(f'创建表失败: {e}')
    
    print('智慧渔场管理系统启动中...')
    print('访问地址: http://127.0.0.1:5000')
    print('按 Ctrl+C 停止服务')
    
    # 启动硬件采集
    with app.app_context():
        try:
            init_hardware_collection()
        except Exception as e:
            print(f"⚠️  硬件采集启动失败: {e}")
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n应用正在关闭...")
        shutdown_hardware()
        print("✅ 已正确关闭")
