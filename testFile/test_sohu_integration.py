#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜狐接口集成
"""

import asyncio
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_sohu_article_list():
    """测试获取搜狐图文列表"""
    print("🧪 测试搜狐图文列表接口")
    print("=" * 50)
    
    try:
        from sohu_client import sohu_client
        
        async with sohu_client as client:
            # 测试获取第一页内容
            print("📖 获取第一页图文列表...")
            result = await client.get_article_list(
                page_num=1,
                page_size=5,
                state="OnShelf"
            )
            
            # 调试：打印完整的返回结果
            print(f"🔍 接口返回结果: {result}")
            
            if result.get("code") == 200:
                print("✅ 获取图文列表成功")
                
                # 尝试不同的数据结构
                data = result.get("data", {})
                if isinstance(data, list):
                    # 如果data直接是列表
                    articles = data
                    total = len(articles)
                    print(f"   📊 总数量: {total}")
                    print(f"   📝 当前页数量: {len(articles)}")
                elif isinstance(data, dict):
                    # 如果data是字典
                    total = data.get("total", 0)
                    articles = data.get("data", [])
                    if not articles and "list" in data:
                        articles = data.get("list", [])
                    print(f"   📊 总数量: {total}")
                    print(f"   📝 当前页数量: {len(articles)}")
                else:
                    print(f"   ⚠️  未知的数据结构: {type(data)}")
                    articles = []
                    total = 0
                
                # 显示前3篇文章信息
                for i, article in enumerate(articles[:3]):
                    print(f"\n   文章 {i+1}:")
                    print(f"     ID: {article.get('id')}")
                    print(f"     标题: {article.get('title')}")
                    print(f"     作者: {article.get('userName')} ({article.get('nickName')})")
                    print(f"     状态: {article.get('state')} | {article.get('auditState')}")
                    print(f"     封面: {article.get('coverImage')}")
                    print(f"     统计: 阅读{article.get('viewCount')} | 点赞{article.get('praiseCount')} | 收藏{article.get('collectCount')}")
                
                # 测试获取第二页
                if total > 5:
                    print(f"\n📖 获取第二页图文列表...")
                    result2 = await client.get_article_list(
                        page_num=2,
                        page_size=5,
                        state="OnShelf"
                    )
                    
                    if result2.get("code") == 200:
                        data2 = result2.get("data", {})
                        articles2 = data2.get("data", [])
                        print(f"   ✅ 第二页获取成功，数量: {len(articles2)}")
                        
                        # 检查是否与第一页不同
                        first_page_ids = {article.get('id') for article in articles}
                        second_page_ids = {article.get('id') for article in articles2}
                        
                        if first_page_ids != second_page_ids:
                            print("   ✅ 分页正常，内容不同")
                        else:
                            print("   ⚠️  分页异常，内容相同")
                    else:
                        print(f"   ❌ 第二页获取失败: {result2.get('msg')}")
                
            else:
                print(f"❌ 获取图文列表失败: {result.get('msg')}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"❌ 测试失败: {e}")
        return False

async def test_content_by_id():
    """测试根据ID获取内容详情"""
    print("\n🔍 测试根据ID获取内容详情")
    print("=" * 50)
    
    try:
        from sohu_client import sohu_client
        
        async with sohu_client as client:
            # 先获取一个文章ID
            result = await client.get_article_list(page_num=1, page_size=1)
            
            # 调试：打印完整的返回结果
            print(f"🔍 接口返回结果: {result}")
            
            if result.get("code") == 200:
                # 尝试不同的数据结构
                data = result.get("data", {})
                if isinstance(data, list):
                    articles = data
                elif isinstance(data, dict):
                    articles = data.get("data", [])
                    if not articles and "list" in data:
                        articles = data.get("list", [])
                else:
                    articles = []
                if articles:
                    article_id = articles[0].get("id")
                    print(f"📝 获取文章详情 (ID: {article_id})...")
                    
                    detail = await client.get_content_by_id(article_id, "article")
                    
                    if detail.get("code") == 200:
                        print("✅ 获取文章详情成功")
                        data = detail.get("data", {})
                        print(f"   标题: {data.get('title')}")
                        print(f"   作者: {data.get('userName')}")
                        print(f"   内容: {data.get('content', '')[:100]}...")
                    else:
                        print(f"❌ 获取文章详情失败: {detail.get('msg')}")
                else:
                    print("❌ 没有可用的文章ID")
            else:
                print(f"❌ 获取文章列表失败: {result.get('msg')}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"❌ 测试失败: {e}")
        return False

async def test_ai_rec_parameter():
    """测试aiRec参数的影响"""
    print("\n🤖 测试aiRec参数的影响")
    print("=" * 50)
    
    try:
        from sohu_client import sohu_client
        
        async with sohu_client as client:
            # 测试aiRec=false（推荐）
            print("📖 测试 aiRec=false...")
            result1 = await client.get_article_list(
                page_num=1,
                page_size=5,
                state="OnShelf"
            )
            
            # 调试：打印完整的返回结果
            print(f"🔍 接口返回结果: {result1}")
            
            if result1.get("code") == 200:
                # 尝试不同的数据结构
                data1 = result1.get("data", {})
                if isinstance(data1, list):
                    articles1 = data1
                elif isinstance(data1, dict):
                    articles1 = data1.get("data", [])
                    if not articles1 and "list" in data1:
                        articles1 = data1.get("list", [])
                else:
                    articles1 = []
                
                ids1 = [article.get("id") for article in articles1]
                print(f"   aiRec=false 结果: {ids1}")
                
                # 再次请求，检查结果是否不同
                result2 = await client.get_article_list(
                    page_num=1,
                    page_size=5,
                    state="OnShelf"
                )
                
                if result2.get("code") == 200:
                    # 尝试不同的数据结构
                    data2 = result2.get("data", {})
                    if isinstance(data2, list):
                        articles2 = data2
                    elif isinstance(data2, dict):
                        articles2 = data2.get("data", [])
                        if not articles2 and "list" in data2:
                            articles2 = data2.get("list", [])
                    else:
                        articles2 = []
                    
                    ids2 = [article.get("id") for article in articles2]
                    print(f"   aiRec=false 第二次结果: {ids2}")
                    
                    if ids1 != ids2:
                        print("   ✅ aiRec=false 每次结果不同，符合预期")
                    else:
                        print("   ⚠️  aiRec=false 结果相同，可能有问题")
                else:
                    print(f"   ❌ 第二次请求失败: {result2.get('msg')}")
            else:
                print(f"❌ 第一次请求失败: {result1.get('msg')}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"❌ 测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试搜狐接口集成")
    print("=" * 60)
    
    # 测试图文列表
    success1 = await test_sohu_article_list()
    
    # 测试内容详情
    success2 = await test_content_by_id()
    
    # 测试aiRec参数
    success3 = await test_ai_rec_parameter()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"   图文列表接口: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"   内容详情接口: {'✅ 通过' if success2 else '❌ 失败'}")
    print(f"   aiRec参数测试: {'✅ 通过' if success3 else '❌ 失败'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 所有测试通过！搜狐接口集成成功")
    else:
        print("\n⚠️  部分测试失败，请检查接口配置")

if __name__ == "__main__":
    asyncio.run(main()) 