#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同的搜狐接口路径
"""

import asyncio
import aiohttp
import json

async def test_different_paths():
    """测试不同的接口路径"""
    print("🧪 测试不同的搜狐接口路径")
    print("=" * 50)
    
    base_url = "http://192.168.150.252:8080"
    
    # 可能的接口路径
    possible_paths = [
        "/app/api/content/article/list",
        "/api/content/article/list", 
        "/content/article/list",
        "/article/list",
        "/content/list",
        "/app/content/article/list",
        "/v1/content/article/list",
        "/v1/api/content/article/list"
    ]
    
    async with aiohttp.ClientSession() as session:
        for path in possible_paths:
            print(f"\n🔗 测试路径: {path}")
            
            try:
                params = {
                    "pageNum": 1,
                    "pageSize": 5,
                    "aiRec": "false"
                }
                
                url = f"{base_url}{path}"
                async with session.get(url, params=params, timeout=10) as response:
                    print(f"   HTTP状态: {response.status}")
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                            print(f"   ✅ 成功! 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                            break  # 找到正确的路径
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
    
    print("\n✅ 路径测试完成")

if __name__ == "__main__":
    asyncio.run(test_different_paths()) 