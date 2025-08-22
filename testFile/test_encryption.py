#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试加密逻辑是否正确
"""

import asyncio
import json
from sohu_client import SohuAPIClient

async def test_encryption():
    """测试加密逻辑"""
    print("🔐 测试加密逻辑")
    print("=" * 50)
    
    async with SohuAPIClient() as client:
        try:
            # 获取加密密钥
            if not await client._ensure_encryption_ready():
                print("❌ 无法获取加密密钥")
                return
            
            print(f"✅ 加密密钥获取成功")
            print(f"   hmac_key: {client.hmac_key[:20]}...")
            print(f"   aes_key: {client.aes_key}")
            print(f"   iv: {client.iv}")
            print(f"   access_token: {client.access_token}")
            print(f"   user_id: {client.user_id}")
            
            # 测试URL - 只使用相对路径
            test_url = "/api/content/article/list?pageNum=1&pageSize=5&aiRec=false"
            
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
            
            # 解密验证
            decrypted_data = client._get_decrypt(encrypted_data)
            print(f"\n🔓 解密验证:")
            print(f"   {decrypted_data}")
            
            # 验证解密结果是否与原始JSON一致
            if decrypted_data == json_string:
                print("✅ 加密解密验证成功")
            else:
                print("❌ 加密解密验证失败")
                print(f"   原始: {json_string}")
                print(f"   解密: {decrypted_data}")
            
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n✅ 加密测试完成")

if __name__ == "__main__":
    asyncio.run(test_encryption()) 