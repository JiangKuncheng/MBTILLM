 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MBTI评分模式切换和推荐接口分页功能
"""

import asyncio
import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"

async def test_mbti_scoring_mode_switching():
    """测试MBTI评分模式切换功能"""
    print("🧪 测试MBTI评分模式切换功能")
    print("=" * 80)
    
    try:
        # 步骤1: 检查当前评分模式
        print("📋 步骤1: 检查当前评分模式")
        print("-" * 50)
        
        response = requests.get(f"{BASE_URL}/api/v1/system/mbti-scoring-mode")
        if response.status_code == 200:
            mode_info = response.json()
            current_mode = mode_info["data"]["current_mode"]
            print(f"   ✅ 当前评分模式: {current_mode}")
            print(f"   描述: {mode_info['data']['description']}")
        else:
            print(f"   ❌ 获取评分模式失败: {response.status_code}")
            return
        
        # 步骤2: 切换到随机数模式
        print("\n📋 步骤2: 切换到随机数模式")
        print("-" * 50)
        
        response = requests.post(f"{BASE_URL}/api/v1/system/mbti-scoring-mode", params={"mode": "random"})
        if response.status_code == 200:
            print("   ✅ 已切换到随机数模式")
        else:
            print(f"   ❌ 切换模式失败: {response.status_code}")
            return
        
        # 步骤3: 测试随机数评分
        print("\n📋 步骤3: 测试随机数评分")
        print("-" * 50)
        
        test_content = {
            "content": "这是一个测试内容，用于验证随机数评分模式。内容包含团队协作、创新思维等元素。",
            "title": "测试内容 - 随机数模式"
        }
        
        print("   🔄 测试随机数评分...")
        response = requests.post(f"{BASE_URL}/api/v1/admin/content/10001/evaluate", json=test_content)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ 随机数评分成功")
            print(f"   评分模式: {result['data']['scoring_mode']}")
            
            # 检查是否有评分方法字段（新评价的内容才有）
            if 'scoring_method' in result['data']:
                print(f"   评分方法: {result['data']['scoring_method']}")
            else:
                print(f"   评分方法: 已存在（无需重新评价）")
            
            print(f"   MBTI评分: {result['data']['mbti_analysis']}")
        else:
            print(f"   ❌ 随机数评分失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
        
        print("\n🎉 MBTI评分模式测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

def test_recommendation_pagination():
    """测试推荐接口分页功能"""
    print("\n🧪 测试推荐接口分页功能")
    print("=" * 80)
    
    try:
        # 步骤1: 测试用户推荐分页
        print("📋 步骤1: 测试用户推荐分页")
        print("-" * 50)
        
        # 测试第一页
        print("   🔄 测试第一页推荐...")
        response = requests.get(
            f"{BASE_URL}/api/v1/recommendations/1",
            params={
                "page": 1,
                "limit": 10,
                "include_content_details": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ 第一页推荐成功")
            print(f"   当前页: {result['data']['pagination']['current_page']}")
            print(f"   总页数: {result['data']['pagination']['total_pages']}")
            print(f"   总数量: {result['data']['pagination']['total_count']}")
            print(f"   每页数量: {result['data']['pagination']['limit']}")
            print(f"   是否有下一页: {result['data']['pagination']['has_next']}")
            print(f"   是否有上一页: {result['data']['pagination']['has_prev']}")
            print(f"   推荐数量: {len(result['data'].get('recommendations', []))}")
            
            # 检查是否包含内容详情
            recommendations = result['data'].get('recommendations', [])
            if recommendations:
                first_rec = recommendations[0]
                if 'content' in first_rec:
                    print(f"   ✅ 包含内容详情: {first_rec['content'] is not None}")
                else:
                    print(f"   ✅ 内容详情字段: 未包含（可能API调用失败或未启用）")
            else:
                print(f"   ⚠️  没有推荐内容")
        else:
            print(f"   ❌ 第一页推荐失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
        
        # 步骤2: 测试相似内容推荐分页
        print("\n📋 步骤2: 测试相似内容推荐分页")
        print("-" * 50)
        
        print("   🔄 测试相似内容推荐...")
        response = requests.get(
            f"{BASE_URL}/api/v1/recommendations/similar/10001",
            params={
                "page": 1,
                "limit": 5,
                "include_content_details": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ 相似内容推荐成功")
            print(f"   基础内容ID: {result['data']['base_content_id']}")
            print(f"   当前页: {result['data']['pagination']['current_page']}")
            print(f"   总页数: {result['data']['pagination']['total_pages']}")
            print(f"   总数量: {result['data']['pagination']['total_count']}")
            print(f"   相似内容数量: {len(result['data'].get('similar_contents', []))}")
            
            # 检查是否包含内容详情
            similar_contents = result['data'].get('similar_contents', [])
            if similar_contents:
                first_similar = similar_contents[0]
                if 'content' in first_similar:
                    print(f"   ✅ 包含内容详情: {first_similar['content'] is not None}")
                else:
                    print(f"   ✅ 内容详情字段: 未包含（可能API调用失败或未启用）")
            else:
                print(f"   ⚠️  没有相似内容")
        else:
            print(f"   ❌ 相似内容推荐失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
        
        print("\n🎉 推荐接口分页测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """测试API端点是否可用"""
    print("🔍 检查API端点可用性...")
    
    endpoints = [
        "/health",
        "/api/v1/system/mbti-scoring-mode",
        "/api/v1/admin/content/10001/evaluate",
        "/api/v1/recommendations/1",
        "/api/v1/recommendations/similar/10001"
    ]
    
    for endpoint in endpoints:
        try:
            if "POST" in endpoint:
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.get(f"{BASE_URL}{endpoint}")
            
            if response.status_code in [200, 405]:  # 200成功，405方法不允许
                print(f"   ✅ {endpoint}: 可用")
            else:
                print(f"   ❌ {endpoint}: 状态码 {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {endpoint}: 连接失败，请确保服务器已启动")
        except Exception as e:
            print(f"   ❌ {endpoint}: 异常 {e}")

async def main():
    """主函数"""
    print("🚀 MBTI评分模式和推荐接口分页测试")
    print("=" * 80)
    
    # 先检查API端点
    test_api_endpoints()
    
    print("\n" + "=" * 80)
    
    # 运行主要测试
    await test_mbti_scoring_mode_switching()
    
    print("\n" + "=" * 80)
    
    # 测试推荐接口分页
    test_recommendation_pagination()
    
    print("\n" + "=" * 80)
    print("🎉 所有测试完成！")

if __name__ == "__main__":
    asyncio.run(main())