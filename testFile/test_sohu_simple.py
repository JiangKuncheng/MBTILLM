#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试搜狐接口是否可达
"""

import asyncio
import aiohttp
import json

async def test_sohu_api():
    """测试搜狐API是否可达"""
    print("🧪 测试搜狐API连接")
    print("=" * 50)
    
    # 测试不同的接口地址
    test_urls = [
        "https://api.sohuglobal.com",
        "http://192.168.150.252:888",
        "http://192.168.150.252:8080",
        "https://api.sohu.com"
    ]
    
    for base_url in test_urls:
        print(f"\n🔗 测试地址: {base_url}")
        
        try:
            # 测试基本连接
            async with aiohttp.ClientSession() as session:
                # 测试根路径
                try:
                    async with session.get(f"{base_url}/", timeout=10) as response:
                        print(f"   根路径: HTTP {response.status}")
                except Exception as e:
                    print(f"   根路径: 连接失败 - {e}")
                
                # 测试加密密钥接口
                try:
                    async with session.get(f"{base_url}/app/v1/query/aesKey", timeout=10) as response:
                        print(f"   加密密钥接口: HTTP {response.status}")
                        if response.status == 200:
                            result = await response.json()
                            print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                except Exception as e:
                    print(f"   加密密钥接口: 连接失败 - {e}")
                
                # 测试图文列表接口
                try:
                    params = {
                        "pageNum": 1,
                        "pageSize": 5,
                        "aiRec": "false"
                    }
                    async with session.get(f"{base_url}/app/api/content/article/list", params=params, timeout=10) as response:
                        print(f"   图文列表接口: HTTP {response.status}")
                        if response.status == 200:
                            result = await response.json()
                            print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        elif response.status == 401:
                            print("   需要认证")
                        elif response.status == 404:
                            print("   接口不存在")
                        elif response.status == 501:
                            print("   接口未实现")
                except Exception as e:
                    print(f"   图文列表接口: 连接失败 - {e}")
                
        except Exception as e:
            print(f"   整体连接失败: {e}")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_sohu_api()) 