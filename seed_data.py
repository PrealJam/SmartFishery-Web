"""
数据库数据初始化脚本
用于添加示例数据
"""

import sys
from datetime import datetime, timedelta
import random
from app import app, db, Pond, SensorData, Device, DeviceLog

def clear_all_data():
    """清空所有数据"""
    print("正在清空现有数据...")
    try:
        DeviceLog.query.delete()
        SensorData.query.delete()
        Device.query.delete()
        Pond.query.delete()
        db.session.commit()
        print("✓ 数据清空成功")
    except Exception as e:
        print(f"✗ 清空数据失败: {e}")
        db.session.rollback()

def add_ponds():
    """添加鱼池数据"""
    print("\n正在添加鱼池数据...")
    ponds = [
        {
            'pond_name': '一号池',
            'fish_type': '草鱼',
            'fish_count': 3500,
            'volume': 500.0,
            'status': '正常',
            'location': '北区001'
        },
        {
            'pond_name': '二号池',
            'fish_type': '鲈鱼',
            'fish_count': 2800,
            'volume': 400.0,
            'status': '正常',
            'location': '北区002'
        },
        {
            'pond_name': '三号池',
            'fish_type': '鲶鱼',
            'fish_count': 4200,
            'volume': 600.0,
            'status': '维护中',
            'location': '中区001'
        },
        {
            'pond_name': '四号池',
            'fish_type': '鲤鱼',
            'fish_count': 3000,
            'volume': 450.0,
            'status': '正常',
            'location': '中区002'
        },
        {
            'pond_name': '五号池',
            'fish_type': '鳙鱼',
            'fish_count': 2500,
            'volume': 350.0,
            'status': '正常',
            'location': '南区001'
        }
    ]
    
    try:
        for pond_data in ponds:
            pond = Pond(**pond_data)
            db.session.add(pond)
        db.session.commit()
        print(f"✓ 成功添加 {len(ponds)} 个鱼池")
        return Pond.query.all()
    except Exception as e:
        print(f"✗ 添加鱼池失败: {e}")
        db.session.rollback()
        return []

def add_devices(ponds):
    """添加设备数据"""
    print("\n正在添加设备数据...")
    devices = []
    device_types = [
        {'name': '增氧机', 'power': 750},
        {'name': '投喂机', 'power': 500},
        {'name': '水泵', 'power': 1100},
        {'name': '温控器', 'power': 300}
    ]
    
    try:
        device_id = 1
        for pond in ponds:
            # 每个鱼池添加3-4个设备
            for i, dtype in enumerate(device_types[:3]):
                device = Device(
                    pond_id=pond.id,
                    device_name=f"{pond.pond_name}-{dtype['name']}{i+1}",
                    device_type=dtype['name'],
                    device_model='标准型',
                    status='在线' if random.random() > 0.2 else '离线',
                    power_consumption=dtype['power'],
                    last_active=datetime.utcnow()
                )
                db.session.add(device)
                devices.append(device)
                device_id += 1
        
        db.session.commit()
        print(f"✓ 成功添加 {len(devices)} 个设备")
        return Device.query.all()
    except Exception as e:
        print(f"✗ 添加设备失败: {e}")
        db.session.rollback()
        return []

def add_sensor_data(ponds):
    """添加传感器水质数据"""
    print("\n正在添加水质监测数据...")
    
    try:
        # 为每个鱼池添加最近24小时的水质数据
        data_count = 0
        for pond in ponds:
            base_time = datetime.utcnow()
            for hours_ago in range(24, -1, -6):  # 每隔6小时添加一条数据
                timestamp = base_time - timedelta(hours=hours_ago)
                
                # 模拟水质参数（加入一些随机偏差）
                sensor = SensorData(
                    pond_id=pond.id,
                    temperature=round(24 + random.uniform(-2, 3), 2),
                    ph_value=round(7.5 + random.uniform(-0.5, 0.8), 2),
                    dissolved_oxygen=round(8.0 + random.uniform(-1, 1), 2),
                    salinity=round(15 + random.uniform(-3, 3), 2),
                    ammonia_nitrogen=round(2.5 + random.uniform(-0.5, 1.5), 2),
                    nitrite_nitrogen=round(1.2 + random.uniform(-0.3, 0.5), 2),
                    recorded_at=timestamp
                )
                db.session.add(sensor)
                data_count += 1
        
        db.session.commit()
        print(f"✓ 成功添加 {data_count} 条水质监测数据")
    except Exception as e:
        print(f"✗ 添加传感器数据失败: {e}")
        db.session.rollback()

def add_device_logs(devices, ponds):
    """添加设备操作日志"""
    print("\n正在添加设备操作日志...")
    
    actions = ['开启', '关闭', '报警', '自动触发', '故障检修']
    
    try:
        log_count = 0
        base_time = datetime.utcnow()
        
        for device in devices[:10]:  # 为部分设备添加日志
            for i in range(random.randint(2, 5)):  # 每个设备添加2-5条日志
                log = DeviceLog(
                    device_id=device.id,
                    pond_id=device.pond_id,
                    action=random.choice(actions),
                    operator='admin手动' if random.random() > 0.3 else '系统自动触发',
                    previous_state='停止',
                    current_state='运行中',
                    details=f'{device.device_name}已执行操作',
                    log_time=base_time - timedelta(hours=random.randint(1, 48))
                )
                db.session.add(log)
                log_count += 1
        
        db.session.commit()
        print(f"✓ 成功添加 {log_count} 条设备日志")
    except Exception as e:
        print(f"✗ 添加设备日志失败: {e}")
        db.session.rollback()

def main():
    """主函数"""
    with app.app_context():
        print("=" * 50)
        print("智慧渔场管理系统 - 数据库初始化")
        print("=" * 50)
        
        try:
            # 创建所有表
            print("\n正在创建数据库表...")
            db.create_all()
            print("✓ 数据库表创建成功")
            
            # 清空旧数据
            clear_all_data()
            
            # 添加数据
            ponds = add_ponds()
            devices = add_devices(ponds)
            add_sensor_data(ponds)
            add_device_logs(devices, ponds)
            
            print("\n" + "=" * 50)
            print("✓ 数据初始化完成！")
            print("=" * 50)
            print("\n添加的数据摘要:")
            print(f"  - 鱼池数量: {len(ponds)} 个")
            print(f"  - 设备数量: {len(devices)} 个")
            print(f"  - 可在以下地址访问系统:")
            print(f"    http://127.0.0.1:5000")
            print("\n")
            
        except Exception as e:
            print(f"\n✗ 初始化失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
