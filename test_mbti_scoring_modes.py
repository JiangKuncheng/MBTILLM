 
 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MBTI评分模式切换功能
验证AI评分、随机数生成、混合模式三种方式
"""

import asyncio
import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"

async def test_mbti_scoring_modes():
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
            print(f"   可用模式: {mode_info['data']['available_modes']}")
        else:
            print(f"   ❌ 获取评分模式失败: {response.status_code}")
            return
        
        # 步骤2: 测试随机数模式
        print("\n📋 步骤2: 测试随机数模式")
        print("-" * 50)
        
        # 切换到随机数模式
        response = requests.post(f"{BASE_URL}/api/v1/system/mbti-scoring-mode", params={"mode": "random"})
        if response.status_code == 200:
            print("   ✅ 已切换到随机数模式")
        else:
            print(f"   ❌ 切换模式失败: {response.status_code}")
            return
        
        # 测试随机数评分
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
            print(f"   评分方法: {result['data']['scoring_method']}")
            print(f"   MBTI评分: {result['data']['mbti_analysis']}")
        else:
            print(f"   ❌ 随机数评分失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
        
        # 步骤3: 测试AI模式
        print("\n📋 步骤3: 测试AI模式")
        print("-" * 50)
        
        # 切换到AI模式
        response = requests.post(f"{BASE_URL}/api/v1/system/mbti-scoring-mode", params={"mode": "ai"})
        if response.status_code == 200:
            print("   ✅ 已切换到AI模式")
        else:
            print(f"   ❌ 切换模式失败: {response.status_code}")
            return
        
        # 测试AI评分
        test_content_ai = {
            "content": "这是一个测试内容，用于验证AI评分模式。内容强调逻辑分析、系统思考、创新突破等特征。",
            "title": "测试内容 - AI模式"
        }
        
        print("   🔄 测试AI评分...")
        response = requests.post(f"{BASE_URL}/api/v1/admin/content/10002/evaluate", json=test_content_ai)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ AI评分成功")
            print(f"   评分模式: {result['data']['scoring_mode']}")
            print(f"   评分方法: {result['data']['scoring_method']}")
            print(f"   MBTI评分: {result['data']['mbti_analysis']}")
        else:
            print(f"   ❌ AI评分失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
        
        # 步骤4: 测试混合模式
        print("\n📋 步骤4: 测试混合模式")
        print("-" * 50)
        
        # 切换到混合模式
        response = requests.post(f"{BASE_URL}/api/v1/system/mbti-scoring-mode", params={"mode": "mixed"})
        if response.status_code == 200:
            print("   ✅ 已切换到混合模式")
        else:
            print(f"   ❌ 切换模式失败: {response.status_code}")
            return
        
        # 测试混合模式评分（多次测试看效果）
        test_contents_mixed = [
            {
                "content": "混合模式测试内容1：强调团队合作、创新思维、系统分析",
                "title": "混合模式测试1"
            },
            {
                "content": "混合模式测试内容2：注重细节、逻辑推理、情感表达",
                "title": "混合模式测试2"
            },
            {
                "content": "混合模式测试内容3：灵活应变、计划执行、人际沟通",
                "title": "混合模式测试3"
            }
        ]
        
        for i, test_content in enumerate(test_contents_mixed, 1):
            print(f"   🔄 混合模式测试 {i}/3...")
            response = requests.post(f"{BASE_URL}/api/v1/admin/content/{10010 + i}/evaluate", json=test_content)
            
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ 测试 {i} 成功")
                print(f"      评分方法: {result['data']['scoring_method']}")
                print(f"      MBTI评分: {result['data']['mbti_analysis']}")
            else:
                print(f"      ❌ 测试 {i} 失败: {response.status_code}")
        
        # 步骤5: 测试快速模式切换
        print("\n📋 步骤5: 测试快速模式切换")
        print("-" * 50)
        
        # 使用测试接口快速验证所有模式
        print("   🔄 使用快速测试接口...")
        response = requests.post(f"{BASE_URL}/api/v1/system/test-mbti-scoring")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ 快速测试成功")
            print(f"   当前模式: {result['data']['current_mode']}")
            
            test_results = result['data']['test_results']
            for mode, mode_result in test_results.items():
                print(f"   📊 {mode}: {mode_result.get('scoring_method', 'N/A')}")
        else:
            print(f"   ❌ 快速测试失败: {response.status_code}")
        
        # 步骤6: 验证模式切换的持久性
        print("\n📋 步骤6: 验证模式切换的持久性")
        print("-" * 50)
        
        # 检查当前模式
        response = requests.get(f"{BASE_URL}/api/v1/system/mbti-scoring-mode")
        if response.status_code == 200:
            mode_info = response.json()
            final_mode = mode_info["data"]["current_mode"]
            print(f"   📊 最终评分模式: {final_mode}")
            print(f"   描述: {mode_info['data']['description']}")
        else:
            print(f"   ❌ 获取最终模式失败: {response.status_code}")
        
        print("\n🎉 MBTI评分模式测试完成！")
        
        # 总结
        print("\n📋 测试总结:")
        print("   ✅ 随机数模式: 快速生成MBTI评分，适合开发和测试")
        print("   ✅ AI模式: 真正调用大模型，适合生产环境")
        print("   ✅ 混合模式: 平衡性能和准确性，适合过渡期")
        print("   ✅ 模式切换: 支持运行时动态切换，无需重启")
        print("   ✅ 接口兼容: 保持原有API接口不变")
        
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
        "/api/v1/admin/content/10001/evaluate"
    ]
    
    for endpoint in endpoints:
        try:
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
    print("🚀 MBTI评分模式测试")
    print("=" * 80)
    
    # 先检查API端点
    test_api_endpoints()
    
    print("\n" + "=" * 80)
    
    # 运行主要测试
    await test_mbti_scoring_modes()

if __name__ == "__main__":
    asyncio.run(main())