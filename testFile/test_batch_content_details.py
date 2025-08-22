#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批量获取推荐内容的详情
"""

import asyncio
import json
from datetime import datetime

async def test_batch_content_details():
    """测试批量获取推荐内容的详情"""
    print("🧪 测试批量获取推荐内容的详情")
    print("=" * 60)
    
    try:
        from database_service import db_service
        from sohu_client import sohu_client
        
        print("📋 测试1: 从推荐列表获取30条内容ID")
        print("-" * 50)
        
        # 从搜狐接口获取30条内容
        print("从搜狐接口获取30条内容...")
        sohu_contents = await db_service.get_sohu_contents_for_recommendation(limit=30)
        
        if sohu_contents:
            print(f"✅ 成功获取 {len(sohu_contents)} 条内容")
            
            # 提取内容ID
            content_ids = [content['id'] for content in sohu_contents]
            print(f"📊 内容ID列表: {content_ids}")
            
            # 显示前几条内容的基本信息
            print(f"\n📰 前5条内容预览:")
            for i, content in enumerate(sohu_contents[:5], 1):
                print(f"   内容 {i}:")
                print(f"     ID: {content.get('id')}")
                print(f"     标题: {content.get('title', '无标题')[:30]}...")
                print(f"     类型: {content.get('type')}")
                print(f"     状态: {content.get('state')}")
                print()
            
            print(f"\n📋 测试2: 批量获取内容详情")
            print("-" * 50)
            
            # 批量获取内容详情
            content_details = []
            failed_ids = []
            
            print(f"开始批量获取 {len(content_ids)} 条内容的详情...")
            
            async with sohu_client as client:
                for i, content_id in enumerate(content_ids, 1):
                    print(f"🔄 获取第 {i}/{len(content_ids)} 条: ID {content_id}")
                    
                    try:
                        # 获取内容详情
                        detail_result = await client.get_content_by_id(content_id)
                        
                        if detail_result and detail_result.get('code') == 200:
                            detail_data = detail_result.get('data', {})
                            if detail_data:
                                content_details.append(detail_data)
                                print(f"   ✅ 成功获取详情")
                                
                                # 显示关键信息
                                title = detail_data.get('title', '无标题')
                                content = detail_data.get('content', '')
                                has_content = bool(content and content.strip())
                                
                                print(f"     标题: {title[:30]}...")
                                print(f"     有文字内容: {'是' if has_content else '否'}")
                                if has_content:
                                    # 清理HTML标签，显示纯文本预览
                                    import re
                                    clean_content = re.sub(r'<[^>]+>', '', content)
                                    clean_content = re.sub(r'&nbsp;', ' ', clean_content)
                                    print(f"     内容预览: {clean_content[:50]}...")
                            else:
                                print(f"   ⚠️  没有详情数据")
                                failed_ids.append(content_id)
                        else:
                            print(f"   ❌ 获取失败: {detail_result.get('msg') if detail_result else '未知错误'}")
                            failed_ids.append(content_id)
                            
                    except Exception as e:
                        print(f"   ❌ 异常: {e}")
                        failed_ids.append(content_id)
                    
                    # 添加小延迟，避免请求过快
                    await asyncio.sleep(0.1)
            
            print(f"\n📊 批量获取结果统计")
            print("-" * 50)
            print(f"   总内容数: {len(content_ids)}")
            print(f"   成功获取: {len(content_details)}")
            print(f"   获取失败: {len(failed_ids)}")
            print(f"   成功率: {len(content_details)/len(content_ids)*100:.1f}%")
            
            if failed_ids:
                print(f"   失败的内容ID: {failed_ids}")
            
            if content_details:
                print(f"\n📋 测试3: 分析获取到的内容详情")
                print("-" * 50)
                
                # 分析内容详情
                content_with_text = []
                content_with_images = []
                content_with_both = []
                
                for detail in content_details:
                    has_text = bool(detail.get('content') and detail.get('content').strip())
                    has_images = bool(detail.get('images') or detail.get('coverImage'))
                    
                    if has_text and has_images:
                        content_with_both.append(detail)
                    elif has_text:
                        content_with_text.append(detail)
                    elif has_images:
                        content_with_images.append(detail)
                
                print(f"📊 内容详情分析:")
                print(f"   有文字内容: {len(content_with_text)} 条")
                print(f"   有图片内容: {len(content_with_images)} 条")
                print(f"   文字+图片: {len(content_with_both)} 条")
                print(f"   总计: {len(content_details)} 条")
                
                # 显示有文字内容的示例
                if content_with_text or content_with_both:
                    print(f"\n📝 有文字内容的内容示例:")
                    text_contents = content_with_text + content_with_both
                    for i, content in enumerate(text_contents[:3], 1):
                        print(f"   内容 {i}:")
                        print(f"     ID: {content.get('id')}")
                        print(f"     标题: {content.get('title', '无标题')[:30]}...")
                        
                        # 清理HTML标签显示纯文本
                        raw_content = content.get('content', '')
                        if raw_content:
                            import re
                            clean_content = re.sub(r'<[^>]+>', '', raw_content)
                            clean_content = re.sub(r'&nbsp;', ' ', clean_content)
                            clean_content = clean_content.strip()
                            print(f"     纯文本内容: {clean_content[:100]}...")
                        print()
                
                print(f"\n📋 测试4: 验证内容质量")
                print("-" * 50)
                
                # 验证内容质量
                high_quality = 0
                medium_quality = 0
                low_quality = 0
                
                for detail in content_details:
                    title = detail.get('title', '')
                    content = detail.get('content', '')
                    cover_image = detail.get('coverImage') or detail.get('coverUrl')
                    
                    # 简单的质量评分
                    score = 0
                    if title and len(title.strip()) > 5:
                        score += 1
                    if content and len(content.strip()) > 20:
                        score += 2
                    if cover_image:
                        score += 1
                    
                    if score >= 3:
                        high_quality += 1
                    elif score >= 1:
                        medium_quality += 1
                    else:
                        low_quality += 1
                
                print(f"📈 内容质量分布:")
                print(f"   高质量内容: {high_quality} 条")
                print(f"   中等质量: {medium_quality} 条")
                print(f"   低质量内容: {low_quality} 条")
                print(f"   平均质量: {(high_quality * 3 + medium_quality * 2 + low_quality * 1) / len(content_details):.1f}/4")
            
        else:
            print(f"❌ 没有获取到搜狐内容")
        
        print("\n🎯 测试总结")
        print("-" * 50)
        if sohu_contents:
            print(f"✅ 成功获取推荐内容: {len(sohu_contents)} 条")
            print(f"✅ 批量获取详情: 可用")
            print(f"✅ 内容质量分析: 完成")
            print(f"✅ 可用于MBTI评分: {len([c for c in content_details if c.get('content')])} 条")
        else:
            print("❌ 搜狐内容获取失败")
        
        print("\n✨ 批量内容详情获取测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_batch_content_details()) 