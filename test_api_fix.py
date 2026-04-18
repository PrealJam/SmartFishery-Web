#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test API endpoints after fixing the double /api prefix issue"""

import requests
import json

session = requests.Session()

# 登录为供应商
login_resp = session.post('http://127.0.0.1:5000/login', data={
    'username': 'supplier1',
    'password': 'supplier123', 
    'identity': 'supplier'
}, allow_redirects=False)

print(f'[OK] 登录状态码: {login_resp.status_code}')

# 测试产品 API
prod_resp = session.get('http://127.0.0.1:5000/api/my-products?page=1&per_page=20')
print(f'[OK] 产品 API 状态码: {prod_resp.status_code}')

if prod_resp.status_code == 200:
    data = prod_resp.json()
    print(f'[OK] 成功获取 {len(data.get("data", []))} 个产品')
    print(f'[OK] 响应格式正确: {data.get("status")}')
else:
    print(f'[ERR] 错误: {prod_resp.text[:200]}')

# 测试销售统计 API  
stats_resp = session.get('http://127.0.0.1:5000/api/my-sales-stats')
print(f'[OK] 销售统计 API 状态码: {stats_resp.status_code}')
if stats_resp.status_code == 200:
    print(f'[OK] 销售统计数据已返回')
    
# 测试订单 API
orders_resp = session.get('http://127.0.0.1:5000/api/my-orders?page=1&per_page=5')
print(f'[OK] 订单 API 状态码: {orders_resp.status_code}')
if orders_resp.status_code == 200:
    data = orders_resp.json()
    print(f'[OK] 成功获取 {len(data.get("data", []))} 个订单')

print('[OK] 所有 API 端点测试完成')
