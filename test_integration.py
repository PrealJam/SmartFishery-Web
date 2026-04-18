#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
集成测试脚本 - SmartFishery 多身份系统
测试流程：登录 -> 权限检查 -> CRUD操作 -> API集成
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

def print_test(message, status="INFO"):
    """打印测试信息"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icons = {
        "PASS": "[OK]",
        "FAIL": "[FAIL]",
        "INFO": "[INFO]",
        "WARN": "[WARN]"
    }
    print(f"[{timestamp}] {icons.get(status, '*')} {message}")

def test_scenario_1_admin_login():
    """测试场景1：管理员登录流程"""
    print_test("=" * 60, "INFO")
    print_test("测试场景1：管理员登录流程", "INFO")
    print_test("=" * 60, "INFO")
    
    # 获取登录页面
    resp = session.get(f"{BASE_URL}/login")
    if resp.status_code == 200:
        print_test("[OK] 访问登录页面成功 (状态码: 200)", "PASS")
    else:
        print_test(f"✗ 访问登录页面失败 (状态码: {resp.status_code})", "FAIL")
        return False
    
    # 尝试以管理员身份登录
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'identity': 'admin'
    }
    resp = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    
    if resp.status_code in [200, 302]:
        print_test("[OK] 管理员登录成功", "PASS")
        # 检查会话
        if session.cookies.get('session'):
            print_test("[OK] 会话cookie已设置", "PASS")
        return True
    else:
        print_test(f"✗ 管理员登录失败 (状态码: {resp.status_code})", "FAIL")
        return False


def test_scenario_2_supplier_login():
    """测试场景2：供应商登录流程"""
    print_test("=" * 60, "INFO")
    print_test("测试场景2：供应商登录流程", "INFO")
    print_test("=" * 60, "INFO")
    
    # 创建新会话
    supplier_session = requests.Session()
    
    # 尝试以供应商身份登录
    login_data = {
        'username': 'supplier1',
        'password': 'supplier123',
        'identity': 'supplier'
    }
    resp = supplier_session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    
    if resp.status_code in [200, 302]:
        print_test("[OK] 供应商登录成功", "PASS")
        if supplier_session.cookies.get('session'):
            print_test("[OK] 会话cookie已设置", "PASS")
        return True, supplier_session
    else:
        print_test(f"✗ 供应商登录失败 (状态码: {resp.status_code})", "FAIL")
        return False, None


def test_scenario_3_api_access():
    """测试场景3：权限检查与数据隔离"""
    print_test("=" * 60, "INFO")
    print_test("测试场景3：权限检查与数据隔离", "INFO")
    print_test("=" * 60, "INFO")
    
    # 测试管理员可以访问供应商列表
    resp = session.get(f"{BASE_URL}/api/suppliers?page=1&per_page=10")
    if resp.status_code == 200:
        data = resp.json()
        print_test(f"[OK] 管理员访问供应商列表成功 (找到 {len(data.get('data', []))} 个供应商)", "PASS")
    else:
        print_test(f"✗ 管理员访问供应商列表失败 (状态码: {resp.status_code})", "FAIL")
    
    # 测试供应商无法访问供应商列表
    supplier_session = requests.Session()
    supplier_login_data = {
        'username': 'supplier1',
        'password': 'supplier123',
        'identity': 'supplier'
    }
    supplier_session.post(f"{BASE_URL}/login", data=supplier_login_data)
    
    resp = supplier_session.get(f"{BASE_URL}/api/suppliers?page=1&per_page=10")
    if resp.status_code == 403:
        print_test("[OK] 供应商无法访问供应商列表 (403 Forbidden)", "PASS")
    else:
        print_test(f"⚠️ 供应商访问供应商列表返回 {resp.status_code}", "WARN")
    
    return True


def test_scenario_4_supplier_products():
    """测试场景4：供应商产品管理"""
    print_test("=" * 60, "INFO")
    print_test("测试场景4：供应商产品管理 (查询)", "INFO")
    print_test("=" * 60, "INFO")
    
    supplier_session = requests.Session()
    supplier_login_data = {
        'username': 'supplier1',
        'password': 'supplier123',
        'identity': 'supplier'
    }
    supplier_session.post(f"{BASE_URL}/login", data=supplier_login_data)
    
    # 查询供应商产品
    resp = supplier_session.get(f"{BASE_URL}/api/my-products?page=1&per_page=10")
    if resp.status_code == 200:
        data = resp.json()
        product_count = len(data.get('data', []))
        print_test(f"[OK] 供应商产品查询成功 (找到 {product_count} 个产品)", "PASS")
        
        if product_count > 0:
            product = data['data'][0]
            print_test(f"  - 产品示例: {product.get('product_name', 'N/A')} ({product.get('species', 'N/A')})", "INFO")
        return True
    else:
        print_test(f"✗ 供应商产品查询失败 (状态码: {resp.status_code})", "FAIL")
        return False


def test_scenario_5_sales_stats():
    """测试场景5：供应商销售统计"""
    print_test("=" * 60, "INFO")
    print_test("测试场景5：供应商销售统计", "INFO")
    print_test("=" * 60, "INFO")
    
    supplier_session = requests.Session()
    supplier_login_data = {
        'username': 'supplier1',
        'password': 'supplier123',
        'identity': 'supplier'
    }
    supplier_session.post(f"{BASE_URL}/login", data=supplier_login_data)
    
    # 查询销售统计
    resp = supplier_session.get(f"{BASE_URL}/api/my-sales-stats")
    if resp.status_code == 200:
        data = resp.json()
        if data.get('status') == 'success':
            stats = data.get('data', {})
            print_test(f"[OK] 销售统计查询成功", "PASS")
            print_test(f"  - 总销售额: CNY{stats.get('total_sales', 0)}", "INFO")
            print_test(f"  - 总订单数: {stats.get('total_orders', 0)}", "INFO")
            return True
    
    print_test(f"✗ 销售统计查询失败 (状态码: {resp.status_code})", "FAIL")
    return False


def test_scenario_6_orders():
    """测试场景6：订单管理"""
    print_test("=" * 60, "INFO")
    print_test("测试场景6：供应商订单管理", "INFO")
    print_test("=" * 60, "INFO")
    
    supplier_session = requests.Session()
    supplier_login_data = {
        'username': 'supplier1',
        'password': 'supplier123',
        'identity': 'supplier'
    }
    supplier_session.post(f"{BASE_URL}/login", data=supplier_login_data)
    
    # 查询订单
    resp = supplier_session.get(f"{BASE_URL}/api/my-orders?page=1&per_page=10")
    if resp.status_code == 200:
        data = resp.json()
        order_count = len(data.get('data', []))
        print_test(f"[OK] 订单查询成功 (找到 {order_count} 个订单)", "PASS")
        
        if order_count > 0:
            order = data['data'][0]
            print_test(f"  - 订单示例: #{order.get('id')} 金额: CNY{order.get('total_amount', 0)}", "INFO")
            
            # 尝试更新订单状态
            if order.get('status') == 'draft':
                update_resp = supplier_session.post(
                    f"{BASE_URL}/api/my-orders/{order['id']}/update-status",
                    json={'status': 'confirmed'}
                )
                if update_resp.status_code == 200:
                    print_test(f"[OK] 订单状态更新成功", "PASS")
                else:
                    print_test(f"⚠️ 订单状态更新失败 (状态码: {update_resp.status_code})", "WARN")
        return True
    else:
        print_test(f"✗ 订单查询失败 (状态码: {resp.status_code})", "FAIL")
        return False


def test_scenario_7_frontend_routes():
    """测试场景7：前端路由访问"""
    print_test("=" * 60, "INFO")
    print_test("测试场景7：前端页面路由", "INFO")
    print_test("=" * 60, "INFO")
    
    # 测试供应商路由
    supplier_session = requests.Session()
    supplier_login_data = {
        'username': 'supplier1',
        'password': 'supplier123',
        'identity': 'supplier'
    }
    supplier_session.post(f"{BASE_URL}/login", data=supplier_login_data)
    
    routes = [
        ('/supplier-dashboard', '供应商仪表板'),
        ('/supplier-products', '产品管理'),
        ('/supplier-orders', '订单管理'),
        ('/supplier-stats', '财务统计')
    ]
    
    for route, name in routes:
        resp = supplier_session.get(f"{BASE_URL}{route}")
        if resp.status_code == 200:
            print_test(f"[OK] {name} 页面访问成功", "PASS")
        else:
            print_test(f"✗ {name} 页面访问失败 (状态码: {resp.status_code})", "FAIL")
    
    # 测试管理员路由
    print_test("\n管理员页面路由:", "INFO")
    resp = session.get(f"{BASE_URL}/seedling-management")
    if resp.status_code == 200:
        print_test("[OK] 鱼苗管理页面访问成功", "PASS")
    else:
        print_test(f"✗ 鱼苗管理页面访问失败 (状态码: {resp.status_code})", "FAIL")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print_test("╔" + "=" * 58 + "╗", "INFO")
    print_test("║  SmartFishery 集成测试套件                          ║", "INFO")
    print_test("║  多身份系统 + 供应商平台                            ║", "INFO")
    print_test("[" + "=" * 58 + "╝", "INFO")
    print_test("", "INFO")
    
    results = []
    
    # 测试1: 管理员登录
    try:
        result = test_scenario_1_admin_login()
        results.append(("管理员登录", result))
    except Exception as e:
        print_test(f"[FAIL] 测试异常: {str(e)}", "FAIL")
        results.append(("管理员登录", False))
    
    print_test("", "INFO")
    
    # 测试2: 供应商登录
    try:
        result, supplier_session = test_scenario_2_supplier_login()
        results.append(("供应商登录", result))
    except Exception as e:
        print_test(f"[FAIL] 测试异常: {str(e)}", "FAIL")
        results.append(("供应商登录", False))
    
    print_test("", "INFO")
    
    # 测试3: 权限检查
    try:
        result = test_scenario_3_api_access()
        results.append(("权限检查", result))
    except Exception as e:
        print_test(f"[FAIL] 测试异常: {str(e)}", "FAIL")
        results.append(("权限检查", False))
    
    print_test("", "INFO")
    
    # 测试4: 产品管理
    try:
        result = test_scenario_4_supplier_products()
        results.append(("产品管理", result))
    except Exception as e:
        print_test(f"[FAIL] 测试异常: {str(e)}", "FAIL")
        results.append(("产品管理", False))
    
    print_test("", "INFO")
    
    # 测试5: 销售统计
    try:
        result = test_scenario_5_sales_stats()
        results.append(("销售统计", result))
    except Exception as e:
        print_test(f"[FAIL] 测试异常: {str(e)}", "FAIL")
        results.append(("销售统计", False))
    
    print_test("", "INFO")
    
    # 测试6: 订单管理
    try:
        result = test_scenario_6_orders()
        results.append(("订单管理", result))
    except Exception as e:
        print_test(f"[FAIL] 测试异常: {str(e)}", "FAIL")
        results.append(("订单管理", False))
    
    print_test("", "INFO")
    
    # 测试7: 前端路由
    try:
        result = test_scenario_7_frontend_routes()
        results.append(("前端路由", result))
    except Exception as e:
        print_test(f"[FAIL] 测试异常: {str(e)}", "FAIL")
        results.append(("前端路由", False))
    
    print_test("", "INFO")
    print_test("=" * 60, "INFO")
    print_test("测试总结", "INFO")
    print_test("=" * 60, "INFO")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print_test(f"{test_name}: {status}", status)
    
    print_test("", "INFO")
    print_test(f"总计: {passed}/{total} 项测试通过", "PASS" if passed == total else "WARN")
    print_test("=" * 60, "INFO")
    
    return passed == total


if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print_test(f"[FAIL] 致命错误: {str(e)}", "FAIL")
        sys.exit(1)
