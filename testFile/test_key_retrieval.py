#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试加密密钥获取
"""

import asyncio
import json
import aiohttp

async def test_key_retrieval():
    """测试加密密钥获取"""
    print("🔑 测试加密密钥获取")
    print("=" * 50)
    
    base_url = "http://192.168.150.252:8080"
    endpoint = "/app/v1/query/aesKey"
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"{base_url}{endpoint}"
            print(f"🔗 请求URL: {url}")
            
            async with session.get(url) as response:
                print(f"📡 HTTP状态: {response.status}")
                print(f"📋 Content-Type: {response.headers.get('content-type', 'unknown')}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 成功获取响应:")
                    print(f"   {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    if result.get("code") == 200:
                        data = result.get("data", {})
                        hmac_key = data.get("hmacKey")
                        aes_key = data.get("aesKey")
                        iv = data.get("iv")
                        
                        print(f"\n🔍 密钥信息:")
                        print(f"   hmacKey: {hmac_key}")
                        print(f"   aesKey: {aes_key}")
                        print(f"   iv: {iv}")
                        
                        print(f"\n📏 密钥长度:")
                        print(f"   hmacKey长度: {len(hmac_key)} 字符")
                        print(f"   aesKey长度: {len(aes_key)} 字符")
                        print(f"   iv长度: {len(iv)} 字符")
                        
                        print(f"\n🔐 字节长度:")
                        print(f"   hmacKey字节: {len(hmac_key.encode('utf-8'))} 字节")
                        print(f"   aesKey字节: {len(aes_key.encode('utf-8'))} 字节")
                        print(f"   iv字节: {len(iv.encode('utf-8'))} 字节")
                        
                        # 验证AES密钥长度
                        if len(aes_key.encode('utf-8')) == 16:
                            print(f"   ✅ AES密钥长度正确 (16字节 = AES-128)")
                        elif len(aes_key.encode('utf-8')) == 24:
                            print(f"   ✅ AES密钥长度正确 (24字节 = AES-192)")
                        elif len(aes_key.encode('utf-8')) == 32:
                            print(f"   ✅ AES密钥长度正确 (32字节 = AES-256)")
                        else:
                            print(f"   ⚠️  AES密钥长度异常: {len(aes_key.encode('utf-8'))} 字节")
                        
                    else:
                        print(f"❌ 响应码错误: {result.get('code')}")
                        print(f"   错误信息: {result.get('msg')}")
                else:
                    print(f"❌ HTTP请求失败: {response.status}")
                    
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    print("\n✅ 密钥获取测试完成")

if __name__ == "__main__":
    asyncio.run(test_key_retrieval()) 