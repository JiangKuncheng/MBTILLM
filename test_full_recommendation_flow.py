#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整推荐系统流程
模拟真实用户行为：随机推荐 -> 用户点赞 -> MBTI评分 -> 计算用户MBTI -> 再次推荐 -> 相似度排序
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from database_service import db_service
from mbti_service import mbti_service
from sohu_client import sohu_client

class RecommendationFlowTester:
    def __init__(self):
        self.test_user_id = 999  # 测试用户ID
        self.test_results = {}
        
    async def test_full_flow(self):
        """测试完整的推荐流程"""
        print("🚀 开始测试完整推荐系统流程")
        print("=" * 80)
        
        try:
            # 步骤1: 随机推荐60条内容
            print("📋 步骤1: 随机推荐60条内容")
            print("-" * 50)
            initial_recommendations = await self._get_initial_recommendations(60)
            print(f"✅ 成功获取 {len(initial_recommendations)} 条初始推荐")
            
            # 步骤2: 模拟用户对50条内容点赞
            print("\n📋 步骤2: 模拟用户点赞50条内容")
            print("-" * 50)
            liked_contents = await self._simulate_user_likes(initial_recommendations[:50])
            print(f"✅ 用户点赞了 {len(liked_contents)} 条内容")
            
            # 步骤3: 触发MBTI评分（通过记录行为触发）
            print("\n📋 步骤3: 触发MBTI评分")
            print("-" * 50)
            await self._trigger_mbti_evaluation(liked_contents)
            
            # 步骤4: 计算用户MBTI档案
            print("\n📋 步骤4: 计算用户MBTI档案")
            print("-" * 50)
            user_mbti = await self._calculate_user_mbti()
            
            # 步骤5: 再次获取推荐（基于MBTI相似度）
            print("\n📋 步骤5: 获取基于MBTI的推荐")
            print("-" * 50)
            mbti_recommendations = await self._get_mbti_based_recommendations()
            
            # 步骤6: 对推荐内容进行MBTI评分
            print("\n📋 步骤6: 对推荐内容进行MBTI评分")
            print("-" * 50)
            await self._evaluate_recommendation_contents(mbti_recommendations)
            
            # 步骤7: 基于相似度排序
            print("\n📋 步骤7: 基于相似度排序推荐内容")
            print("-" * 50)
            sorted_recommendations = await self._sort_by_similarity(user_mbti, mbti_recommendations)
            
            # 步骤8: 展示最终结果
            print("\n📋 步骤8: 最终推荐结果")
            print("-" * 50)
            await self._show_final_results(sorted_recommendations, user_mbti)
            
            print("\n🎉 完整推荐流程测试完成！")
            
        except Exception as e:
            print(f"❌ 测试过程中出现异常: {e}")
            import traceback
            traceback.print_exc()
    
    async def _get_initial_recommendations(self, limit: int) -> List[Dict]:
        """获取初始随机推荐"""
        try:
            # 从搜狐接口获取内容
            async with sohu_client as client:
                result = await client.get_article_list(
                    page_num=1,
                    page_size=limit,
                    state="OnShelf"
                )
            
            if result.get("code") == 200 and "data" in result:
                data = result["data"]
                if isinstance(data, list):
                    articles = data
                elif isinstance(data, dict):
                    articles = data.get("data", [])
                    if not articles and "list" in data:
                        articles = data.get("list", [])
                else:
                    articles = []
                
                # 转换为标准格式
                recommendations = []
                for article in articles[:limit]:
                    if article.get("id") and article.get("title"):
                        recommendations.append({
                            "id": article["id"],
                            "title": article.get("title", ""),
                            "content": article.get("content", ""),
                            "type": article.get("type", "article")
                        })
                
                return recommendations
            else:
                print(f"❌ 获取初始推荐失败: {result}")
                return []
                
        except Exception as e:
            print(f"❌ 获取初始推荐异常: {e}")
            return []
    
    async def _simulate_user_likes(self, contents: List[Dict]) -> List[Dict]:
        """模拟用户点赞行为"""
        liked_contents = []
        
        for i, content in enumerate(contents, 1):
            try:
                print(f"   👍 用户点赞第 {i}/{len(contents)} 条: {content['title'][:30]}...")
                
                # 记录用户行为
                behavior = db_service.record_user_behavior(
                    user_id=self.test_user_id,
                    content_id=content["id"],
                    action="like",
                    source="test",
                    session_id=f"test_session_{int(time.time())}",
                    extra_data={"test": True, "step": "initial_like"}
                )
                
                # 增加用户行为计数
                behavior_count = db_service.increment_behavior_count(self.test_user_id)
                print(f"      ✅ 行为记录成功，当前行为数: {behavior_count}")
                
                liked_contents.append(content)
                
                # 模拟真实用户行为间隔
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"      ❌ 记录点赞行为失败: {e}")
        
        return liked_contents
    
    async def _trigger_mbti_evaluation(self, liked_contents: List[Dict]):
        """触发MBTI评分"""
        try:
            print(f"   🔍 开始对 {len(liked_contents)} 条点赞内容进行MBTI评分...")
            
            # 先获取每个内容的详细正文
            print("   📥 正在获取内容详细正文...")
            detailed_contents = []
            
            async with sohu_client as client:
                for i, content in enumerate(liked_contents, 1):
                    try:
                        print(f"      📄 获取第 {i}/{len(liked_contents)} 条内容详情: ID {content['id']}")
                        content_detail = await client.get_content_by_id(content["id"])
                        
                        if content_detail.get("code") == 200 and "data" in content_detail:
                            data = content_detail["data"]
                            content_text = data.get("content", "") or data.get("description", "")
                            title = data.get("title", "")
                            
                            if content_text and len(content_text.strip()) >= 10:
                                detailed_contents.append({
                                    "id": content["id"],
                                    "title": title,
                                    "content": content_text
                                })
                                print(f"         ✅ 获取成功，正文长度: {len(content_text)} 字符")
                            else:
                                print(f"         ⚠️ 正文内容不足，长度: {len(content_text)} 字符")
                        else:
                            print(f"         ❌ 获取失败: {content_detail.get('msg', '未知错误')}")
                        
                        # 避免请求过快
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        print(f"         ❌ 获取内容 {content['id']} 详情失败: {e}")
            
            print(f"   📝 准备对 {len(detailed_contents)} 条有内容的内容进行评分...")
            
            if detailed_contents:
                # 批量评分
                scoring_result = await mbti_service.batch_evaluate_contents(detailed_contents)
                print(f"   ✅ MBTI评分完成: {scoring_result['new_evaluated']} 条新评分")
            else:
                print("   ⚠️ 没有足够内容进行评分")
                
        except Exception as e:
            print(f"   ❌ MBTI评分失败: {e}")
    
    async def _calculate_user_mbti(self) -> Dict[str, Any]:
        """计算用户MBTI档案"""
        try:
            print("   🧮 计算用户MBTI档案...")
            
            # 触发MBTI更新
            update_result = await mbti_service.update_user_mbti_profile(
                user_id=self.test_user_id,
                force_update=True
            )
            
            if update_result.get("updated"):
                print("   ✅ 用户MBTI档案更新成功")
                
                # 获取用户档案
                profile = db_service.get_user_profile(self.test_user_id)
                if profile:
                    mbti_data = {
                        "E": profile.E,
                        "I": profile.I,
                        "S": profile.S,
                        "N": profile.N,
                        "T": profile.T,
                        "F": profile.F,
                        "J": profile.J,
                        "P": profile.P,
                        "mbti_type": profile.mbti_type
                    }
                    print(f"   📊 用户MBTI: {profile.mbti_type}")
                    print(f"   📈 MBTI向量: E={profile.E:.3f}, I={profile.I:.3f}, S={profile.S:.3f}, N={profile.N:.3f}")
                    print(f"   📈 MBTI向量: T={profile.T:.3f}, F={profile.F:.3f}, J={profile.J:.3f}, P={profile.P:.3f}")
                    return mbti_data
            else:
                print("   ⚠️ 用户MBTI档案无需更新")
            
            return {}
            
        except Exception as e:
            print(f"   ❌ 计算用户MBTI失败: {e}")
            return {}
    
    async def _get_mbti_based_recommendations(self) -> List[Dict]:
        """获取基于MBTI的推荐"""
        try:
            print("   🔍 获取基于MBTI的推荐内容...")
            
            # 从搜狐接口获取新的推荐内容
            async with sohu_client as client:
                result = await client.get_article_list(
                    page_num=2,  # 使用不同页面获取新内容
                    page_size=30,
                    state="OnShelf"
                )
            
            if result.get("code") == 200 and "data" in result:
                data = result["data"]
                if isinstance(data, list):
                    articles = data
                elif isinstance(data, dict):
                    articles = data.get("data", [])
                    if not articles and "list" in data:
                        articles = data.get("list", [])
                else:
                    articles = []
                
                # 转换为标准格式
                recommendations = []
                for article in articles[:30]:
                    if article.get("id") and article.get("title"):
                        recommendations.append({
                            "id": article["id"],
                            "title": article.get("title", ""),
                            "content": article.get("content", ""),
                            "type": article.get("type", "article")
                        })
                
                print(f"   ✅ 获取到 {len(recommendations)} 条推荐内容")
                return recommendations
            else:
                print(f"   ❌ 获取推荐内容失败: {result}")
                return []
                
        except Exception as e:
            print(f"   ❌ 获取推荐内容异常: {e}")
            return []
    
    async def _evaluate_recommendation_contents(self, recommendations: List[Dict]):
        """对推荐内容进行MBTI评分"""
        try:
            print(f"   🔍 开始对 {len(recommendations)} 条推荐内容进行MBTI评分...")
            
            # 先获取每个内容的详细正文
            print("   📥 正在获取推荐内容详细正文...")
            detailed_contents = []
            
            async with sohu_client as client:
                for i, content in enumerate(recommendations, 1):
                    try:
                        print(f"      📄 获取第 {i}/{len(recommendations)} 条内容详情: ID {content['id']}")
                        content_detail = await client.get_content_by_id(content["id"])
                        
                        if content_detail.get("code") == 200 and "data" in content_detail:
                            data = content_detail["data"]
                            content_text = data.get("content", "") or data.get("description", "")
                            title = data.get("title", "")
                            
                            if content_text and len(content_text.strip()) >= 10:
                                detailed_contents.append({
                                    "id": content["id"],
                                    "title": title,
                                    "content": content_text
                                })
                                print(f"         ✅ 获取成功，正文长度: {len(content_text)} 字符")
                            else:
                                print(f"         ⚠️ 正文内容不足，长度: {len(content_text)} 字符")
                        else:
                            print(f"         ❌ 获取失败: {content_detail.get('msg', '未知错误')}")
                        
                        # 避免请求过快
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        print(f"         ❌ 获取内容 {content['id']} 详情失败: {e}")
            
            print(f"   📝 准备对 {len(detailed_contents)} 条有内容的内容进行评分...")
            
            if detailed_contents:
                # 批量评分
                scoring_result = await mbti_service.batch_evaluate_contents(detailed_contents)
                print(f"   ✅ MBTI评分完成: {scoring_result['new_evaluated']} 条新评分")
            else:
                print("   ⚠️ 没有足够内容进行评分")
                
        except Exception as e:
            print(f"   ❌ MBTI评分失败: {e}")
    
    async def _sort_by_similarity(self, user_mbti: Dict, recommendations: List[Dict]) -> List[Dict]:
        """基于相似度排序推荐内容"""
        try:
            print("   🔍 基于用户MBTI计算相似度并排序...")
            
            if not user_mbti:
                print("   ⚠️ 用户MBTI不存在，无法计算相似度")
                return recommendations
            
            # 获取用户MBTI向量
            user_vector = [
                user_mbti.get("E", 0.5),
                user_mbti.get("S", 0.5),
                user_mbti.get("T", 0.5),
                user_mbti.get("J", 0.5)
            ]
            
            # 计算每个推荐内容的相似度
            scored_recommendations = []
            for content in recommendations:
                content_id = content["id"]
                
                # 获取内容的MBTI评分
                content_mbti = db_service.get_content_mbti(content_id)
                if content_mbti:
                    content_vector = [
                        content_mbti.E,
                        content_mbti.S,
                        content_mbti.T,
                        content_mbti.J
                    ]
                    
                    # 计算余弦相似度
                    similarity = self._calculate_cosine_similarity(user_vector, content_vector)
                    
                    scored_recommendations.append({
                        **content,
                        "similarity_score": similarity,
                        "mbti_vector": content_vector
                    })
                else:
                    # 如果没有MBTI评分，使用默认相似度
                    scored_recommendations.append({
                        **content,
                        "similarity_score": 0.5,
                        "mbti_vector": [0.5, 0.5, 0.5, 0.5]
                    })
            
            # 按相似度排序
            scored_recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            print(f"   ✅ 相似度排序完成，共 {len(scored_recommendations)} 条内容")
            return scored_recommendations
            
        except Exception as e:
            print(f"   ❌ 相似度排序失败: {e}")
            return recommendations
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        try:
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    async def _show_final_results(self, sorted_recommendations: List[Dict], user_mbti: Dict):
        """展示最终推荐结果"""
        print("   📊 最终推荐结果（按相似度排序）:")
        print("   " + "-" * 60)
        
        if not sorted_recommendations:
            print("   ⚠️ 没有推荐内容")
            return
        
        # 显示前10条推荐
        for i, content in enumerate(sorted_recommendations[:10], 1):
            similarity = content.get("similarity_score", 0)
            title = content.get("title", "")[:40]
            content_id = content.get("id", "")
            
            print(f"   {i:2d}. 相似度: {similarity:.4f} | ID: {content_id} | {title}...")
        
        if len(sorted_recommendations) > 10:
            print(f"   ... 还有 {len(sorted_recommendations) - 10} 条推荐内容")
        
        # 显示统计信息
        if user_mbti:
            print(f"\n   👤 用户MBTI档案:")
            print(f"     类型: {user_mbti.get('mbti_type', '未知')}")
            print(f"     向量: E={user_mbti.get('E', 0):.3f}, S={user_mbti.get('S', 0):.3f}, T={user_mbti.get('T', 0):.3f}, J={user_mbti.get('J', 0):.3f}")
        
        # 相似度分布
        similarities = [r.get("similarity_score", 0) for r in sorted_recommendations]
        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
            max_similarity = max(similarities)
            min_similarity = min(similarities)
            
            print(f"\n   📈 相似度统计:")
            print(f"     平均: {avg_similarity:.4f}")
            print(f"     最高: {max_similarity:.4f}")
            print(f"     最低: {min_similarity:.4f}")

async def main():
    """主函数"""
    print("🧪 MBTI推荐系统完整流程测试")
    print("=" * 80)
    print("测试流程:")
    print("1. 随机推荐60条内容")
    print("2. 用户点赞50条内容")
    print("3. 触发MBTI评分")
    print("4. 计算用户MBTI档案")
    print("5. 获取基于MBTI的推荐")
    print("6. 对推荐内容进行MBTI评分")
    print("7. 基于相似度排序")
    print("8. 展示最终结果")
    print("=" * 80)
    
    # 创建测试器
    tester = RecommendationFlowTester()
    
    # 运行测试
    await tester.test_full_flow()

if __name__ == "__main__":
    asyncio.run(main()) 