#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM原始返回内容
"""

import asyncio
import json
from mbti_service import mbti_service

async def test_raw_llm_response():
    """测试LLM的原始返回内容"""
    print("🧪 测试LLM原始返回内容")
    print("=" * 60)
    
    # 测试内容
    test_content = "这是一个测试内容，关于团队协作和创新的讨论。"
    
    print(f"📝 测试内容: {test_content}")
    print("-" * 60)
    
    try:
        # 直接调用LLM，不做任何处理
        print("🚀 调用LLM...")
        response = await mbti_service._call_llm_api(test_content)
        
        print("🔍 LLM原始响应:")
        print(f"类型: {type(response)}")
        print(f"内容: {response}")
        print("-" * 60)
        
        if response and response.get('choices'):
            content_text = response['choices'][0].get('message', {}).get('content', '')
            print("📄 提取的文本内容:")
            print(f"类型: {type(content_text)}")
            print(f"长度: {len(content_text)}")
            print(f"内容: {repr(content_text)}")
            print("-" * 60)
            
            # 尝试直接解析JSON
            try:
                parsed = json.loads(content_text)
                print("✅ JSON解析成功:")
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print("原始内容:")
                print(content_text)
        else:
            print("❌ LLM响应格式异常")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_raw_llm_response()) 