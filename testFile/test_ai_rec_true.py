#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试aiRec=true是否能让每次获取的内容不同
"""

import asyncio
import json
from datetime import datetime
from collections import Counter

async def test_ai_rec_true():
    """测试aiRec=true的效果"""
    print("🧪 测试aiRec=true的内容多样性")
    print("=" * 60)
    
    try:
        from sohu_client import sohu_client
        
        print("📋 测试1: 连续多次获取内容，检查aiRec=true是否有效")
        print("-" * 50)
        
        # 连续获取5次，每次10条内容
        all_fetches = []
        content_ids_per_fetch = []
        
        for fetch_round in range(1, 6):
            print(f"\n🔄 第{fetch_round}次获取 (aiRec=true):")
            
            async with sohu_client as client:
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
                        # 提取内容ID和标题
                        content_info = []
                        for article in articles:
                            content_info.append({
                                'id': article.get('id'),
                                'title': article.get('title', '无标题')[:30],
                                'type': article.get('type'),
                                'state': article.get('state'),
                                'auditState': article.get('auditState')
                            })
                        
                        all_fetches.append(content_info)
                        content_ids = [article.get('id') for article in articles]
                        content_ids_per_fetch.append(content_ids)
                        
                        print(f"   ✅ 成功获取 {len(articles)} 条内容")
                        print(f"   📊 内容ID: {content_ids}")
                        print(f"   📝 前3条标题:")
                        for i, info in enumerate(content_info[:3], 1):
                            print(f"      {i}. ID:{info['id']} - {info['title']}...")
                    else:
                        print(f"   ❌ 没有获取到内容")
                else:
                    print(f"   ❌ 获取失败: {result.get('msg')}")
        
        print("\n📋 测试2: 分析内容重复情况")
        print("-" * 50)
        
        if all_fetches:
            # 统计所有内容ID
            all_content_ids = []
            for fetch_ids in content_ids_per_fetch:
                all_content_ids.extend(fetch_ids)
            
            # 统计每个ID出现的次数
            id_counter = Counter(all_content_ids)
            
            print(f"📊 统计信息:")
            print(f"   总获取次数: {len(all_fetches)}")
            print(f"   总内容条数: {len(all_content_ids)}")
            print(f"   唯一内容数: {len(id_counter)}")
            print(f"   重复内容数: {len(all_content_ids) - len(id_counter)}")
            
            # 显示重复的内容
            repeated_ids = [id for id, count in id_counter.items() if count > 1]
            if repeated_ids:
                print(f"\n🔄 重复出现的内容ID:")
                for content_id in repeated_ids:
                    count = id_counter[content_id]
                    print(f"   ID {content_id}: 出现 {count} 次")
                    
                    # 显示这个内容在不同获取中的信息
                    for i, fetch in enumerate(all_fetches):
                        for content in fetch:
                            if content['id'] == content_id:
                                print(f"     第{i+1}次: {content['title']}...")
            else:
                print(f"\n✅ 没有重复内容！aiRec=true工作正常")
            
            # 计算多样性指标
            diversity_ratio = len(id_counter) / len(all_content_ids) * 100
            print(f"\n📈 内容多样性: {diversity_ratio:.1f}%")
            
            if diversity_ratio > 80:
                print("   🎉 内容多样性很高！aiRec=true工作正常")
            elif diversity_ratio > 50:
                print("   👍 内容多样性中等，aiRec=true部分有效")
            else:
                print("   ⚠️  内容多样性较低，aiRec=true可能无效")
        
        print("\n📋 测试3: 对比aiRec=false和aiRec=true")
        print("-" * 50)
        
        # 临时测试aiRec=false的效果
        print("🔍 临时测试aiRec=false (对比用):")
        
        false_fetch_results = []
        for fetch_round in range(1, 4):
            async with sohu_client as client:
                # 临时修改参数
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
                        false_fetch_results.append(content_ids)
                        
                        if fetch_round == 1:
                            print(f"   第{fetch_round}次: {len(articles)}条, ID: {content_ids[:5]}...")
        
        # 分析false的结果
        if false_fetch_results:
            all_false_ids = []
            for fetch_ids in false_fetch_results:
                all_false_ids.extend(fetch_ids)
            
            unique_false_ids = set(all_false_ids)
            false_diversity = len(unique_false_ids) / len(all_false_ids) * 100
            
            print(f"   📊 aiRec=false多样性: {false_diversity:.1f}%")
        
        print("\n🎯 测试总结")
        print("-" * 50)
        if all_fetches:
            unique_ratio = len(set(all_content_ids)) / len(all_content_ids) * 100
            print(f"✅ aiRec=true内容唯一性: {unique_ratio:.1f}%")
            print(f"✅ 总获取次数: {len(all_fetches)}")
            print(f"✅ 总内容条数: {len(all_content_ids)}")
            
            if unique_ratio > 80:
                print("🎉 aiRec=true工作正常，每次获取内容都不同！")
            elif unique_ratio > 50:
                print("👍 aiRec=true有一定效果，内容多样性提升")
            else:
                print("⚠️  aiRec=true效果不明显，可能需要其他方案")
        else:
            print("❌ 没有获取到任何内容，需要检查接口连接")
        
        print("\n✨ aiRec=true测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_rec_true()) 