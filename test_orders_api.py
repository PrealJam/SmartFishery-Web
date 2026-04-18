#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试订单管理 API"""

import requests
import json

session = requests.Session()

# 登录
print('[STEP 1] 登录供应商账户')
login_resp = session.post('http://127.0.0.1:5000/login', data={
    'username': 'supplier1',
    'password': 'supplier123',
    'identity': 'supplier'
}, allow_redirects=False)
print(f'登录状态: {login_resp.status_code}')

# 测试 /api/my-orders API
print('\n[STEP 2] 调用 /api/my-orders API')
orders_resp = session.get('http://127.0.0.1:5000/api/my-orders?page=1&per_page=20')
print(f'API 状态码: {orders_resp.status_code}')

if orders_resp.status_code == 200:
    data = orders_resp.json()
    status = data.get('status')
    orders = data.get('data', [])
    print(f'响应状态: {status}')
    print(f'订单数: {len(orders)}')
    if orders:
        print(f'第一个订单: {json.dumps(orders[0], indent=2, ensure_ascii=False)[:500]}')
else:
    print(f'错误: {orders_resp.text[:300]}')

# 测试访问订单页面
print('\n[STEP 3] 访问订单管理页面')
page_resp = session.get('http://127.0.0.1:5000/supplier-orders')
print(f'页面状态码: {page_resp.status_code}')

if page_resp.status_code == 200:
    # 检查页面中是否包含 API 调用
    if '/api/my-orders' in page_resp.text:
        print('[OK] 页面中包含正确的 API 调用')
    else:
        print('[WARN] 页面中未找到 API 调用')
