#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试前端 API 调用和数据返回"""

import requests
import json

session = requests.Session()

print("[INFO] 测试前端 API 数据加载...\n")

# 1. 以供应商身份登录
print("[TEST] 1. 供应商登录")
login_resp = session.post('http://127.0.0.1:5000/login', data={
    'username': 'supplier1',
    'password': 'supplier123',
    'identity': 'supplier'
}, allow_redirects=False)
print(f"[OK] 登录成功，状态码: {login_resp.status_code}\n")

# 2. 获取产品页面（检查页面是否可以加载）
print("[TEST] 2. 访问产品管理页面")
page_resp = session.get('http://127.0.0.1:5000/supplier-products')
print(f"[OK] 页面加载成功，状态码: {page_resp.status_code}")
print(f"[OK] 页面大小: {len(page_resp.text)} 字节\n")

# 3. 测试 API 返回的数据格式
endpoints = [
    ('/api/my-products?page=1&per_page=20', '产品列表'),
    ('/api/my-sales-stats', '销售统计'),
    ('/api/my-orders?page=1&per_page=5', '订单列表'),
]

print("[TEST] 3. 验证 API 返回数据格式")
for endpoint, name in endpoints:
    resp = session.get(f'http://127.0.0.1:5000{endpoint}')
    
    print(f"\n  [{name}]")
    print(f"  - 状态码: {resp.status_code}")
    
    # 检查内容类型
    content_type = resp.headers.get('content-type', '')
    print(f"  - Content-Type: {content_type}")
    
    # 尝试解析 JSON
    try:
        data = resp.json()
        print(f"  - 响应状态: {data.get('status')}")
        
        if data.get('status') == 'success':
            if isinstance(data.get('data'), list):
                print(f"  - 数据项数: {len(data.get('data'))}")
            elif isinstance(data.get('data'), dict):
                print(f"  - 数据类型: dict")
                print(f"  - 数据键: {list(data.get('data', {}).keys())}")
        
        print(f"  [OK] JSON 解析成功")
    except json.JSONDecodeError as e:
        print(f"  [ERR] JSON 解析失败: {e}")
        print(f"  [ERR] 响应内容: {resp.text[:200]}")

print("\n[OK] 前端 API 测试完成")
