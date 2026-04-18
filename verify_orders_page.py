#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证订单页面 API 调用是否正常"""

import requests
import json

session = requests.Session()

print("=" * 60)
print("订单管理页面 API 调用验证")
print("=" * 60)

# 登录
print("\n[1] 登录供应商账户")
login_resp = session.post('http://127.0.0.1:5000/login', data={
    'username': 'supplier1',
    'password': 'supplier123',
    'identity': 'supplier'
}, allow_redirects=False)
print(f"    状态码: {login_resp.status_code}")

# 直接调用 API
print("\n[2] 直接调用 /api/my-orders API")
api_resp = session.get('http://127.0.0.1:5000/api/my-orders?page=1&per_page=20')
print(f"    状态码: {api_resp.status_code}")

if api_resp.status_code == 200:
    data = api_resp.json()
    print(f"    响应状态: {data.get('status')}")
    print(f"    订单数: {len(data.get('data', []))}")
    print("[OK] API 返回数据成功")
else:
    print(f"[ERR] API 返回错误: {api_resp.text[:200]}")

# 访问页面
print("\n[3] 访问订单管理页面")
page_resp = session.get('http://127.0.0.1:5000/supplier-orders')
print(f"    状态码: {page_resp.status_code}")

if page_resp.status_code == 200:
    # 检查页面中的 API URL
    if '/my-orders' in page_resp.text and 'apiCall' in page_resp.text:
        print("[OK] 页面包含 API 调用代码")
        
        # 检查是否仍然有双重 /api 前缀
        if '/api/my-orders' in page_resp.text:
            # 但这里可能是在其他地方（不是 apiCall 调用）
            import re
            apiCall_calls = re.findall(r'apiCall\(["\']([^"\']+)["\']', page_resp.text)
            print(f"    apiCall 调用的 URL:")
            for url in apiCall_calls:
                if 'my-orders' in url:
                    print(f"      - {url}")
                    if url.startswith('/api/'):
                        print(f"        [WARN] 仍然有双重前缀!")
                    else:
                        print(f"        [OK] URL 格式正确")
        else:
            print("[OK] 页面中没有双重 /api 前缀")
    else:
        print("[ERR] 页面中缺少 API 调用代码")
else:
    print(f"[ERR] 页面加载失败: {page_resp.status_code}")

print("\n" + "=" * 60)
print("验证完成")
print("=" * 60)
