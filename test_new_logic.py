#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的推荐逻辑
验证用户每次操作都直接调用大模型评分，推荐时直接取10条评分并排序
"""

import asyncio
from database_service import db_service
from mbti_service import mbti_service

async def test_new_recommendation_logic():
    """测试新的推荐逻辑"""
    print("🧪 测试新的推荐逻辑")
    print("=" * 80)
    
    test_user_id = 999
    
    try:
        # 步骤1: 模拟用户操作，触发内容评分
        print("📋 步骤1: 模拟用户操作，触发内容评分")
        print("-" * 50)
        
        # 模拟用户对几个内容进行操作
        test_contents = [3055, 3054, 3053, 3050, 3049]
        
        for content_id in test_contents:
            print(f"   👤 用户 {test_user_id} 对内容 {content_id} 进行操作...")
            
            # 记录用户行为（这会触发内容评分）
            behavior = db_service.record_user_behavior(
                user_id=test_user_id,
                content_id=content_id,
                action="like",
                source="test",
                session_id=f"test_session_{content_id}",
                extra_data={"test": True}
            )
            
            print(f"      ✅ 行为记录成功，行为ID: {behavior.id}")
            
            # 检查内容是否已有MBTI评分
            content_mbti = db_service.get_content_mbti(content_id)
            if content_mbti:
                print(f"      📊 内容 {content_id} 已有MBTI评分")
            else:
                print(f"      ⏳ 内容 {content_id} 等待MBTI评分")
        
        # 步骤2: 获取推荐（这会触发评分和排序）
        print("\n📋 步骤2: 获取推荐（触发评分和排序）")
        print("-" * 50)
        
        print("   🔍 获取用户推荐...")
        recommendations = db_service.get_recommendations_for_user(
            user_id=test_user_id,
            limit=10
        )
        
        print(f"   ✅ 推荐获取成功")
        print(f"   📊 推荐数量: {len(recommendations.get('recommendations', []))}")
        
        # 显示推荐结果
        if 'recommendations' in recommendations:
            print("\n   📋 推荐结果（按相似度排序）:")
            for i, rec in enumerate(recommendations['recommendations'][:5], 1):
                content_id = rec.get('content_id')
                title = rec.get('title', '')[:30]
                similarity = rec.get('similarity_score', 0)
                print(f"      {i}. ID: {content_id} | 相似度: {similarity:.4f} | {title}...")
        
        # 显示统计信息
        if 'similarity_stats' in recommendations:
            stats = recommendations['similarity_stats']
            print(f"\n   📈 相似度统计:")
            print(f"      平均: {stats.get('average', 0):.4f}")
            print(f"      最高: {stats.get('maximum', 0):.4f}")
            print(f"      最低: {stats.get('minimum', 0):.4f}")
        
        # 显示元数据
        if 'metadata' in recommendations:
            metadata = recommendations['metadata']
            print(f"\n   📊 元数据:")
            print(f"      候选内容: {metadata.get('total_candidates', 0)}")
            print(f"      有效内容: {metadata.get('valid_candidates', 0)}")
            print(f"      已评分: {metadata.get('scored_contents', 0)}")
            print(f"      推荐数量: {metadata.get('recommendation_count', 0)}")
            print(f"      待评分: {metadata.get('scoring_pending', 0)}")
        
        # 步骤3: 检查数据库中的评分状态
        print("\n📋 步骤3: 检查数据库中的评分状态")
        print("-" * 50)
        
        total_scored = 0
        for content_id in test_contents:
            content_mbti = db_service.get_content_mbti(content_id)
            if content_mbti:
                total_scored += 1
                print(f"   ✅ 内容 {content_id}: 已评分")
            else:
                print(f"   ⏳ 内容 {content_id}: 未评分")
        
        print(f"\n   📊 总评分状态: {total_scored}/{len(test_contents)} 条内容已评分")
        
        print("\n🎉 新推荐逻辑测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    await test_new_recommendation_logic()

if __name__ == "__main__":
    asyncio.run(main()) 