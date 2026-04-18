"""
智慧渔场管理系统增强版 - 带数据推送的Flask应用
Smart Fishery Management System v2.0 - Flask with Real-time Data
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
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
    print(f"[WARN] 硬件服务导入失败: {e}")
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
    default_supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True)
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
            'default_supplier_id': self.default_supplier_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.BigInteger, primary_key=True)
    pond_id = db.Column(db.Integer, db.ForeignKey('ponds.id'), nullable=False)
    temperature = db.Column(db.Float)
    ph_value = db.Column(db.Float)
    food_value = db.Column(db.Float)
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
            'food_value': self.food_value,
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
# 用户认证模型（任务4）
# ============================================================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    full_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'supplier_id': self.supplier_id,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================
# 供应商管理模型（任务5）
# ============================================================

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    contact_person = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(255))
    registration_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    products = db.relationship('SeedlingProduct', backref='supplier', lazy='dynamic', cascade='all, delete-orphan')
    users = db.relationship('User', backref='supplier_obj', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SeedlingProduct(db.Model):
    __tablename__ = 'seedling_products'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(50))
    unit_price = db.Column(db.Float, default=0.0)
    cost_price = db.Column(db.Float)
    growth_cycle_days = db.Column(db.Integer)
    survival_rate = db.Column(db.Float)
    image_url = db.Column(db.String(255))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'product_name': self.product_name,
            'species': self.species,
            'grade': self.grade,
            'unit_price': self.unit_price,
            'cost_price': self.cost_price,
            'growth_cycle_days': self.growth_cycle_days,
            'survival_rate': self.survival_rate,
            'image_url': self.image_url,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SeedlingInventory(db.Model):
    __tablename__ = 'seedling_inventory'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('seedling_products.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'last_updated_at': self.last_updated_at.isoformat() if self.last_updated_at else None,
            'updated_by': self.updated_by
        }


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='RESTRICT'), nullable=False)
    pond_id = db.Column(db.Integer, db.ForeignKey('ponds.id', ondelete='RESTRICT'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='draft')
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', backref='created_orders')
    pond_ref = db.relationship('Pond', backref='purchase_orders')
    supplier_ref = db.relationship('Supplier', backref='purchase_orders')
    
    def to_dict(self):
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'pond_id': self.pond_id,
            'created_by': self.created_by,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'status': self.status,
            'total_amount': self.total_amount,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('seedling_products.id', ondelete='RESTRICT'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    product = db.relationship('SeedlingProduct', backref='order_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.quantity * self.unit_price,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================
# 硬件数据采集初始化
# ============================================================

def init_hardware_collection():
    """初始化硬件数据采集"""
    if not HARDWARE_SUPPORT:
        print("[WARN] 硬件支持未启用")
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
                logger.info(f"[OK] 硬件采集已绑定到: {pond.pond_name} (ID=1)")
            else:
                logger.warning("[WARN] 一号池（ID=1）不存在！")
        
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
                        food_value=parsed_data.get('food_value'),
                        dissolved_oxygen=parsed_data.get('dissolved_oxygen'),
                        salinity=parsed_data.get('salinity'),
                        ammonia_nitrogen=parsed_data.get('ammonia_nitrogen'),
                        nitrite_nitrogen=parsed_data.get('nitrite_nitrogen'),
                        timestamp=timestamp
                    )
                    logger.debug(f"✓ 传感器数据已保存: T={parsed_data.get('temperature'):.2f}°C, Food={parsed_data.get('food_value')}")

                
            except Exception as e:
                logger.error(f"数据回调处理失败: {e}")
        
        # 初始化采集器
        collector = init_collector(port='COM12', baudrate=9600, data_callback=on_hardware_data)
        
        # 启动采集
        collector.start()
        print("[OK] 硬件数据采集已启动")
        
        # 输出解析器状态
        if HARDWARE_SUPPORT:
            parser = get_parser()
            print(f"📊 解析器就绪: {parser.__class__.__name__}")
        
    except Exception as e:
        print(f"[ERR] 硬件初始化失败: {e}")


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
# 认证和权限检查（任务4）
# ============================================================
from functools import wraps

# 设置 session 密钥
app.secret_key = 'smartfishery-secret-key-2026'

def login_required(f):
    """权限检查装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def api_login_required(f):
    """API 权限检查装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': '未认证，请登录'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# 权限装饰器（任务6）
# ============================================================

def role_required(allowed_roles):
    """角色权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'status': 'error', 'message': '未认证，请登录'}), 401
            
            user = User.query.get(session['user_id'])
            if not user or user.role not in allowed_roles:
                return jsonify({'status': 'error', 'message': '您没有权限访问此资源'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def supplier_scope_check(f):
    """供应商数据隔离检查装饰器 - 确保供应商只能访问自己的数据"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': '未认证，请登录'}), 401
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 401
        
        # 管理员可以访问所有数据
        if user.role == 'admin':
            return f(*args, **kwargs)
        
        # 供应商只能访问自己的数据
        if user.role == 'supplier' and user.supplier_id:
            # 将supplier_id注入到kwargs中供路由函数使用
            kwargs['_supplier_id'] = user.supplier_id
            return f(*args, **kwargs)
        
        return jsonify({'status': 'error', 'message': '没有权限访问此数据'}), 403
    return decorated_function


# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        identity = request.form.get('identity', 'admin')  # 获取选择的身份
        
        user = User.query.filter_by(username=username).first()
        # 简单密码验证（生产环境应使用哈希）
        if user and user.password_hash == password:
            # 验证选择的身份是否与用户角色匹配
            if identity == 'admin' and user.role != 'admin':
                return render_template('login.html', error='该账号不是管理员账号，请选择"鱼苗供应商"身份')
            elif identity == 'supplier' and user.role != 'supplier':
                return render_template('login.html', error='该账号不是供应商账号，请选择"渔场管理员"身份')
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['supplier_id'] = user.supplier_id
            
            # 根据角色重定向到不同的仪表板
            if user.role == 'admin':
                return redirect(url_for('index'))
            elif user.role == 'supplier':
                return redirect(url_for('supplier_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

# 登出
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ============================================================
# 页面路由
# ============================================================

@app.route('/')
@login_required
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
                    latest_sensor.food_value or 0,
                    latest_sensor.dissolved_oxygen or 0,
                    latest_sensor.salinity or 0
                ]
            }
        else:
            water_quality_data = {'values': [0, 0, 0, 0, 0]}
        
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
                             online_devices=0, devices=[], water_quality_data={'values': [0,0,0,0,0]},
                             device_status_data={'online': 0, 'offline': 0, 'running': 0},
                             recent_data={'temperature': [0]*12, 'oxygen': [0]*12},
                             now=datetime.now())


@app.route('/ponds')
@login_required
def ponds_page():
    try:
        ponds = Pond.query.all()
        return render_template('ponds.html', ponds=ponds)
    except Exception as e:
        print(f'Ponds error: {e}')
        return render_template('ponds.html', ponds=[])


@app.route('/water-quality')
@login_required
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
                    'food_value': latest.food_value or 0,
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
@login_required
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
                'food_value': data.food_value or 0,
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
    """
    获取指定鱼池的传感器数据（支持分页和时间范围过滤）
    查询参数：page（页码），per_page（每页数量），hours（过去N小时内的数据）
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        hours = request.args.get('hours', None, type=int)
        
        query = SensorData.query.filter_by(pond_id=pond_id)
        
        # 支持时间范围过滤
        if hours:
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(SensorData.recorded_at >= cutoff_time)
        
        # 使用分页并按时间倒序排列
        pagination = query.order_by(SensorData.recorded_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'status': 'success',
            'data': [d.to_dict() for d in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/devices/<int:pond_id>', methods=['GET'])
def get_devices(pond_id):
    """
    获取指定鱼池的设备列表（支持分页）
    查询参数：page（页码，默认1），per_page（每页数量，默认20）
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 使用分页查询，优化大数据集性能
        pagination = Device.query.filter_by(pond_id=pond_id).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'status': 'success', 
            'data': [d.to_dict() for d in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
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
    """
    获取仪表板统计数据（优化：使用数据库级聚合）
    """
    try:
        # 一次查询获取多个统计值，避免多次查询
        from sqlalchemy import func
        
        stats_query = db.session.query(
            func.count(Pond.id).label('pond_count'),
            func.count(Device.id).label('total_devices'),
            func.sum(Pond.fish_count).label('total_fish_count'),
            func.sum(db.case(
                (Device.status == '在线', 1),
                else_=0
            )).label('online_devices'),
            func.sum(db.case(
                (Device.status == '运行中', 1),
                else_=0
            )).label('running_devices')
        ).outerjoin(Device).first()
        
        stats = {
            'pond_count': stats_query.pond_count or 0,
            'total_devices': stats_query.total_devices or 0,
            'total_fish_count': int(stats_query.total_fish_count or 0),
            'online_devices': stats_query.online_devices or 0,
            'running_devices': stats_query.running_devices or 0
        }
        
        return jsonify({'status': 'success', 'data': stats}), 200
    except Exception as e:
        # 如果聚合查询失败，降级到多个查询
        try:
            stats = {
                'pond_count': Pond.query.count(),
                'total_fish_count': db.session.query(db.func.sum(Pond.fish_count)).scalar() or 0,
                'total_devices': Device.query.count(),
                'online_devices': Device.query.filter_by(status='在线').count(),
                'running_devices': Device.query.filter_by(status='运行中').count()
            }
            return jsonify({'status': 'success', 'data': stats}), 200
        except Exception as e2:
            return jsonify({'status': 'error', 'message': str(e2)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取系统统计数据（优化：复用仪表板统计接口）"""
    try:
        # 复用仪表板统计，避免重复查询
        stats_response = get_dashboard_stats()
        if stats_response[1] == 200:
            return stats_response
        
        # 如果失败，降级方案
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
    """获取指定鱼池的最新传感器数据（使用索引优化查询）"""
    try:
        # 使用组合索引 idx_pond_recorded (pond_id, recorded_at) 优化查询
        # order_by + first() 比 first() 后再 order_by 更高效
        data = SensorData.query.filter_by(pond_id=pond_id)\
            .order_by(SensorData.recorded_at.desc())\
            .first()
        
        if not data:
            return jsonify({'status': 'success', 'data': None}), 200
        
        return jsonify({
            'status': 'success',
            'data': data.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 前端页面路由（任务7-9）
# ============================================================

@app.route('/supplier-dashboard', methods=['GET'])
@login_required
def supplier_dashboard():
    """供应商仪表板"""
    try:
        if session.get('role') != 'supplier':
            return redirect(url_for('login_page'))
        
        supplier_id = session.get('supplier_id')
        supplier = Supplier.query.get(supplier_id)
        
        return render_template('supplier-dashboard.html', 
                               username=session.get('username'),
                               role=session.get('role'),
                               supplier_name=supplier.name if supplier else '供应商')
    except Exception as e:
        return render_template('error.html', message=str(e)), 500


@app.route('/supplier-products', methods=['GET'])
@login_required
def supplier_products():
    """供应商产品管理"""
    try:
        if session.get('role') != 'supplier':
            return redirect(url_for('login_page'))
        
        return render_template('supplier-products.html', 
                               username=session.get('username'),
                               role=session.get('role'))
    except Exception as e:
        return render_template('error.html', message=str(e)), 500


@app.route('/supplier-orders', methods=['GET'])
@login_required
def supplier_orders():
    """供应商订单管理"""
    try:
        if session.get('role') != 'supplier':
            return redirect(url_for('login_page'))
        
        return render_template('supplier-orders.html', 
                               username=session.get('username'),
                               role=session.get('role'))
    except Exception as e:
        return render_template('error.html', message=str(e)), 500


@app.route('/supplier-stats', methods=['GET'])
@login_required
def supplier_stats():
    """供应商财务统计"""
    try:
        if session.get('role') != 'supplier':
            return redirect(url_for('login_page'))
        
        return render_template('supplier-stats.html', 
                               username=session.get('username'),
                               role=session.get('role'))
    except Exception as e:
        return render_template('error.html', message=str(e)), 500


@app.route('/seedling-management', methods=['GET'])
@login_required
def seedling_management():
    """管理员鱼苗管理中心"""
    try:
        if session.get('role') != 'admin':
            return redirect(url_for('login_page'))
        
        return render_template('seedling-management.html', 
                               username=session.get('username'),
                               role=session.get('role'))
    except Exception as e:
        return render_template('error.html', message=str(e)), 500


# ============================================================
# 供应商管理 API 注册（任务6）
# ============================================================

try:
    from supplier_api import register_supplier_apis
    register_supplier_apis(app, db, Supplier, SeedlingProduct, SeedlingInventory, PurchaseOrder, OrderItem, User, Pond)
    print("[OK] 供应商管理API已注册")
except ImportError as e:
    print(f"[WARN] 供应商API导入失败: {e}")
except Exception as e:
    print(f"[WARN] 供应商API注册失败: {e}")


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
            print(f"[WARN] 硬件采集启动失败: {e}")
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n应用正在关闭...")
        shutdown_hardware()
        print("[OK] 已正确关闭")
