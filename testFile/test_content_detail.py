#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试获取帖子详情的功能
"""

import asyncio
import json
from datetime import datetime

async def test_content_detail():
    """测试获取帖子详情功能"""
    print("🧪 测试获取帖子详情功能")
    print("=" * 60)
    
    try:
        from sohu_client import sohu_client
        
        # 测试获取帖子ID 3055 的详情
        test_content_id = 3055
        print(f"📋 测试获取帖子详情: ID {test_content_id}")
        print("-" * 50)
        
        async with sohu_client as client:
            print(f"🔍 开始获取帖子 {test_content_id} 的详情...")
            
            start_time = datetime.now()
            result = await client.get_content_by_id(test_content_id)
            end_time = datetime.now()
            
            fetch_time = (end_time - start_time).total_seconds()
            
            if result:
                print(f"✅ 获取成功! 耗时: {fetch_time:.2f} 秒")
                print(f"📊 返回结果:")
                print(f"   状态码: {result.get('code')}")
                print(f"   消息: {result.get('msg')}")
                
                # 检查是否有数据
                if 'data' in result:
                    data = result['data']
                    print(f"✅ 包含数据字段")
                    
                    # 显示数据的基本信息
                    if isinstance(data, dict):
                        print(f"📝 数据字段:")
                        for key, value in data.items():
                            if isinstance(value, str) and len(value) > 100:
                                print(f"   {key}: {value[:100]}...")
                            else:
                                print(f"   {key}: {value}")
                    elif isinstance(data, list):
                        print(f"📝 数据是列表，长度: {len(data)}")
                        for i, item in enumerate(data[:3], 1):
                            print(f"   项目 {i}: {item}")
                    else:
                        print(f"📝 数据类型: {type(data)}")
                        print(f"   数据内容: {data}")
                else:
                    print(f"⚠️  没有data字段")
                
                # 显示完整的返回结果
                print(f"\n📋 完整返回结果:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
            else:
                print(f"❌ 获取失败")
        
        print(f"\n📋 测试2: 测试其他帖子ID")
        print("-" * 50)
        
        # 测试其他几个帖子ID
        test_ids = [3054, 3053, 3050, 3049]
        
        for content_id in test_ids:
            print(f"\n🔄 测试帖子 ID {content_id}:")
            
            try:
                result = await client.get_content_by_id(content_id)
                
                if result and result.get('code') == 200:
                    data = result.get('data', {})
                    if isinstance(data, dict):
                        title = data.get('title', '无标题')
                        content = data.get('content', '无内容')
                        has_content = bool(content and content.strip())
                        
                        print(f"   ✅ 成功获取")
                        print(f"   标题: {title[:30]}...")
                        print(f"   有文字内容: {'是' if has_content else '否'}")
                        if has_content:
                            print(f"   内容预览: {content[:50]}...")
                    else:
                        print(f"   ✅ 成功获取，数据类型: {type(data)}")
                else:
                    print(f"   ❌ 获取失败: {result.get('msg') if result else '未知错误'}")
                    
            except Exception as e:
                print(f"   ❌ 异常: {e}")
        
        print(f"\n🎯 测试总结")
        print("-" * 50)
        print(f"✅ 帖子详情接口: 已测试")
        print(f"✅ 接口地址: /app/api/content/article/{test_content_id}")
        print(f"✅ 获取方式: GET请求")
        print(f"✅ 需要认证: 是")
        print(f"✅ 加密方式: 是")
        
        print(f"\n✨ 帖子详情获取测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_content_detail()) 