#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看搜狐接口的实际响应内容
"""

import asyncio
import aiohttp

async def check_response_content():
    """检查接口响应的实际内容"""
    print("🔍 检查搜狐接口响应内容")
    print("=" * 50)
    
    base_url = "http://192.168.150.252:8080"
    path = "/api/content/article/list"
    
    async with aiohttp.ClientSession() as session:
        try:
            params = {
                "pageNum": 1,
                "pageSize": 5,
                "aiRec": "false"
            }
            
            url = f"{base_url}{path}"
            async with session.get(url, params=params, timeout=10) as response:
                print(f"HTTP状态: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                print(f"响应长度: {len(await response.read())}")
                
                # 重新获取响应内容
                async with session.get(url, params=params, timeout=10) as response2:
                    content = await response2.text()
                    print(f"\n📄 响应内容:")
                    print("-" * 30)
                    print(content[:500])  # 只显示前500个字符
                    if len(content) > 500:
                        print("... (内容被截断)")
                    print("-" * 30)
                    
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    
    print("\n✅ 响应检查完成")

if __name__ == "__main__":
    asyncio.run(check_response_content()) 