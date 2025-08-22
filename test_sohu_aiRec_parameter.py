 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜狐API的aiRec参数
验证aiRec=false是否能解决返回帖子一直一样的问题
"""

import asyncio
import json
from datetime import datetime
from sohu_client import sohu_client

async def test_sohu_aiRec_parameter():
    """测试搜狐API的aiRec参数"""
    print("🧪 测试搜狐API的aiRec参数")
    print("=" * 80)
    
    try:
        # 测试参数组合
        test_cases = [
            {"aiRec": "false", "description": "aiRec=false (字符串)"},
            {"aiRec": False, "description": "aiRec=False (布尔值)"},
            {"aiRec": "true", "description": "aiRec=true (字符串)"},
            {"aiRec": True, "description": "aiRec=True (布尔值)"},
            {"aiRec": None, "description": "aiRec=None (不传参数)"},
        ]
        
        # 存储每次请求的结果
        all_results = {}
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}: {test_case['description']}")
            print("-" * 60)
            
            aiRec_value = test_case["aiRec"]
            description = test_case["description"]
            
            # 进行多次请求，检查是否返回相同内容
            request_results = []
            
            for request_num in range(1, 6):  # 连续请求5次
                try:
                    print(f"   🔄 第 {request_num} 次请求...")
                    
                    async with sohu_client as client:
                        # 构建请求参数
                        params = {
                            "page_num": 1,
                            "page_size": 10,
                            "state": "OnShelf",
                            "site_id": 11
                        }
                        
                        # 添加aiRec参数
                        if aiRec_value is not None:
                            params["aiRec"] = aiRec_value
                        
                        print(f"      请求参数: {params}")
                        
                        # 发送请求
                        start_time = datetime.now()
                        result = await client.get_article_list(**params)
                        end_time = datetime.now()
                        
                        request_duration = (end_time - start_time).total_seconds()
                        
                        if result.get("code") == 200:
                            data = result.get("data", {})
                            
                            # 处理不同的数据结构
                            if isinstance(data, list):
                                articles = data
                            elif isinstance(data, dict):
                                articles = data.get("data", [])
                                if not articles and "list" in data:
                                    articles = data.get("list", [])
                            else:
                                articles = []
                            
                            # 提取关键信息
                            article_info = []
                            for article in articles[:5]:  # 只取前5条
                                article_info.append({
                                    "id": article.get("id"),
                                    "title": article.get("title", "")[:30],
                                    "type": article.get("type", ""),
                                    "created_at": article.get("created_at", ""),
                                    "updated_at": article.get("updated_at", "")
                                })
                            
                            request_results.append({
                                "request_num": request_num,
                                "duration": request_duration,
                                "article_count": len(articles),
                                "articles": article_info,
                                "success": True
                            })
                            
                            print(f"      ✅ 请求成功，耗时: {request_duration:.2f}s")
                            print(f"      返回文章数: {len(articles)}")
                            print(f"      前5篇文章:")
                            for j, article in enumerate(article_info, 1):
                                print(f"        {j}. ID: {article['id']} | {article['title']}...")
                            
                        else:
                            request_results.append({
                                "request_num": request_num,
                                "duration": request_duration,
                                "error": result.get("msg", "未知错误"),
                                "success": False
                            })
                            
                            print(f"      ❌ 请求失败: {result.get('msg', '未知错误')}")
                    
                    # 请求间隔
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"      ❌ 请求异常: {e}")
                    request_results.append({
                        "request_num": request_num,
                        "duration": 0,
                        "error": str(e),
                        "success": False
                    })
            
            # 分析这个测试用例的结果
            all_results[description] = request_results
            
            # 检查是否有重复内容
            await analyze_test_case_results(description, request_results)
        
        # 综合分析所有测试用例
        print("\n📋 综合分析结果")
        print("=" * 80)
        await analyze_all_results(all_results)
        
        print("\n🎉 aiRec参数测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

async def analyze_test_case_results(description: str, request_results: list):
    """分析单个测试用例的结果"""
    print(f"\n   📊 分析结果: {description}")
    
    if not request_results:
        print("      ⚠️ 没有有效的请求结果")
        return
    
    # 检查成功率
    successful_requests = [r for r in request_results if r.get("success")]
    success_rate = len(successful_requests) / len(request_results) * 100
    print(f"      请求成功率: {success_rate:.1f}% ({len(successful_requests)}/{len(request_results)})")
    
    if len(successful_requests) < 2:
        print("      ⚠️ 成功请求不足，无法分析重复性")
        return
    
    # 分析文章重复性
    all_article_ids = []
    all_article_titles = []
    
    for result in successful_requests:
        articles = result.get("articles", [])
        for article in articles:
            article_id = article.get("id")
            article_title = article.get("title", "")
            if article_id:
                all_article_ids.append(article_id)
            if article_title:
                all_article_titles.append(article_title)
    
    # 检查ID重复
    unique_ids = set(all_article_ids)
    id_duplication_rate = (1 - len(unique_ids) / len(all_article_ids)) * 100 if all_article_ids else 0
    
    # 检查标题重复
    unique_titles = set(all_article_titles)
    title_duplication_rate = (1 - len(unique_titles) / len(all_article_titles)) * 100 if all_article_titles else 0
    
    print(f"      文章ID重复率: {id_duplication_rate:.1f}%")
    print(f"      文章标题重复率: {title_duplication_rate:.1f}%")
    
    if id_duplication_rate > 50:
        print("      ⚠️ 文章ID重复率很高，可能存在缓存问题")
    elif id_duplication_rate > 20:
        print("      ⚠️ 文章ID重复率较高，建议检查参数")
    else:
        print("      ✅ 文章ID重复率较低，参数设置合理")
    
    # 显示重复的文章
    if id_duplication_rate > 0:
        from collections import Counter
        id_counts = Counter(all_article_ids)
        repeated_ids = [aid for aid, count in id_counts.items() if count > 1]
        print(f"      重复的文章ID: {repeated_ids[:5]}...")  # 只显示前5个

async def analyze_all_results(all_results: dict):
    """综合分析所有测试用例的结果"""
    print("📊 各测试用例对比分析:")
    
    # 计算每个测试用例的重复率
    test_case_analysis = {}
    
    for description, results in all_results.items():
        successful_requests = [r for r in results if r.get("success")]
        if len(successful_requests) >= 2:
            # 计算重复率
            all_article_ids = []
            for result in successful_requests:
                articles = result.get("articles", [])
                for article in articles:
                    article_id = article.get("id")
                    if article_id:
                        all_article_ids.append(article_id)
            
            unique_ids = set(all_article_ids)
            duplication_rate = (1 - len(unique_ids) / len(all_article_ids)) * 100 if all_article_ids else 0
            
            test_case_analysis[description] = {
                "duplication_rate": duplication_rate,
                "success_rate": len(successful_requests) / len(results) * 100,
                "total_articles": len(all_article_ids)
            }
    
    # 按重复率排序
    sorted_cases = sorted(test_case_analysis.items(), key=lambda x: x[1]["duplication_rate"])
    
    print("\n   排名 (按重复率从低到高):")
    for i, (description, analysis) in enumerate(sorted_cases, 1):
        print(f"   {i}. {description}")
        print(f"      重复率: {analysis['duplication_rate']:.1f}%")
        print(f"      成功率: {analysis['success_rate']:.1f}%")
        print(f"      总文章数: {analysis['total_articles']}")
        print()
    
    # 推荐最佳参数
    if sorted_cases:
        best_case = sorted_cases[0]
        print(f"🏆 推荐参数: {best_case[0]}")
        print(f"   重复率最低: {best_case[1]['duplication_rate']:.1f}%")
        print(f"   成功率: {best_case[1]['success_rate']:.1f}%")

async def main():
    """主函数"""
    await test_sohu_aiRec_parameter()

if __name__ == "__main__":
    asyncio.run(main())