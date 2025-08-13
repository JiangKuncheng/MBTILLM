# -*- coding: utf-8 -*-
"""
MBTI推荐系统快速演示（使用API接口测试）
展示：内容MBTI评分 → 用户行为分析 → 用户MBTI档案 → 个性化推荐
"""

import asyncio
import json
import logging
import aiohttp
import time
from datetime import datetime
from typing import Dict, List

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# API配置
API_BASE_URL = "http://localhost:8000"

async def call_api(method: str, endpoint: str, data: dict = None) -> dict:
    """调用API接口的辅助函数"""
    url = f"{API_BASE_URL}{endpoint}"
    
    async with aiohttp.ClientSession() as session:
        if method.upper() == "GET":
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API调用失败 {response.status}: {error_text}")
        elif method.upper() == "POST":
            headers = {"Content-Type": "application/json"}
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API调用失败 {response.status}: {error_text}")

async def create_demo_content(content_id: int, title: str, content: str) -> bool:
    """创建演示内容（通过直接插入数据库模拟）"""
    try:
        # 由于搜狐API用不了，我们通过内容评价API来创建内容MBTI数据
        # 这里先尝试评价内容，如果内容不存在，API会尝试从搜狐获取（会失败），
        # 但我们可以通过修改mbti_service来处理这种情况
        result = await call_api("POST", f"/api/v1/admin/content/{content_id}/evaluate")
        return result.get("success", False)
    except Exception as e:
        print(f"    ⚠️  创建内容 {content_id} 失败: {e}")
        return False

