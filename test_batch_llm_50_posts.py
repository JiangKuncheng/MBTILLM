#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试大模型API批量评分50条帖子
验证真实LLM API的批量处理能力
"""

import asyncio
import json
from typing import List, Dict, Any
from mbti_service import mbti_service
from sohu_client import sohu_client

async def test_batch_llm_50_posts():
    """测试大模型API批量评分50条帖子"""
    print("🧪 测试大模型API批量评分50条帖子")
    print("=" * 80)
    
    try:
        # 步骤1: 从搜狐API获取50条内容
        print("📋 步骤1: 获取50条内容")
        print("-" * 50)
        
        async with sohu_client as client:
            result = await client.get_article_list(
                page_num=1,
                page_size=50,
                state="OnShelf"
            )
        
        if result.get("code") != 200 or "data" not in result:
            print(f"❌ 获取内容失败: {result}")
            return
        
        data = result["data"]
        if isinstance(data, list):
            articles = data
        elif isinstance(data, dict):
            articles = data.get("data", [])
            if not articles and "list" in data:
                articles = data.get("list", [])
        else:
            articles = []
        
        print(f"✅ 成功获取 {len(articles)} 条内容")
        
        # 步骤2: 获取每条内容的详细正文
        print("\n📋 步骤2: 获取内容详细正文")
        print("-" * 50)
        
        contents_for_scoring = []
        async with sohu_client as client:
            for i, article in enumerate(articles[:50], 1):
                try:
                    content_id = article.get("id")
                    title = article.get("title", "")
                    
                    print(f"   📄 获取第 {i}/50 条内容详情: ID {content_id} - {title[:30]}...")
                    
                    content_detail = await client.get_content_by_id(content_id)
                    
                    if content_detail.get("code") == 200 and "data" in content_detail:
                        data = content_detail["data"]
                        content_text = data.get("content", "") or data.get("description", "")
                        
                        if content_text and len(content_text.strip()) >= 10:
                            contents_for_scoring.append({
                                "id": content_id,
                                "title": title,
                                "content": content_text
                            })
                            print(f"      ✅ 获取成功，正文长度: {len(content_text)} 字符")
                        else:
                            print(f"      ⚠️ 正文内容不足，长度: {len(content_text)} 字符")
                    else:
                        print(f"      ❌ 获取失败: {content_detail.get('msg', '未知错误')}")
                    
                    # 避免请求过快
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    print(f"      ❌ 获取内容 {content_id} 详情失败: {e}")
        
        print(f"\n📝 准备对 {len(contents_for_scoring)} 条有内容的内容进行MBTI评分...")
        
        if not contents_for_scoring:
            print("❌ 没有足够内容进行评分")
            return
        
        # 步骤3: 调用大模型API进行批量评分
        print("\n📋 步骤3: 调用大模型API批量评分")
        print("-" * 50)
        
        print(f"🔍 开始调用大模型API评分 {len(contents_for_scoring)} 条内容...")
        
        # 调用批量评分
        scoring_result = await mbti_service.batch_evaluate_contents(contents_for_scoring)
        
        print(f"\n📊 批量评分结果:")
        print(f"   总内容数: {scoring_result['total']}")
        print(f"   成功评分: {scoring_result['successful']}")
        print(f"   缓存内容: {scoring_result['cached']}")
        print(f"   新评分: {scoring_result['new_evaluated']}")
        
        # 步骤4: 显示详细的评分结果
        print("\n📋 步骤4: 详细评分结果")
        print("-" * 50)
        
        results = scoring_result.get('results', [])
        for i, result in enumerate(results[:10], 1):  # 只显示前10条
            content_id = result.get('id', 'unknown')
            title = result.get('title', '')[:40]
            from_cache = result.get('from_cache', False)
            error = result.get('error', None)
            
            if from_cache:
                print(f"   {i:2d}. ID: {content_id} | {title}... | ✅ 来自缓存")
            elif error:
                print(f"   {i:2d}. ID: {content_id} | {title}... | ❌ 错误: {error}")
            else:
                e_i = result.get('E_I', 0.5)
                s_n = result.get('S_N', 0.5)
                t_f = result.get('T_F', 0.5)
                j_p = result.get('J_P', 0.5)
                print(f"   {i:2d}. ID: {content_id} | {title}... | ✅ 新评分: E={e_i:.3f}, S={s_n:.3f}, T={t_f:.3f}, J={j_p:.3f}")
        
        if len(results) > 10:
            print(f"   ... 还有 {len(results) - 10} 条结果")
        
        # 步骤5: 统计评分成功率
        print("\n📋 步骤5: 评分成功率分析")
        print("-" * 50)
        
        total = scoring_result['total']
        successful = scoring_result['successful']
        cached = scoring_result['cached']
        new_evaluated = scoring_result['new_evaluated']
        
        success_rate = (successful / total * 100) if total > 0 else 0
        new_rate = (new_evaluated / total * 100) if total > 0 else 0
        
        print(f"📈 总体成功率: {success_rate:.1f}% ({successful}/{total})")
        print(f"📈 新评分率: {new_rate:.1f}% ({new_evaluated}/{total})")
        print(f"📈 缓存命中率: {(cached/total*100):.1f}% ({cached}/{total})")
        
        if new_evaluated == 0:
            print("\n⚠️ 警告: 没有新评分！可能的原因:")
            print("   1. 所有内容都已有缓存评分")
            print("   2. 大模型API调用失败")
            print("   3. 响应解析失败")
            print("   4. 网络或配置问题")
        
        print("\n🎉 批量评分测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    await test_batch_llm_50_posts()

if __name__ == "__main__":
    asyncio.run(main()) 