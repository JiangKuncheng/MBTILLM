#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用模拟认证信息测试搜狐接口
"""

import asyncio
import json
from sohu_client import SohuAPIClient

async def test_with_mock_auth():
    """使用模拟认证信息测试"""
    print("🔐 使用模拟认证信息测试")
    print("=" * 50)
    
    async with SohuAPIClient() as client:
        try:
            # 获取加密密钥
            if not await client._ensure_encryption_ready():
                print("❌ 无法获取加密密钥")
                return
            
            # 设置模拟的认证信息
            client.access_token = "mock_access_token_12345"
            client.user_id = 12345
            
            print(f"✅ 设置模拟认证信息")
            print(f"   access_token: {client.access_token}")
            print(f"   user_id: {client.user_id}")
            
            # 测试URL
            test_url = "http://192.168.150.252:8080/api/content/article/list?pageNum=1&pageSize=5&aiRec=false"
            
            # 获取加密数据
            encrypt_data = client._get_encrypt_data(test_url)
            print(f"\n📝 加密数据:")
            print(f"   {json.dumps(encrypt_data, indent=2, ensure_ascii=False)}")
            
            # 转换为JSON字符串
            json_string = json.dumps(encrypt_data)
            print(f"\n📄 JSON字符串:")
            print(f"   {json_string}")
            
            # AES加密
            encrypted_data = client._get_encrypt(json_string)
            print(f"\n🔒 AES加密结果:")
            print(f"   {encrypted_data}")
            
            # 现在测试实际的接口调用
            print(f"\n🚀 测试实际接口调用...")
            result = await client.get_article_list(page_num=1, page_size=5)
            print(f"📊 接口调用结果:")
            print(f"   {json.dumps(result, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n✅ 模拟认证测试完成")

if __name__ == "__main__":
    asyncio.run(test_with_mock_auth()) 