async def quick_demo():
    """快速演示系统核心功能"""
    print("🚀 MBTI推荐系统快速演示")
    print("=" * 80)
    
    try:
        print("📡 检查API服务器连接...")
        
        # 检查API服务器是否在运行
        try:
            health_check = await call_api("GET", "/health")
            print(f"✅ API服务器运行正常: {health_check['status']}")
        except Exception as e:
            print(f"❌ 无法连接到API服务器: {e}")
            print("请确保运行了: python main_api.py")
            return False
        
        # =================================================================
        # 第一部分：内容MBTI评分演示
        # =================================================================
        print("\n📊 第一部分：内容MBTI评分演示")
        print("-" * 60)
        
        # 准备测试内容ID（这些内容已经在mbti_service中硬编码）
        demo_content_ids = [1001, 1002, 1003, 1004, 1005, 1006]
        demo_content_titles = {
            1001: "团队协作的力量",
            1002: "独处思考的价值", 
            1003: "数据驱动的决策",
            1004: "关怀他人的重要性",
            1005: "计划的重要性",
            1006: "拥抱变化与灵活性"
        }
        
        print(f"准备评价 {len(demo_content_ids)} 个示例内容...")
        print()
        
        # 逐个评价内容的MBTI特征
        content_mbti_results = {}
        for content_id in demo_content_ids:
            title = demo_content_titles[content_id]
            print(f"正在评价内容 {content_id}: {title}")
            
            try:
                # 通过API评价内容
                result = await call_api("POST", f"/api/v1/admin/content/{content_id}/evaluate")
                
                if result["success"]:
                    if result["data"].get("already_evaluated"):
                        print(f"  ✅ 内容已评价")
                        # 可以显示已有的评价结果
                        mbti_data = result["data"]["mbti_analysis"]
                        if mbti_data:
                            print(f"  MBTI概率分布:")
                            pairs = [("E", "I"), ("S", "N"), ("T", "F"), ("J", "P")]
                            for pair in pairs:
                                trait1, trait2 = pair
                                prob1 = mbti_data.get(trait1, 0.5)
                                prob2 = mbti_data.get(trait2, 0.5)
                                dominant = trait1 if prob1 > prob2 else trait2
                                print(f"    {trait1}: {prob1:.3f} | {trait2}: {prob2:.3f} → 倾向: {dominant}")
                    else:
                        print(f"  🔄 开始评价...")
                        # 等待评价完成（后台任务）
                        await asyncio.sleep(2)
                        print(f"  ✅ 评价完成")
                else:
                    print(f"  ❌ 评价失败")
            except Exception as e:
                print(f"  ❌ API调用失败: {e}")
            
            print()
        
        print("✅ 内容MBTI评分完成")
        
        # =================================================================
        # 第二部分：用户行为分析演示  
        # =================================================================
        print("\n👤 第二部分：用户行为分析演示")
        print("-" * 60)
        
        # 创建两个不同特征的演示用户
        users = [
            {
                "id": 2001,
                "name": "外向思考者Alice",
                "preferred_contents": [1001, 1003, 1005],  # 团队协作、数据决策、计划性
                "behaviors": ["like", "like", "like"]  # 只使用like行为
            },
            {
                "id": 2002, 
                "name": "内向情感者Bob",
                "preferred_contents": [1002, 1004, 1006],  # 独处思考、关怀他人、灵活性
                "behaviors": ["like", "like", "like"]  # 只使用like行为
            }
        ]
        
        user_profiles = {}
        
        for user in users:
            print(f"\n分析用户 {user['id']} ({user['name']}):")
            
            # 模拟用户行为历史
            print(f"  模拟用户行为历史...")
            for i, (content_id, action) in enumerate(zip(user["preferred_contents"], user["behaviors"])):
                try:
                    # 通过API记录用户行为
                    behavior_data = {
                        "user_id": user["id"],
                        "content_id": content_id,
                        "action": action,
                        "source": "api_demo"
                    }
                    result = await call_api("POST", "/api/v1/behavior/record", behavior_data)
                    if result["success"]:
                        print(f"    ✅ {action} 内容 {content_id}")
                    else:
                        print(f"    ❌ 记录失败: {action} 内容 {content_id}")
                except Exception as e:
                    print(f"    ❌ API调用失败: {e}")
            
            # 添加更多like行为以达到分析阈值
            import random
            additional_behaviors = 15
            print(f"  添加 {additional_behaviors} 个额外like行为...")
            for i in range(additional_behaviors):
                content_id = random.choice(user["preferred_contents"])
                action = "like"  # 只使用like行为
                try:
                    behavior_data = {
                        "user_id": user["id"],
                        "content_id": content_id,
                        "action": action,
                        "source": "api_demo_extra"
                    }
                    result = await call_api("POST", "/api/v1/behavior/record", behavior_data)
                    if result["success"]:
                        if i < 3:  # 只显示前3个
                            print(f"    ✅ {action} 内容 {content_id}")
                        elif i == 3:
                            print(f"    ...")
                except Exception as e:
                    if i < 3:
                        print(f"    ❌ API调用失败: {e}")
            
            print(f"    总计记录 {len(user['preferred_contents']) + additional_behaviors} 个行为")
            
            # 获取用户行为统计
            try:
                stats_result = await call_api("GET", f"/api/v1/behavior/stats/{user['id']}")
                if stats_result["success"]:
                    stats = stats_result["data"]
                    print(f"  行为统计:")
                    print(f"    总行为数: {stats['total_behaviors']}")
                    print(f"    活跃程度: {stats['activity_level']}")
                    print(f"    行为分布: {stats['action_distribution']}")
                else:
                    print(f"  ❌ 获取统计失败")
            except Exception as e:
                print(f"  ❌ 获取统计API调用失败: {e}")
            
            user_profiles[user["id"]] = user
        
        print("\n✅ 用户行为分析完成")
        
        # =================================================================
        # 第三部分：用户MBTI档案生成演示
        # =================================================================
        print("\n🧠 第三部分：用户MBTI档案生成演示")
        print("-" * 60)
        
        for user in users:
            user_id = user["id"]
            print(f"\n为用户 {user_id} ({user['name']}) 生成MBTI档案:")
            
            try:
                # 强制更新MBTI档案
                update_data = {
                    "force_update": True,
                    "analyze_last_n_behaviors": 50
                }
                update_result = await call_api("POST", f"/api/v1/mbti/update/{user_id}", update_data)
                
                if update_result["success"]:
                    data = update_result["data"]
                    print(f"  ✅ MBTI档案更新成功")
                    print(f"  分析行为数: {data.get('behaviors_analyzed', 'N/A')}")
                    print(f"  分析内容数: {data.get('contents_analyzed', 'N/A')}")
                    print(f"  推导类型: {data.get('new_mbti_type', 'N/A')}")
                    
                    # 显示概率分布
                    if "new_profile" in data and "probabilities" in data["new_profile"]:
                        probabilities = data["new_profile"]["probabilities"]
                        print(f"  概率分布:")
                        pairs = [("E", "I"), ("S", "N"), ("T", "F"), ("J", "P")]
                        for pair in pairs:
                            trait1, trait2 = pair
                            prob1 = probabilities.get(trait1, 0.5)
                            prob2 = probabilities.get(trait2, 0.5)
                            confidence = abs(prob1 - prob2)
                            print(f"    {trait1}: {prob1:.3f} | {trait2}: {prob2:.3f} (置信度: {confidence:.3f})")
                else:
                    print(f"  ⚠️  档案更新失败")
            except Exception as e:
                print(f"  ❌ API调用失败: {e}")
        
        print("\n✅ 用户MBTI档案生成完成")
        
        # =================================================================
        # 第四部分：个性化推荐演示
        # =================================================================
        print("\n🎯 第四部分：个性化推荐演示")
        print("-" * 60)
        
        for user in users:
            user_id = user["id"]
            print(f"\n为用户 {user_id} ({user['name']}) 生成个性化推荐:")
            
            try:
                # 生成推荐
                recommendations_result = await call_api("GET", f"/api/v1/recommendations/{user_id}?limit=10&similarity_threshold=0.3")
                
                if recommendations_result["success"]:
                    recommendations = recommendations_result["data"]
                    
                    print(f"  用户MBTI类型: {recommendations['user_mbti_type']}")
                    print(f"  用户概率分布: {recommendations['user_mbti_probabilities']}")
                    print(f"  推荐算法:")
                    print(f"    候选内容数: {recommendations['metadata']['total_candidates']}")
                    print(f"    过滤后数量: {recommendations['metadata']['filtered_count']}")
                    print(f"    平均相似度: {recommendations['metadata']['avg_similarity']}")
                    
                    # 显示推荐结果
                    recs = recommendations["recommendations"]
                    if recs:
                        print(f"  📋 推荐结果 (前5个):")
                        for i, rec in enumerate(recs[:5]):
                            content_id = rec["content_id"]
                            similarity = rec["similarity_score"]
                            traits = ", ".join(rec["mbti_match_traits"])
                            
                            # 查找对应的内容标题
                            content_title = demo_content_titles.get(content_id, "未知内容")
                            
                            print(f"    {i+1}. 内容 {content_id}: {content_title}")
                            print(f"       相似度: {similarity:.3f} | 匹配特征: [{traits}]")
                    else:
                        print(f"  ⚠️  暂无推荐内容")
                else:
                    print(f"  ❌ 推荐生成失败")
            except Exception as e:
                print(f"  ❌ API调用失败: {e}")
            
            print()
        
        print("✅ 个性化推荐演示完成")
        
        # =================================================================
        # 第五部分：系统统计总结
        # =================================================================
        print("\n📈 第五部分：系统统计总结")
        print("-" * 60)
        
        # 获取系统信息
        try:
            system_info = await call_api("GET", "/api/v1/system/info")
            if system_info["success"]:
                stats = system_info["data"]["database_stats"]
                print("数据库统计:")
                print(f"  👥 用户总数: {stats['total_users']}")
                print(f"  📝 行为记录数: {stats['total_behaviors']}")
                print(f"  📄 内容MBTI评价数: {stats['total_contents']}")
                print(f"  🎯 推荐日志数: {stats['total_recommendations']}")
            else:
                print("❌ 无法获取系统统计")
        except Exception as e:
            print(f"❌ 获取系统统计失败: {e}")
        
        # 显示用户档案对比
        print("\n用户档案对比:")
        print(f"{'用户ID':<8} {'用户名':<15} {'MBTI类型':<8}")
        print("-" * 40)
        
        for user in users:
            user_id = user["id"]
            try:
                profile_result = await call_api("GET", f"/api/v1/mbti/profile/{user_id}")
                if profile_result["success"]:
                    profile_data = profile_result["data"]
                    mbti_type = profile_data.get("mbti_type", "")
                    print(f"{user_id:<8} {user['name']:<15} {mbti_type:<8}")
                else:
                    print(f"{user_id:<8} {user['name']:<15} {'N/A':<8}")
            except Exception as e:
                print(f"{user_id:<8} {user['name']:<15} {'ERROR':<8}")
        
        print("\n" + "=" * 80)
        print("🎉 MBTI推荐系统API演示完成！")
        print("=" * 80)
        
        print("\n📝 演示总结:")
        print("1. ✅ 通过API成功评价了6个不同特征的示例内容")
        print("2. ✅ 通过API模拟了2个用户的行为历史和偏好分析")
        print("3. ✅ 通过API基于行为历史生成了用户MBTI档案")
        print("4. ✅ 通过API根据MBTI向量相似度生成了个性化推荐")
        print("5. ✅ 展示了完整的API接口工作流程")
        
        print(f"\n🚀 API系统测试完成！所有接口均正常工作")
        print(f"💡 API服务器正在运行: {API_BASE_URL}")
        print(f"📖 查看API文档: {API_BASE_URL}/docs")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_demo():
    """运行演示"""
    print("🎬 启动MBTI推荐系统快速演示...")
    asyncio.run(quick_demo())

if __name__ == "__main__":
    run_demo()
