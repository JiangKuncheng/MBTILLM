#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试请求头是否正确设置
"""

import asyncio
import json
import aiohttp

async def test_headers():
    """测试请求头"""
    print("🧪 测试请求头设置")
    print("=" * 50)
    
    base_url = "http://192.168.150.252:8080"
    path = "/api/content/article/list"
    
    # 模拟的加密数据
    mock_encrypt_data = {
        "token": "",
        "userId": 0,
        "timestamp": int(asyncio.get_event_loop().time() * 1000),
        "url": path,
        "platform": "web",
        "nonce": "test_nonce_12345",
        "sign": "test_signature_12345"
    }
    
    # 模拟的加密值
    mock_encrypted_value = "mock_encrypted_data_12345"
    
    # 测试不同的请求头组合
    test_cases = [
        {
            "name": "只有x-encrypt-key",
            "headers": {
                "Content-Type": "application/json",
                "x-encrypt-key": mock_encrypted_value
            }
        },
        {
            "name": "x-encrypt-key + version",
            "headers": {
                "Content-Type": "application/json",
                "x-encrypt-key": mock_encrypted_value,
                "version": "1.5.0"
            }
        },
        {
            "name": "x-encrypt-key + version + platform-type",
            "headers": {
                "Content-Type": "application/json",
                "x-encrypt-key": mock_encrypted_value,
                "version": "1.5.0",
                "platform-type": "USER"
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"\n🔗 测试: {test_case['name']}")
            print(f"   请求头: {json.dumps(test_case['headers'], indent=2, ensure_ascii=False)}")
            
            try:
                params = {
                    "pageNum": 1,
                    "pageSize": 5,
                    "aiRec": "false"
                }
                
                url = f"{base_url}{path}"
                async with session.get(url, params=params, headers=test_case['headers'], timeout=10) as response:
                    print(f"   HTTP状态: {response.status}")
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                            print(f"   ✅ 成功! 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                            print(f"   🎯 找到正确的请求头组合!")
                            break
                        except:
                            print(f"   ✅ 成功! 但响应不是JSON格式")
                    elif response.status == 401:
                        print("   🔒 需要认证")
                    elif response.status == 404:
                        print("   ❌ 接口不存在")
                    elif response.status == 501:
                        print("   ⚠️  接口未实现")
                    elif response.status == 500:
                        print("   💥 服务器内部错误")
                    else:
                        print(f"   ❓ 其他状态: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ 请求失败: {e}")
    
    print("\n✅ 请求头测试完成")

if __name__ == "__main__":
    asyncio.run(test_headers()) 