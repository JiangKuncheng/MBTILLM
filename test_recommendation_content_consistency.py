#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试推荐接口和搜狐接口的返回内容一致性
确保推荐接口返回的内容与搜狐接口一致
"""

import asyncio
import requests
import json
from datetime import datetime
from sohu_client import sohu_client

# API基础URL
BASE_URL = "http://localhost:8000"

async def test_sohu_api_content():
    """测试搜狐API返回的内容结构"""
    print("🧪 测试搜狐API返回的内容结构")
    print("=" * 80)
    
    try:
        print("📋 步骤1: 获取搜狐文章列表")
        print("-" * 50)
        
        async with sohu_client as client:
            # 获取文章列表
            result = await client.get_article_list(
                page_num=1,
                page_size=3,  # 只取3条用于分析
                state="OnShelf",
                site_id=11
            )
            
            if result.get("code") == 200:
                print("✅ 搜狐API调用成功")
                
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
                
                print(f"返回文章数量: {len(articles)}")
                
                if articles:
                    print("\n📊 搜狐API返回的文章结构:")
                    first_article = articles[0]
                    for key, value in first_article.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"  {key}: {value[:100]}...")
                        else:
                            print(f"  {key}: {value}")
                    
                    # 保存搜狐API的返回结构
                    with open("sohu_api_structure.json", "w", encoding="utf-8") as f:
                        json.dump(first_article, f, indent=2, ensure_ascii=False)
                    print("\n📁 搜狐API结构已保存到 sohu_api_structure.json")
                    
                    return first_article
                else:
                    print("❌ 搜狐API返回的文章列表为空")
                    return None
            else:
                print(f"❌ 搜狐API调用失败: {result.get('msg', '未知错误')}")
                return None
                
    except Exception as e:
        print(f"❌ 测试搜狐API时出现异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_your_recommendation_api():
    """测试你的推荐接口返回的内容"""
    print("\n🧪 测试你的推荐接口返回的内容")
    print("=" * 80)
    
    try:
        print("📋 步骤2: 测试用户推荐接口")
        print("-" * 50)
        
        # 测试用户推荐接口
        response = requests.get(
            f"{BASE_URL}/api/v1/recommendations/1",
            params={
                "page": 1,
                "limit": 3,
                "include_content_details": True,
                "auto_page": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 你的推荐接口调用成功")
            
            recommendations = result['data'].get('recommendations', [])
            print(f"返回推荐数量: {len(recommendations)}")
            
            if recommendations:
                print("\n📊 你的推荐接口返回的结构:")
                first_rec = recommendations[0]
                for key, value in first_rec.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"  {key}: {value[:100]}...")
                    else:
                        print(f"  {key}: {value}")
                
                # 检查是否包含搜狐内容详情
                content = first_rec.get('content')
                if content:
                    print("\n📊 搜狐内容详情结构:")
                    for key, value in content.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"  content.{key}: {value[:100]}...")
                        else:
                            print(f"  content.{key}: {value}")
                    
                    # 保存你的接口返回结构
                    with open("your_api_structure.json", "w", encoding="utf-8") as f:
                        json.dump(first_rec, f, indent=2, ensure_ascii=False)
                    print("\n📁 你的接口结构已保存到 your_api_structure.json")
                    
                    return first_rec
                else:
                    print("\n❌ 推荐结果中没有搜狐内容详情")
                    return first_rec
            else:
                print("❌ 你的推荐接口返回的推荐列表为空")
                return None
        else:
            print(f"❌ 你的推荐接口调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 测试你的推荐接口时出现异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_sohu_batch_content_api():
    """测试搜狐批量内容接口"""
    print("\n🧪 测试搜狐批量内容接口")
    print("=" * 80)
    
    try:
        print("📋 步骤3: 测试搜狐批量内容接口")
        print("-" * 50)
        
        # 使用一些测试内容ID
        test_content_ids = [1, 2, 3]  # 假设的内容ID
        
        async def test_batch():
            async with sohu_client as client:
                result = await client.get_contents_batch(test_content_ids)
                return result
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_batch())
        loop.close()
        
        if result.get("code") == 200:
            print("✅ 搜狐批量内容接口调用成功")
            
            data = result.get("data", {})
            contents = data.get("contents", [])
            
            print(f"返回内容数量: {len(contents)}")
            
            if contents:
                print("\n📊 搜狐批量内容接口返回的结构:")
                first_content = contents[0]
                for key, value in first_content.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"  {key}: {value[:100]}...")
                    else:
                        print(f"  {key}: {value}")
                
                # 保存搜狐批量内容接口的返回结构
                with open("sohu_batch_structure.json", "w", encoding="utf-8") as f:
                    json.dump(first_content, f, indent=2, ensure_ascii=False)
                print("\n📁 搜狐批量内容结构已保存到 sohu_batch_structure.json")
                
                return first_content
            else:
                print("❌ 搜狐批量内容接口返回的内容列表为空")
                return None
        else:
            print(f"❌ 搜狐批量内容接口调用失败: {result.get('msg', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ 测试搜狐批量内容接口时出现异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_content_structures(sohu_article, your_rec, sohu_batch_content):
    """比较内容结构的一致性"""
    print("\n🧪 比较内容结构的一致性")
    print("=" * 80)
    
    try:
        print("📋 步骤4: 内容结构对比分析")
        print("-" * 50)
        
        # 分析搜狐文章列表接口的字段
        if sohu_article:
            print("📊 搜狐文章列表接口字段:")
            sohu_fields = set(sohu_article.keys())
            for field in sorted(sohu_fields):
                print(f"  ✅ {field}")
        
        # 分析搜狐批量内容接口的字段
        if sohu_batch_content:
            print("\n📊 搜狐批量内容接口字段:")
            batch_fields = set(sohu_batch_content.keys())
            for field in sorted(batch_fields):
                print(f"  ✅ {field}")
        
        # 分析你的推荐接口字段
        if your_rec:
            print("\n📊 你的推荐接口字段:")
            your_fields = set(your_rec.keys())
            for field in sorted(your_fields):
                print(f"  ✅ {field}")
            
            # 检查搜狐内容详情
            content = your_rec.get('content')
            if content:
                print("\n📊 你的接口中的搜狐内容详情字段:")
                content_fields = set(content.keys())
                for field in sorted(content_fields):
                    print(f"  ✅ content.{field}")
        
        # 对比分析
        print("\n📋 结构一致性分析:")
        print("-" * 50)
        
        if sohu_article and sohu_batch_content:
            # 找出两个搜狐接口的共同字段
            common_fields = sohu_fields.intersection(batch_fields)
            print(f"搜狐两个接口的共同字段: {len(common_fields)} 个")
            for field in sorted(common_fields):
                print(f"  🔗 {field}")
            
            # 找出差异字段
            article_only = sohu_fields - batch_fields
            batch_only = batch_fields - sohu_fields
            
            if article_only:
                print(f"\n只在文章列表接口中出现的字段: {len(article_only)} 个")
                for field in sorted(article_only):
                    print(f"  📝 {field}")
            
            if batch_only:
                print(f"\n只在批量内容接口中出现的字段: {len(batch_only)} 个")
                for field in sorted(batch_only):
                    print(f"  📦 {field}")
        
        if your_rec and sohu_batch_content:
            content = your_rec.get('content')
            if content:
                # 对比你的接口和搜狐批量内容接口
                your_content_fields = set(content.keys())
                missing_fields = batch_fields - your_content_fields
                extra_fields = your_content_fields - batch_fields
                
                if missing_fields:
                    print(f"\n❌ 你的接口缺少的搜狐字段: {len(missing_fields)} 个")
                    for field in sorted(missing_fields):
                        print(f"  ❌ {field}")
                
                if extra_fields:
                    print(f"\n⚠️  你的接口多余的字段: {len(extra_fields)} 个")
                    for field in sorted(extra_fields):
                        print(f"  ⚠️  {field}")
                
                if not missing_fields and not extra_fields:
                    print("\n✅ 你的接口与搜狐接口字段完全一致！")
                elif not missing_fields:
                    print("\n✅ 你的接口包含了所有搜狐字段")
                else:
                    print("\n❌ 你的接口缺少部分搜狐字段，需要补充")
        
        print("\n🎉 内容结构对比分析完成！")
        
    except Exception as e:
        print(f"❌ 对比分析时出现异常: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("🚀 推荐接口与搜狐接口内容一致性测试")
    print("=" * 80)
    
    # 测试搜狐API
    sohu_article = await test_sohu_api_content()
    
    # 测试你的推荐接口
    your_rec = test_your_recommendation_api()
    
    # 测试搜狐批量内容接口
    sohu_batch_content = test_sohu_batch_content_api()
    
    # 对比分析
    compare_content_structures(sohu_article, your_rec, sohu_batch_content)
    
    print("\n📁 生成的分析文件:")
    print("  - sohu_api_structure.json: 搜狐文章列表接口结构")
    print("  - your_api_structure.json: 你的推荐接口结构")
    print("  - sohu_batch_structure.json: 搜狐批量内容接口结构")
    
    print("\n💡 建议:")
    print("  1. 检查生成的文件，了解各接口的字段差异")
    print("  2. 确保你的推荐接口返回所有必要的搜狐字段")
    print("  3. 保持字段命名和数据类型的一致性")

if __name__ == "__main__":
    asyncio.run(main()) 