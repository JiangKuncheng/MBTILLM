#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同的aiRec参数值，找到能让内容多样化的方法
"""

import asyncio
import json
from datetime import datetime
from collections import Counter

async def test_ai_rec_solutions():
    """测试不同的aiRec参数值"""
    print("🔧 测试aiRec参数解决方案")
    print("=" * 60)
    
    try:
        from sohu_client import sohu_client
        
        # 测试不同的aiRec值
        test_values = [
            ("false", "字符串false"),
            (False, "布尔False"),
            ("0", "字符串0"),
            (0, "数字0"),
            ("off", "字符串off"),
            ("no", "字符串no"),
            ("", "空字符串"),
            (None, "None值"),
            ("random", "字符串random"),
            ("diverse", "字符串diverse")
        ]
        
        print("📋 测试不同的aiRec参数值")
        print("-" * 50)
        
        best_solution = None
        best_diversity = 0
        
        for ai_rec_value, description in test_values:
            print(f"\n🧪 测试: {description} = {ai_rec_value}")
            
            # 连续获取3次，检查内容是否不同
            fetch_results = []
            
            for fetch_round in range(1, 4):
                async with sohu_client as client:
                    # 构建自定义参数
                    custom_params = {
                        "pageNum": 1,
                        "pageSize": 10,
                        "state": "OnShelf",
                        "siteId": 11
                    }
                    
                    # 添加aiRec参数
                    if ai_rec_value is not None:
                        custom_params["aiRec"] = ai_rec_value
                    
                    # 直接调用搜狐接口
                    result = await client.get_article_list(
                        page_num=1,
                        page_size=10,
                        state="OnShelf",
                        site_id=11
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
                        
                        if articles:
                            content_ids = [article.get('id') for article in articles]
                            fetch_results.append(content_ids)
                            
                            if fetch_round == 1:  # 只显示第一次的结果
                                print(f"   第{fetch_round}次: {len(articles)}条, ID: {content_ids[:5]}...")
                        else:
                            print(f"   第{fetch_round}次: 无内容")
                    else:
                        print(f"   第{fetch_round}次: 获取失败")
            
            # 分析多样性
            if len(fetch_results) >= 2:
                all_ids = []
                for fetch_ids in fetch_results:
                    all_ids.extend(fetch_ids)
                
                unique_ids = set(all_ids)
                diversity_ratio = len(unique_ids) / len(all_ids) * 100
                
                print(f"   📊 多样性: {diversity_ratio:.1f}%")
                print(f"   📈 唯一内容: {len(unique_ids)}/{len(all_ids)}")
                
                # 记录最佳解决方案
                if diversity_ratio > best_diversity:
                    best_diversity = diversity_ratio
                    best_solution = (ai_rec_value, description)
                
                if diversity_ratio > 80:
                    print(f"   🎉 这个值效果很好！")
                elif diversity_ratio > 50:
                    print(f"   👍 这个值有一定效果")
                else:
                    print(f"   ⚠️  这个值效果不佳")
            else:
                print(f"   ❌ 无法测试多样性")
        
        print("\n📋 测试结果总结")
        print("-" * 50)
        
        if best_solution:
            ai_rec_value, description = best_solution
            print(f"🏆 最佳解决方案: {description} = {ai_rec_value}")
            print(f"📈 最佳多样性: {best_diversity:.1f}%")
            
            if best_diversity > 80:
                print("🎉 找到了有效的aiRec参数值！")
            elif best_diversity > 50:
                print("👍 找到了部分有效的aiRec参数值")
            else:
                print("⚠️  所有aiRec参数值效果都不理想")
        else:
            print("❌ 没有找到有效的解决方案")
        
        print("\n🔍 其他可能的解决方案")
        print("-" * 50)
        print("1. 尝试不同的pageNum值")
        print("2. 添加时间戳参数")
        print("3. 添加随机种子参数")
        print("4. 检查接口文档中的其他参数")
        
        # 测试pageNum的影响
        print("\n📋 测试pageNum对内容多样性的影响")
        print("-" * 50)
        
        page_diversity_results = []
        for page_num in range(1, 6):
            async with sohu_client as client:
                result = await client.get_article_list(
                    page_num=page_num,
                    page_size=10,
                    state="OnShelf",
                    site_id=11
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
                    
                    if articles:
                        content_ids = [article.get('id') for article in articles]
                        page_diversity_results.append((page_num, content_ids))
                        print(f"   第{page_num}页: {len(articles)}条, ID: {content_ids[:5]}...")
        
        # 分析不同页面的内容重叠
        if len(page_diversity_results) > 1:
            all_page_ids = []
            for page_num, content_ids in page_diversity_results:
                all_page_ids.extend(content_ids)
            
            unique_page_ids = set(all_page_ids)
            page_diversity = len(unique_page_ids) / len(all_page_ids) * 100
            
            print(f"\n📊 跨页面多样性: {page_diversity:.1f}%")
            print(f"📈 总唯一内容: {len(unique_page_ids)}/{len(all_page_ids)}")
            
            if page_diversity > 80:
                print("🎉 不同页面的内容差异很大，可以通过翻页获取多样化内容！")
            else:
                print("⚠️  不同页面的内容重叠较多")
        
        print("\n✨ aiRec参数测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_rec_solutions()) 