#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新后的内容筛选逻辑
"""

import asyncio
import json
from datetime import datetime

async def test_content_filtering_updated():
    """测试更新后的内容筛选逻辑"""
    print("🧪 测试更新后的内容筛选逻辑")
    print("=" * 60)
    
    try:
        from database_service import db_service
        
        print("📋 测试1: 获取50条内容并分析筛选结果")
        print("-" * 50)
        
        # 从搜狐接口获取内容
        print("从搜狐接口获取内容...")
        sohu_contents = await db_service.get_sohu_contents_for_recommendation(limit=50)
        
        if sohu_contents:
            print(f"✅ 成功获取 {len(sohu_contents)} 条内容")
            
            # 使用更新后的筛选逻辑
            valid_contents = []
            invalid_contents = []
            
            for content in sohu_contents:
                if db_service._is_valid_content_for_recommendation(content):
                    valid_contents.append(content)
                else:
                    invalid_contents.append(content)
            
            print(f"📊 筛选结果:")
            print(f"   有效内容: {len(valid_contents)} 条")
            print(f"   无效内容: {len(invalid_contents)} 条")
            print(f"   筛选率: {len(valid_contents)/len(sohu_contents)*100:.1f}%")
            
            # 分析有效内容的特征
            if valid_contents:
                print(f"\n✅ 有效内容特征分析:")
                content_with_text = sum(1 for c in valid_contents if c.get('content'))
                content_with_images = sum(1 for c in valid_contents if c.get('images'))
                content_with_cover = sum(1 for c in valid_contents if c.get('coverImage') or c.get('coverUrl'))
                content_with_title = sum(1 for c in valid_contents if c.get('title'))
                
                print(f"   有标题: {content_with_title}/{len(valid_contents)}")
                print(f"   有文字内容: {content_with_text}/{len(valid_contents)}")
                print(f"   有图片列表: {content_with_images}/{len(valid_contents)}")
                print(f"   有封面图片: {content_with_cover}/{len(valid_contents)}")
                
                # 显示前几条有效内容
                print(f"\n📰 有效内容示例:")
                for i, content in enumerate(valid_contents[:5], 1):
                    print(f"   内容 {i}:")
                    print(f"     ID: {content.get('id')}")
                    print(f"     标题: {content.get('title', '无标题')[:30]}...")
                    print(f"     类型: {content.get('type')}")
                    print(f"     文字内容: {'有' if content.get('content') else '无'}")
                    print(f"     图片内容: {'有' if content.get('images') else '无'}")
                    print(f"     封面图片: {'有' if content.get('coverImage') or content.get('coverUrl') else '无'}")
                    if content.get('content'):
                        print(f"     内容预览: {content.get('content')[:50]}...")
                    print()
            
            # 分析无效内容的原因
            if invalid_contents:
                print(f"\n❌ 无效内容原因分析:")
                no_title = sum(1 for c in invalid_contents if not c.get('title'))
                no_cover = sum(1 for c in invalid_contents if not c.get('coverImage') and not c.get('coverUrl'))
                wrong_state = sum(1 for c in invalid_contents if c.get('state') != 'OnShelf')
                wrong_audit = sum(1 for c in invalid_contents if c.get('auditState') != 'Pass')
                
                print(f"   无标题: {no_title}")
                print(f"   无封面: {no_cover}")
                print(f"   状态错误: {wrong_state}")
                print(f"   审核错误: {wrong_audit}")
                
                # 显示前几条无效内容
                print(f"\n📰 无效内容示例:")
                for i, content in enumerate(invalid_contents[:3], 1):
                    print(f"   内容 {i}:")
                    print(f"     ID: {content.get('id')}")
                    print(f"     标题: {content.get('title', '无标题')}")
                    print(f"     状态: {content.get('state')}")
                    print(f"     审核: {content.get('auditState')}")
                    print(f"     封面: {content.get('coverImage') or content.get('coverUrl') or '无'}")
                    print()
            
            print(f"\n📋 测试2: 验证筛选逻辑的合理性")
            print("-" * 50)
            
            # 测试一些边界情况
            test_cases = [
                {
                    "name": "完整内容",
                    "content": {"title": "测试标题", "content": "测试内容", "coverImage": "test.jpg", "state": "OnShelf", "auditState": "Pass"},
                    "expected": True
                },
                {
                    "name": "只有标题和封面",
                    "content": {"title": "测试标题", "coverImage": "test.jpg", "state": "OnShelf", "auditState": "Pass"},
                    "expected": True
                },
                {
                    "name": "无标题",
                    "content": {"content": "测试内容", "coverImage": "test.jpg", "state": "OnShelf", "auditState": "Pass"},
                    "expected": False
                },
                {
                    "name": "无封面",
                    "content": {"title": "测试标题", "content": "测试内容", "state": "OnShelf", "auditState": "Pass"},
                    "expected": False
                },
                {
                    "name": "状态错误",
                    "content": {"title": "测试标题", "coverImage": "test.jpg", "state": "Draft", "auditState": "Pass"},
                    "expected": False
                },
                {
                    "name": "审核错误",
                    "content": {"title": "测试标题", "coverImage": "test.jpg", "state": "OnShelf", "auditState": "Pending"},
                    "expected": False
                }
            ]
            
            print("🧪 边界情况测试:")
            for test_case in test_cases:
                result = db_service._is_valid_content_for_recommendation(test_case["content"])
                status = "✅" if result == test_case["expected"] else "❌"
                print(f"   {status} {test_case['name']}: 期望{test_case['expected']}, 实际{result}")
            
        else:
            print(f"❌ 没有获取到搜狐内容")
        
        print("\n🎯 测试总结")
        print("-" * 50)
        if sohu_contents:
            valid_count = len([c for c in sohu_contents if db_service._is_valid_content_for_recommendation(c)])
            print(f"✅ 成功获取搜狐内容: {len(sohu_contents)} 条")
            print(f"✅ 筛选出有效内容: {valid_count} 条")
            print(f"✅ 筛选逻辑: 已优化")
            print(f"✅ 可用于MBTI评分: {valid_count} 条")
        else:
            print("❌ 搜狐内容获取失败")
        
        print("\n✨ 内容筛选逻辑测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_content_filtering_updated()) 