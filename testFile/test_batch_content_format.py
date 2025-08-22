#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发送给大模型的批量内容格式
"""

import asyncio
from mbti_service import mbti_service

async def test_batch_content_format():
    """测试发送给大模型的批量内容格式"""
    print("🧪 测试批量内容格式")
    print("=" * 60)
    
    # 模拟测试数据
    test_contents = [
        {
            'id': 1001,
            'title': '团队协作的力量',
            'content': '我真心喜欢和团队一起工作！今天我们小组讨论了新项目，每个人都积极发言，分享自己的想法。'
        },
        {
            'id': 1002,
            'title': '独处思考的价值',
            'content': '我发现最好的想法往往在独处时产生。今天下午一个人在咖啡厅里静静思考，突然对复杂的技术问题有了新的理解。'
        },
        {
            'id': 1003,
            'title': '数据驱动的决策',
            'content': '在做重要决策时，我坚持用数据说话。通过收集相关指标、分析历史趋势、建立预测模型，我们能够做出更加理性和准确的判断。'
        }
    ]
    
    print(f"📝 测试内容数量: {len(test_contents)}")
    print("-" * 60)
    
    # 构建批量内容格式
    batch_content = mbti_service._build_batch_content_for_llm(test_contents)
    
    print("📤 发送给大模型的批量内容格式:")
    print("-" * 60)
    print(batch_content)
    print("-" * 60)
    
    print("📊 内容分析:")
    print(f"总长度: {len(batch_content)} 字符")
    print(f"包含内容ID: {'内容ID:' in batch_content}")
    print(f"包含标题: {'标题:' in batch_content}")
    print(f"包含内容: {'内容:' in batch_content}")
    
    # 检查是否包含所有ID
    for content in test_contents:
        if str(content['id']) in batch_content:
            print(f"✅ 包含ID {content['id']}")
        else:
            print(f"❌ 缺少ID {content['id']}")

if __name__ == "__main__":
    asyncio.run(test_batch_content_format()) 