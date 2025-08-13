#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试MBTI系统功能
测试内容：
1. MBTI测试模型对内容的评价（使用真实API接口）
2. 用户对内容的操作记录和获取
3. 推荐算法功能
4. 数据库读写操作
"""

import asyncio
import sqlite3
import random
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
import subprocess
import threading

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from mbti_service import mbti_service
    from database_service import db_service
    from models import UserProfile, UserBehavior, ContentMBTI, RecommendationLog
    print("✅ 成功导入所有必要的模块")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保所有依赖已安装")
    sys.exit(1)

class ComprehensiveTester:
    """全面测试器"""
    
    def __init__(self):
        self.test_user_id = 9999
        self.test_content_ids = [1001, 1002, 1003, 1004, 1005, 1006]
        self.test_behaviors = []
        self.api_base_url = "http://localhost:8000"
        self.api_process = None
        
    def start_api_server(self):
        """启动API服务器"""
        print("\n🚀 启动API服务器...")
        try:
            # 启动API服务器作为后台进程
            self.api_process = subprocess.Popen(
                [sys.executable, "main_api.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # 等待服务器启动
            print("⏳ 等待API服务器启动...")
            time.sleep(5)
            
            # 检查服务器是否启动成功
            try:
                response = requests.get(f"{self.api_base_url}/health", timeout=10)
                if response.status_code == 200:
                    print("✅ API服务器启动成功")
                    return True
                else:
                    print(f"❌ API服务器响应异常: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"❌ 无法连接到API服务器: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 启动API服务器失败: {e}")
            return False
    
    def stop_api_server(self):
        """停止API服务器"""
        if self.api_process:
            print("\n🛑 停止API服务器...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=10)
                print("✅ API服务器已停止")
            except subprocess.TimeoutExpired:
                self.api_process.kill()
                print("⚠️  强制停止API服务器")
            self.api_process = None
    
    def setup_test_data(self):
        """设置测试数据"""
        print("\n🔧 设置测试数据")
        print("=" * 50)
        
        # 清空现有测试数据
        self.cleanup_test_data()
        
        # 创建测试用户档案
        print("👤 创建测试用户档案...")
        test_profile = db_service.create_user_profile(
            user_id=self.test_user_id,
            E=0.6, I=0.4,  # 偏外向
            S=0.7, N=0.3,  # 偏感觉
            T=0.8, F=0.2,  # 偏思维
            J=0.9, P=0.1   # 偏判断
        )
        print(f"✅ 创建用户档案: {test_profile.mbti_type}")
        
        # 生成真实的测试帖子内容
        print("\n📝 生成真实测试帖子内容...")
        test_posts = [
            {
                "content_id": 1001,
                "title": "团队协作的力量：如何打造高效的工作环境",
                "content": "我真心喜欢和团队一起工作！今天我们小组讨论了新项目，每个人都积极发言，分享自己的想法。通过大家的集思广益，我们很快就找到了创新的解决方案。团队合作让我感到充满活力，看到每个人的贡献汇聚成最终成果真的很有成就感！我喜欢在开放的环境中与同事交流，这种互动让我学到很多新东西。"
            },
            {
                "content_id": 1002,
                "title": "独处思考的价值：在安静中找到灵感",
                "content": "我发现最好的想法往往在独处时产生。今天下午一个人在咖啡厅里静静思考，突然对复杂的技术问题有了新的理解。我喜欢这种深度思考的过程，能够完全沉浸在问题的本质中，不被外界干扰。独立分析让我能够看到别人忽略的细节。有时候，安静的环境比热闹的讨论更能激发创造力。"
            },
            {
                "content_id": 1003,
                "title": "数据驱动的决策：用理性分析解决问题",
                "content": "在做重要决策时，我坚持用数据说话。通过收集相关指标、分析历史趋势、建立预测模型，我们能够做出更加理性和准确的判断。感性的直觉有时会误导我们，只有客观的逻辑分析才能确保决策的科学性和有效性。我喜欢用事实和数据来支持我的观点，这样更有说服力。"
            },
            {
                "content_id": 1004,
                "title": "关怀他人的重要性：建立温暖的人际关系",
                "content": "我始终相信，关心他人的感受比追求完美的逻辑更重要。在团队中，我经常会询问同事的想法，确保每个人都感到被尊重和理解。当有人遇到困难时，我会主动提供帮助和情感支持。人与人之间的温暖连接是工作和生活中最珍贵的财富。我注重团队的氛围，希望每个人都能感到被关心。"
            },
            {
                "content_id": 1005,
                "title": "计划的重要性：有条理地实现目标",
                "content": "我是一个非常有计划性的人，喜欢把所有事情都安排得井井有条。每天早上我都会制定详细的待办清单，按优先级排序任务。这样的安排让我能够高效地完成工作，避免遗漏重要事项。我认为良好的计划是成功的基础。我喜欢按部就班地执行计划，这样让我感到安心和有序。"
            },
            {
                "content_id": 1006,
                "title": "拥抱变化与灵活性：在不确定中成长",
                "content": "我喜欢保持开放的心态，随时准备应对新的挑战和机会。当计划发生变化时，我会积极调整策略，寻找新的可能性。这种灵活性让我能够在不确定的环境中茁壮成长，把每一次变化都看作是学习和成长的机会。我不喜欢被固定的计划束缚，更喜欢随机应变。"
            }
        ]
        
        # 保存帖子内容到数据库（这里我们只是保存MBTI评价，实际内容可以存储在内容管理系统中）
        print("💾 保存帖子内容信息...")
        for post in test_posts:
            print(f"   📝 帖子 {post['content_id']}: {post['title']}")
            print(f"      内容预览: {post['content'][:80]}...")
        
        # 创建测试用户行为
        print("\n📊 创建测试用户行为记录...")
        actions = ["view", "like", "collect", "comment", "share"]
        sources = ["recommendation", "search", "trending", "manual"]
        
        for i, post in enumerate(test_posts):
            # 每个内容创建多个行为
            for j in range(random.randint(2, 4)):
                behavior_data = {
                    "user_id": self.test_user_id,
                    "content_id": post["content_id"],
                    "action": random.choice(actions),
                    "weight": random.uniform(0.1, 1.0),
                    "source": random.choice(sources),
                    "session_id": f"test_session_{i}_{j}",
                    "extra_data": {"test": True, "batch": i, "post_title": post["title"]}
                }
                
                behavior = db_service.record_user_behavior(**behavior_data)
                self.test_behaviors.append(behavior)
                print(f"✅ 行为记录: {behavior.action} 内容 {post['content_id']}")
        
        print(f"\n🎉 测试数据设置完成！")
        print(f"   用户档案: 1个")
        print(f"   测试帖子: {len(test_posts)}个")
        print(f"   用户行为: {len(self.test_behaviors)}条")
        
        # 保存帖子内容到类变量中，供后续测试使用
        self.test_posts = test_posts
    
    def cleanup_test_data(self):
        """清理测试数据"""
        try:
            with db_service.get_session() as session:
                # 删除测试用户档案
                session.query(UserProfile).filter(
                    UserProfile.user_id == self.test_user_id
                ).delete()
                
                # 删除测试内容MBTI（使用test_content_ids或test_posts中的content_id）
                if hasattr(self, 'test_posts') and self.test_posts:
                    content_ids = [post["content_id"] for post in self.test_posts]
                else:
                    content_ids = self.test_content_ids
                
                if content_ids:
                    session.query(ContentMBTI).filter(
                        ContentMBTI.content_id.in_(content_ids)
                    ).delete()
                
                # 删除测试用户行为
                session.query(UserBehavior).filter(
                    UserBehavior.user_id == self.test_user_id
                ).delete()
                
                # 删除测试推荐日志
                session.query(RecommendationLog).filter(
                    RecommendationLog.user_id == self.test_user_id
                ).delete()
                
                session.commit()
                print("🧹 测试数据清理完成")
        except Exception as e:
            print(f"⚠️  清理测试数据时出错: {e}")
    
    async def test_mbti_evaluation(self):
        """测试MBTI评价功能（使用真实API接口）"""
        print("\n🧠 测试MBTI评价功能（真实API接口）")
        print("=" * 50)
        
        try:
            # 使用生成的测试帖子内容
            if not hasattr(self, 'test_posts') or not self.test_posts:
                print("❌ 没有测试帖子内容，请先运行setup_test_data")
                return False
            
            print("📝 通过API接口测试MBTI模型对真实帖子内容的评价...")
            evaluation_results = {}
            
            for post in self.test_posts:
                content_id = post["content_id"]
                title = post["title"]
                content = post["content"]
                
                print(f"\n🔍 评价帖子 {content_id}: {title}")
                print(f"   内容预览: {content[:80]}...")
                
                try:
                    # 调用API接口进行MBTI评价
                    print("   🌐 调用API接口...")
                    start_time = time.time()
                    
                    response = requests.post(
                        f"{self.api_base_url}/api/v1/admin/content/{content_id}/evaluate",
                        json={
                            "content_id": content_id,
                            "content": content,
                            "title": title
                        },
                        timeout=30
                    )
                    
                    api_time = time.time() - start_time
                    print(f"   ⏱️  API调用耗时: {api_time:.2f}秒")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   ✅ API调用成功")
                        
                        if result.get("success"):
                            if result["data"].get("already_evaluated"):
                                # 内容已评价，直接从响应中获取结果
                                probabilities = result["data"]["mbti_analysis"]
                                print("   ✅ 获取到MBTI评价结果（已存在）")
                                for trait, prob in probabilities.items():
                                    print(f"      {trait}: {prob:.3f}")
                                
                                evaluation_results[content_id] = {
                                    "probabilities": probabilities,
                                    "title": title,
                                    "content": content,
                                    "api_time": api_time
                                }
                            elif result["data"].get("evaluation_completed"):
                                # 评价刚完成，直接从响应中获取结果
                                probabilities = result["data"]["mbti_analysis"]
                                print("   ✅ 获取到MBTI评价结果（新评价）")
                                for trait, prob in probabilities.items():
                                    print(f"      {trait}: {prob:.3f}")
                                
                                evaluation_results[content_id] = {
                                    "probabilities": probabilities,
                                    "title": title,
                                    "content": content,
                                    "api_time": api_time
                                }
                            else:
                                print(f"   ⚠️  评价响应格式异常: {result}")
                        else:
                            print(f"   ❌ API调用失败: {result.get('message', '未知错误')}")
                    else:
                        print(f"   ❌ API调用失败: HTTP {response.status_code}")
                        print(f"      响应: {response.text}")
                    
                except Exception as e:
                    print(f"   ❌ 评价失败: {e}")
            
            # 验证数据库保存
            print(f"\n💾 验证评价结果数据库保存...")
            for post in self.test_posts:
                content_id = post["content_id"]
                saved_mbti = db_service.get_content_mbti(content_id)
                if saved_mbti:
                    print(f"   ✅ 内容 {content_id} 评价已保存到数据库")
                    print(f"      模型版本: {saved_mbti.model_version}")
                    print(f"      创建时间: {saved_mbti.created_at}")
                else:
                    print(f"   ❌ 内容 {content_id} 评价未保存到数据库")
            
            # 分析评价质量
            print(f"\n📊 评价质量分析...")
            total_posts = len(evaluation_results)
            if total_posts > 0:
                print(f"   成功评价: {total_posts} 个帖子")
                print(f"   评价成功率: {total_posts}/{len(self.test_posts)} = {total_posts/len(self.test_posts)*100:.1f}%")
                
                # 计算平均API调用时间
                total_api_time = sum(result.get("api_time", 0) for result in evaluation_results.values())
                avg_api_time = total_api_time / total_posts if total_posts > 0 else 0
                print(f"   平均API调用时间: {avg_api_time:.2f}秒")
                
                # 分析评价结果分布合理性（仅校验成对概率和为1）
                self.analyze_evaluation_quality(evaluation_results)
            else:
                print("   ⚠️  没有成功评价的帖子")
            
            return total_posts > 0
            
        except Exception as e:
            print(f"❌ MBTI评价测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def analyze_evaluation_quality(self, evaluation_results):
        """分析评价结果的质量"""
        print(f"\n🔍 评价结果质量分析...")
        
        for content_id, result in evaluation_results.items():
            probabilities = result["probabilities"]
            title = result["title"]
            
            print(f"\n   帖子 {content_id}: {title}")
            
            # 检查每个维度的概率分布
            dimensions = [("E", "I"), ("S", "N"), ("T", "F"), ("J", "P")]
            for dim1, dim2 in dimensions:
                prob1 = probabilities.get(dim1, 0)
                prob2 = probabilities.get(dim2, 0)
                
                # 检查概率和是否为1
                total_prob = prob1 + prob2
                if abs(total_prob - 1.0) > 0.01:
                    print(f"     ⚠️  {dim1}-{dim2} 维度概率和不为1: {prob1:.3f} + {prob2:.3f} = {total_prob:.3f}")
                else:
                    print(f"     ✅ {dim1}-{dim2} 维度概率和正确: {prob1:.3f} + {prob2:.3f} = {total_prob:.3f}")
    
    def test_user_behavior_operations(self):
        """测试用户行为操作功能"""
        print("\n📊 测试用户行为操作功能")
        print("=" * 50)
        
        try:
            # 测试记录新行为
            print("➕ 测试记录新用户行为...")
            new_behavior = db_service.record_user_behavior(
                user_id=self.test_user_id,
                content_id=9999,
                action="test_action",
                weight=0.8,
                source="test_source",
                session_id="test_session_new",
                extra_data={"test": True, "new": True}
            )
            
            if new_behavior:
                print("✅ 新行为记录成功")
                print(f"   行为ID: {new_behavior.id}")
                print(f"   用户ID: {new_behavior.user_id}")
                print(f"   内容ID: {new_behavior.content_id}")
                print(f"   行为: {new_behavior.action}")
            else:
                print("❌ 新行为记录失败")
                return False
            
            # 测试获取用户行为历史
            print("\n📖 测试获取用户行为历史...")
            user_behaviors, total_count = db_service.get_user_behaviors(
                user_id=self.test_user_id,
                limit=20
            )
            
            if user_behaviors:
                print(f"✅ 获取到 {len(user_behaviors)} 条用户行为 (总计: {total_count})")
                print("   最近的行为:")
                for i, behavior in enumerate(user_behaviors[:5]):
                    print(f"     {i+1}. {behavior.action} 内容 {behavior.content_id} "
                          f"({behavior.timestamp.strftime('%Y-%m-%d %H:%M')})")
            else:
                print("❌ 获取用户行为历史失败")
                return False
            
            # 测试获取特定内容的行为
            print("\n🎯 测试获取特定内容的行为...")
            content_behaviors = db_service.get_content_behaviors(
                content_id=1001,
                limit=10
            )
            
            if content_behaviors:
                print(f"✅ 获取到内容 {1001} 的 {len(content_behaviors)} 条行为")
            else:
                print("❌ 获取内容行为失败")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 用户行为操作测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_recommendation_algorithm(self):
        """测试推荐算法功能"""
        print("\n🎯 测试推荐算法功能")
        print("=" * 50)
        
        try:
            # 测试用户推荐
            print("🔍 测试为用户生成推荐...")
            recommendations = db_service.get_recommendations_for_user(
                user_id=self.test_user_id,
                limit=10,
                similarity_threshold=0.3,
                exclude_viewed=False
            )
            
            if recommendations and recommendations.get("recommendations"):
                recs = recommendations["recommendations"]
                print(f"✅ 生成推荐成功: {len(recs)} 条推荐")
                print("   推荐结果:")
                for i, rec in enumerate(recs[:5]):
                    print(f"     {i+1}. 内容 {rec['content_id']} "
                          f"相似度: {rec['similarity_score']:.3f} "
                          f"排名: {rec['rank']}")
                
                # 显示元数据
                metadata = recommendations.get("metadata", {})
                print(f"\n📊 推荐元数据:")
                print(f"   候选内容总数: {metadata.get('total_candidates', 0)}")
                print(f"   过滤后数量: {metadata.get('filtered_count', 0)}")
                print(f"   平均相似度: {metadata.get('avg_similarity', 0):.3f}")
                print(f"   算法版本: {metadata.get('algorithm_version', 'unknown')}")
            else:
                print("❌ 生成推荐失败")
                return False
            
            # 测试相似度计算
            print("\n🧮 测试MBTI相似度计算...")
            user_profile = db_service.get_user_profile(self.test_user_id)
            if user_profile:
                user_vector = [
                    user_profile.E, user_profile.I, user_profile.S, user_profile.N,
                    user_profile.T, user_profile.F, user_profile.J, user_profile.P
                ]
                
                # 获取一些内容向量
                contents = db_service.get_contents_for_recommendation(limit=5)
                if contents:
                    content_vectors = [content.get_vector() for content in contents]
                    similarities = db_service.calculate_mbti_similarity(user_vector, content_vectors)
                    
                    print(f"✅ 相似度计算成功: {len(similarities)} 个内容")
                    for i, (content, sim) in enumerate(zip(contents, similarities)):
                        print(f"   内容 {content.content_id}: 相似度 {sim:.3f}")
                else:
                    print("⚠️  没有内容用于相似度计算")
            
            return True
            
        except Exception as e:
            print(f"❌ 推荐算法测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_database_read_write(self):
        """测试数据库读写操作"""
        print("\n💾 测试数据库读写操作")
        print("=" * 50)
        
        try:
            # 测试读取操作
            print("📖 测试数据库读取操作...")
            
            # 读取用户档案
            user_profile = db_service.get_user_profile(self.test_user_id)
            if user_profile:
                print("✅ 读取用户档案成功")
                print(f"   MBTI类型: {user_profile.mbti_type}")
                print(f"   E: {user_profile.E:.3f}, I: {user_profile.I:.3f}")
                print(f"   S: {user_profile.S:.3f}, N: {user_profile.N:.3f}")
                print(f"   T: {user_profile.T:.3f}, F: {user_profile.F:.3f}")
                print(f"   J: {user_profile.J:.3f}, P: {user_profile.P:.3f}")
            else:
                print("❌ 读取用户档案失败")
                return False
            
            # 读取内容MBTI
            content_mbti = db_service.get_content_mbti(1001)
            if content_mbti:
                print("✅ 读取内容MBTI成功")
                print(f"   内容ID: {content_mbti.content_id}")
                print(f"   模型版本: {content_mbti.model_version}")
                print(f"   创建时间: {content_mbti.created_at}")
            else:
                print("❌ 读取内容MBTI失败")
                return False
            
            # 测试写入操作
            print("\n✏️  测试数据库写入操作...")
            
            # 更新用户档案
            old_mbti_type = user_profile.mbti_type
            updated_profile = db_service.update_user_profile(
                user_id=self.test_user_id,
                probabilities={
                    "E": 0.7, "I": 0.3,
                    "S": 0.8, "N": 0.2,
                    "T": 0.9, "F": 0.1,
                    "J": 0.95, "P": 0.05
                }
            )
            
            if updated_profile and updated_profile.mbti_type != old_mbti_type:
                print("✅ 更新用户档案成功")
                print(f"   MBTI类型变化: {old_mbti_type} -> {updated_profile.mbti_type}")
            else:
                print("❌ 更新用户档案失败")
                return False
            
            # 测试事务回滚
            print("\n🔄 测试事务回滚...")
            try:
                with db_service.get_session() as session:
                    # 尝试插入无效数据
                    invalid_behavior = UserBehavior(
                        user_id=None,  # 这会导致错误
                        content_id=9999,
                        action="test"
                    )
                    session.add(invalid_behavior)
                    session.commit()  # 这里应该失败
            except Exception as e:
                print("✅ 事务回滚测试成功 - 无效数据被拒绝")
                print(f"   错误信息: {e}")
            
            # 验证数据完整性
            print("\n🔍 验证数据完整性...")
            final_profile = db_service.get_user_profile(self.test_user_id)
            if final_profile and final_profile.mbti_type == updated_profile.mbti_type:
                print("✅ 数据完整性验证通过")
            else:
                print("❌ 数据完整性验证失败")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库读写测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始全面测试MBTI系统")
        print("=" * 60)
        
        # 启动API服务器
        self.start_api_server()
        
        # 设置测试数据
        self.setup_test_data()
        
        # 运行各项测试
        test_results = []
        
        # 1. MBTI评价测试
        print("\n" + "="*60)
        result1 = await self.test_mbti_evaluation()
        test_results.append(("MBTI评价功能", result1))
        
        # 2. 用户行为操作测试
        print("\n" + "="*60)
        result2 = self.test_user_behavior_operations()
        test_results.append(("用户行为操作", result2))
        
        # 3. 推荐算法测试
        print("\n" + "="*60)
        result3 = self.test_recommendation_algorithm()
        test_results.append(("推荐算法功能", result3))
        
        # 4. 数据库读写测试
        print("\n" + "="*60)
        result4 = self.test_database_read_write()
        test_results.append(("数据库读写操作", result4))
        
        # 停止API服务器
        self.stop_api_server()
        
        # 输出测试总结
        print("\n" + "="*60)
        print("📊 测试结果总结")
        print("="*60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎉 所有测试都通过了！系统运行正常。")
        else:
            print("⚠️  部分测试失败，请检查相关功能。")
        
        # 保留测试数据以供查看
        print("\n💾 保留测试数据以供查看...")
        print("   如需清理数据，请手动运行 cleanup_test_data() 方法")
        
        return passed == total

async def main():
    """主函数"""
    tester = ComprehensiveTester()
    
    try:
        success = await tester.run_all_tests()
        if success:
            print("\n🎊 测试完成！系统功能正常。")
        else:
            print("\n⚠️  测试完成，但发现问题。")
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保API服务器被停止
        tester.stop_api_server()

if __name__ == "__main__":
    # 检查数据库文件
    db_path = "mbti_system.db"
    if not Path(db_path).exists():
        print(f"❌ 数据库文件 {db_path} 不存在")
        print("请先运行 simple_test.py 创建数据库")
        sys.exit(1)
    
    # 检查依赖
    try:
        import requests
    except ImportError:
        print("❌ 缺少requests库，请安装: pip install requests")
        sys.exit(1)
    
    # 运行测试
    asyncio.run(main())
