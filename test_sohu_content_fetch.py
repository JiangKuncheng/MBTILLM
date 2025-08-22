 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜狐内容获取功能
验证推荐接口是否能正确获取搜狐的完整内容
"""

import asyncio
import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"

async def test_sohu_content_fetch():
    """测试搜狐内容获取功能"""
    print("🧪 测试搜狐内容获取功能")
    print("=" * 80)
    
    try:
        # 步骤1: 测试用户推荐接口（包含内容详情）
        print("📋 步骤1: 测试用户推荐接口（包含内容详情）")
        print("-" * 50)
        
        response = requests.get(
            f"{BASE_URL}/api/v1/recommendations/1",
            params={
                "page": 1,
                "limit": 5,
                "include_content_details": True,
                "auto_page": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ 推荐接口调用成功")
            
            recommendations = result['data'].get('recommendations', [])
            print(f"   - 推荐数量: {len(recommendations)}")
            
            if recommendations:
                print("   - 推荐内容详情:")
                for i, rec in enumerate(recommendations[:3]):  # 只显示前3个
                    print(f"     {i+1}. 内容ID: {rec.get('content_id')}")
                    print(f"        标题: {rec.get('title', 'N/A')}")
                    print(f"        相似度: {rec.get('similarity_score', 'N/A')}")
                    
                    # 检查搜狐内容详情
                    content = rec.get('content')
                    if content:
                        print(f"        搜狐内容: ✅ 已获取")
                        print(f"           - 搜狐ID: {content.get('id')}")
                        print(f"           - 搜狐标题: {content.get('title', 'N/A')}")
                        print(f"           - 搜狐内容: {content.get('content', 'N/A')[:50]}...")
                        print(f"           - 搜狐作者: {content.get('author', 'N/A')}")
                        print(f"           - 搜狐发布时间: {content.get('publish_time', 'N/A')}")
                    else:
                        print(f"        搜狐内容: ❌ 未获取")
            else:
                print("   ⚠️  没有推荐内容")
        else:
            print(f"   ❌ 推荐接口调用失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return
        
        # 步骤2: 测试相似内容推荐接口
        print("\n📋 步骤2: 测试相似内容推荐接口")
        print("-" * 50)
        
        # 先获取一个内容ID用于测试
        if recommendations:
            test_content_id = recommendations[0].get('content_id')
            
            response = requests.get(
                f"{BASE_URL}/api/v1/recommendations/similar/{test_content_id}",
                params={
                    "page": 1,
                    "limit": 3,
                    "include_content_details": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ 相似推荐接口调用成功")
                
                similar_contents = result['data'].get('similar_contents', [])
                print(f"   - 相似内容数量: {len(similar_contents)}")
                
                if similar_contents:
                    print("   - 相似内容详情:")
                    for i, rec in enumerate(similar_contents[:2]):  # 只显示前2个
                        print(f"     {i+1}. 内容ID: {rec.get('content_id')}")
                        print(f"        相似度: {rec.get('similarity_score', 'N/A')}")
                        
                        # 检查搜狐内容详情
                        content = rec.get('content')
                        if content:
                            print(f"        搜狐内容: ✅ 已获取")
                            print(f"           - 搜狐ID: {content.get('id')}")
                            print(f"           - 搜狐标题: {content.get('title', 'N/A')}")
                        else:
                            print(f"        搜狐内容: ❌ 未获取")
                else:
                    print("   ⚠️  没有相似内容")
            else:
                print(f"   ❌ 相似推荐接口调用失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
        else:
            print("   ⚠️  没有推荐内容，无法测试相似推荐")
        
        # 步骤3: 检查搜狐API连接
        print("\n📋 步骤3: 检查搜狐API连接")
        print("-" * 50)
        
        try:
            # 测试搜狐API连接
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("   ✅ 本地API服务正常")
            else:
                print(f"   ❌ 本地API服务异常: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 本地API服务连接失败: {e}")
        
        print("\n🎉 搜狐内容获取测试完成！")
        
        # 总结
        print("\n📋 测试总结:")
        if recommendations and any(rec.get('content') for rec in recommendations):
            print("   ✅ 搜狐内容获取正常，推荐接口返回完整内容")
        else:
            print("   ❌ 搜狐内容获取失败，推荐接口只返回基础信息")
            print("   💡 可能的原因:")
            print("      1. 搜狐API连接失败")
            print("      2. 内容ID不匹配")
            print("      3. 搜狐API返回格式异常")
            print("      4. 网络或认证问题")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 搜狐内容获取功能测试")
    print("=" * 80)
    
    asyncio.run(test_sohu_content_fetch())

if __name__ == "__main__":
    main()