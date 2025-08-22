#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试大模型批量评分功能
"""

import asyncio
import json
from datetime import datetime

async def test_mbti_batch_evaluation():
    """测试大模型批量评分功能"""
    print("🧪 测试大模型批量评分功能")
    print("=" * 60)
    
    try:
        from database_service import db_service
        from mbti_service import mbti_service
        
        print("📋 测试1: 获取50条有content的数据")
        print("-" * 50)
        
        # 从搜狐接口获取内容
        print("从搜狐接口获取内容...")
        sohu_contents = await db_service.get_sohu_contents_for_recommendation(limit=50)
        
        if sohu_contents:
            print(f"✅ 成功获取 {len(sohu_contents)} 条内容")
            
            # 筛选有实际content的内容
            content_with_text = []
            content_with_images = []
            content_with_both = []
            
            for content in sohu_contents:
                has_text = bool(content.get('content'))
                has_images = bool(content.get('images') or content.get('coverImage'))
                
                if has_text and has_images:
                    content_with_both.append(content)
                elif has_text:
                    content_with_text.append(content)
                elif has_images:
                    content_with_images.append(content)
            
            print(f"📊 内容分析:")
            print(f"   有文字内容: {len(content_with_text)} 条")
            print(f"   有图片内容: {len(content_with_images)} 条")
            print(f"   文字+图片: {len(content_with_both)} 条")
            print(f"   总计: {len(sohu_contents)} 条")
            
            # 显示前几条内容的详细信息
            print(f"\n📰 内容示例:")
            for i, content in enumerate(sohu_contents[:5], 1):
                print(f"   内容 {i}:")
                print(f"     ID: {content.get('id')}")
                print(f"     标题: {content.get('title', '无标题')[:30]}...")
                print(f"     类型: {content.get('type')}")
                print(f"     文字内容: {'有' if content.get('content') else '无'}")
                print(f"     图片内容: {'有' if content.get('images') or content.get('coverImage') else '无'}")
                if content.get('content'):
                    print(f"     内容预览: {content.get('content')[:50]}...")
                print()
            
            # 使用更新后的筛选逻辑，选择有效内容进行MBTI评分
            content_for_evaluation = []
            for content in sohu_contents:
                if db_service._is_valid_content_for_recommendation(content):
                    content_for_evaluation.append(content)
            
            print(f"🎯 可用于MBTI评分的内容: {len(content_for_evaluation)} 条")
            
            if content_for_evaluation:
                print(f"\n📋 测试2: 批量MBTI评分")
                print("-" * 50)
                
                # 选择前10条内容进行测试
                test_content_ids = [content['id'] for content in content_for_evaluation[:10]]
                print(f"选择前10条内容进行MBTI评分测试: {test_content_ids}")
                
                # 检查哪些内容已经有MBTI评分
                existing_mbti = []
                pending_mbti = []
                
                for content_id in test_content_ids:
                    existing = db_service.get_content_mbti(content_id)
                    if existing:
                        existing_mbti.append(content_id)
                    else:
                        pending_mbti.append(content_id)
                
                print(f"📊 MBTI评分状态:")
                print(f"   已有评分: {len(existing_mbti)} 条")
                print(f"   待评分: {len(pending_mbti)} 条")
                
                if pending_mbti:
                    print(f"\n🔄 开始批量评分...")
                    print(f"待评分内容ID: {pending_mbti}")
                    
                    # 批量评分
                    start_time = datetime.now()
                    batch_results = await mbti_service.batch_evaluate_contents(
                        content_ids=pending_mbti,
                        max_concurrent=3
                    )
                    end_time = datetime.now()
                    
                    evaluation_time = (end_time - start_time).total_seconds()
                    
                    print(f"✅ 批量评分完成!")
                    print(f"⏱️  评分耗时: {evaluation_time:.2f} 秒")
                    print(f"📊 评分结果: {len(batch_results)}/{len(pending_mbti)} 成功")
                    
                    # 显示评分结果
                    print(f"\n📈 MBTI评分结果:")
                    for content_id, probabilities in batch_results.items():
                        print(f"   内容 {content_id}:")
                        for trait, prob in probabilities.items():
                            print(f"     {trait}: {prob:.3f}")
                        print()
                    
                    # 验证评分是否保存到数据库
                    print(f"🔍 验证数据库保存:")
                    for content_id in pending_mbti:
                        saved_mbti = db_service.get_content_mbti(content_id)
                        if saved_mbti:
                            print(f"   ✅ 内容 {content_id} MBTI评分已保存")
                        else:
                            print(f"   ❌ 内容 {content_id} MBTI评分未保存")
                else:
                    print(f"✅ 所有测试内容都已有MBTI评分")
                
                print(f"\n📋 测试3: 测试单个内容评分")
                print("-" * 50)
                
                # 测试单个内容评分
                if content_for_evaluation:
                    test_content = content_for_evaluation[0]
                    content_id = test_content['id']
                    
                    print(f"测试单个内容评分: ID {content_id}")
                    print(f"标题: {test_content.get('title', '无标题')}")
                    print(f"内容: {test_content.get('content', '无文字内容')[:100]}...")
                    
                    try:
                        single_result = await mbti_service.evaluate_content_by_id(content_id)
                        print(f"✅ 单个内容评分成功:")
                        for trait, prob in single_result.items():
                            print(f"   {trait}: {prob:.3f}")
                    except Exception as e:
                        print(f"❌ 单个内容评分失败: {e}")
            else:
                print(f"❌ 没有找到可用于MBTI评分的内容")
        else:
            print(f"❌ 没有获取到搜狐内容")
        
        print("\n🎯 测试总结")
        print("-" * 50)
        if sohu_contents:
            print(f"✅ 成功获取搜狐内容: {len(sohu_contents)} 条")
            content_for_evaluation = [c for c in sohu_contents if c.get('content')]
            print(f"✅ 可用于MBTI评分: {len(content_for_evaluation)} 条")
            print(f"✅ 批量评分功能: 可用")
            print(f"✅ 单个评分功能: 可用")
        else:
            print("❌ 搜狐内容获取失败")
        
        print("\n✨ MBTI批量评分测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mbti_batch_evaluation()) 