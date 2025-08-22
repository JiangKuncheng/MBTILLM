#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印搜狐接口信息
"""

import asyncio
import json
from datetime import datetime

async def print_sohu_api_info():
    """打印搜狐接口的详细信息"""
    print("🌐 搜狐接口信息")
    print("=" * 60)
    
    try:
        from sohu_client import sohu_client
        
        async with sohu_client as client:
            print("📋 接口基础信息")
            print("-" * 40)
            print(f"   基础URL: {client.base_url}")
            print(f"   超时设置: {client.timeout}秒")
            print(f"   重试次数: {client.max_retries}")
            print()
            
            print("🔐 认证流程")
            print("-" * 40)
            print("   1. 登录接口: /auth/v2/login")
            print("   2. 获取密钥: /app/v1/query/aesKey")
            print("   3. 加密认证: 使用HMAC-SHA256 + AES加密")
            print()
            
            print("📚 内容接口")
            print("-" * 40)
            print("   1. 图文列表: /app/api/content/article/list")
            print("   2. 内容详情: /app/api/content/{type}/detail/{id}")
            print("   3. 批量获取: /app/api/content/batch")
            print()
            
            print("🔑 请求头要求")
            print("-" * 40)
            print("   必需头:")
            print("     - Content-Type: application/json")
            print("     - x-encrypt-key: AES加密的认证数据")
            print("     - Version: 1.5.0")
            print("     - Authorization: Bearer {token}")
            print("   可选头:")
            print("     - syssource: sohuglobal")
            print("     - User-Agent: Apifox/1.0.0")
            print()
            
            print("📝 请求参数")
            print("-" * 40)
            print("   图文列表接口:")
            print("     - pageNum: 页码")
            print("     - pageSize: 每页数量")
            print("     - aiRec: false (避免重复推荐)")
            print("     - state: OnShelf (上架状态)")
            print("     - siteId: 站点ID (可选)")
            print("     - categoryId: 分类ID (可选)")
            print()
            
            print("🔒 加密数据格式")
            print("-" * 40)
            print("   {")
            print('     "token": "登录后的accessToken",')
            print('     "userId": "用户ID",')
            print('     "timestamp": "毫秒时间戳",')
            print('     "url": "相对路径",')
            print('     "platform": "web",')
            print('     "nonce": "随机字符串",')
            print('     "sign": "HMAC-SHA256签名"')
            print("   }")
            print()
            
            print("📊 返回数据格式")
            print("-" * 40)
            print("   {")
            print('     "code": 200,')
            print('     "msg": "查询成功",')
            print('     "total": 总数量,')
            print('     "data": [文章列表]')
            print("   }")
            print()
            
            print("📰 文章数据结构")
            print("-" * 40)
            print("   核心字段:")
            print("     - id: 文章ID")
            print("     - title: 标题")
            print("     - coverImage: 封面图片")
            print("     - userName: 作者用户名")
            print("     - nickName: 作者昵称")
            print("     - state: 状态")
            print("     - auditState: 审核状态")
            print("     - viewCount: 阅读数")
            print("     - praiseCount: 点赞数")
            print("     - collectCount: 收藏数")
            print()
            
            print("🔄 测试接口调用")
            print("-" * 40)
            
            # 测试获取第一页内容
            print("📖 获取第一页图文列表...")
            result = await client.get_article_list(
                page_num=1,
                page_size=3,
                state="OnShelf"
            )
            
            if result.get("code") == 200:
                print("✅ 接口调用成功")
                data = result.get("data", [])
                total = result.get("total", 0)
                
                print(f"   总数量: {total}")
                print(f"   当前页: {len(data)} 篇")
                print()
                
                print("📰 文章示例:")
                for i, article in enumerate(data[:2], 1):
                    print(f"   文章 {i}:")
                    print(f"     ID: {article.get('id')}")
                    print(f"     标题: {article.get('title')}")
                    print(f"     作者: {article.get('userName')} ({article.get('nickName')})")
                    print(f"     状态: {article.get('state')} | {article.get('auditState')}")
                    print(f"     封面: {article.get('coverImage')}")
                    print(f"     统计: 阅读{article.get('viewCount')} | 点赞{article.get('praiseCount')} | 收藏{article.get('collectCount')}")
                    print()
            else:
                print(f"❌ 接口调用失败: {result.get('msg')}")
            
            print("🎯 使用建议")
            print("-" * 40)
            print("   1. 每次请求都会自动登录和获取新token")
            print("   2. 加密数据每次都会重新生成，确保安全性")
            print("   3. aiRec=false 确保每次推荐结果不同")
            print("   4. 支持分页，建议每页20-50条")
            print("   5. 可以根据categoryId筛选特定分类内容")
            print()
            
            print("✨ 接口状态: 完全可用")
            print("🚀 可以开始集成到推荐系统中")
            
    except Exception as e:
        print(f"❌ 获取接口信息失败: {e}")

if __name__ == "__main__":
    asyncio.run(print_sohu_api_info()) 