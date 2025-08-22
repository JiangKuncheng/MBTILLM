#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印搜狐接口返回的文章完整信息
"""

import asyncio
import json
from datetime import datetime

async def print_article_full_info():
    """打印搜狐接口返回的文章完整信息"""
    print("📰 搜狐接口文章完整信息")
    print("=" * 60)
    
    try:
        from sohu_client import sohu_client
        
        async with sohu_client as client:
            print("📖 获取第一页图文列表...")
            result = await client.get_article_list(
                page_num=1,
                page_size=2,  # 只获取2篇，便于查看
                state="OnShelf"
            )
            
            if result.get("code") == 200:
                print("✅ 接口调用成功")
                data = result.get("data", [])
                total = result.get("total", 0)
                
                print(f"总数量: {total}")
                print(f"当前页: {len(data)} 篇")
                print()
                
                # 显示第一篇文章的完整信息
                if data:
                    article = data[0]
                    print("🔍 第一篇文章完整字段信息:")
                    print("-" * 50)
                    
                    # 按类别分组显示字段
                    print("📋 基础信息:")
                    print(f"   ID: {article.get('id')}")
                    print(f"   标题: {article.get('title')}")
                    print(f"   类型: {article.get('type')}")
                    print(f"   媒体类型: {article.get('mediaContentType')}")
                    print()
                    
                    print("👤 用户信息:")
                    print(f"   用户ID: {article.get('userId')}")
                    print(f"   用户名: {article.get('userName')}")
                    print(f"   昵称: {article.get('nickName')}")
                    print(f"   头像: {article.get('userAvatar')}")
                    print()
                    
                    print("🏷️ 分类信息:")
                    print(f"   站点ID: {article.get('siteId')}")
                    print(f"   分类ID: {article.get('categoryId')}")
                    print(f"   分类名称: {article.get('categoryName')}")
                    print(f"   站点名称: {article.get('siteName')}")
                    print()
                    
                    print("🖼️ 图片信息:")
                    print(f"   封面图片: {article.get('coverImage')}")
                    print(f"   封面URL: {article.get('coverUrl')}")
                    print(f"   图片列表: {article.get('images')}")
                    print()
                    
                    print("📊 统计信息:")
                    print(f"   阅读数: {article.get('viewCount')}")
                    print(f"   评论数: {article.get('commentCount')}")
                    print(f"   点赞数: {article.get('praiseCount')}")
                    print(f"   收藏数: {article.get('collectCount')}")
                    print(f"   转发数: {article.get('forwardCount')}")
                    print(f"   学习数: {article.get('learnNum')}")
                    print(f"   提交数: {article.get('submitNum')}")
                    print()
                    
                    print("📝 内容信息:")
                    print(f"   内容: {article.get('content')}")
                    print(f"   信息: {article.get('info')}")
                    print(f"   关系: {article.get('relation')}")
                    print()
                    
                    print("⏰ 时间信息:")
                    print(f"   创建时间: {article.get('createTime')}")
                    print(f"   更新时间: {article.get('updateTime')}")
                    print(f"   提交时间: {article.get('submitTime')}")
                    print(f"   审核时间: {article.get('auditTime')}")
                    print(f"   删除时间: {article.get('delTime')}")
                    print(f"   移除时间: {article.get('removeTime')}")
                    print()
                    
                    print("🔧 系统信息:")
                    print(f"   创建者: {article.get('createBy')}")
                    print(f"   更新者: {article.get('updateBy')}")
                    print(f"   排序索引: {article.get('sortIndex')}")
                    print(f"   同步草稿: {article.get('syncDraft')}")
                    print()
                    
                    print("📋 状态信息:")
                    print(f"   状态: {article.get('state')}")
                    print(f"   审核状态: {article.get('auditState')}")
                    print(f"   拒绝原因: {article.get('rejectReason')}")
                    print(f"   内容状态: {article.get('contentState')}")
                    print(f"   可见类型: {article.get('visibleType')}")
                    print(f"   发布状态: {article.get('publishStatus')}")
                    print(f"   申诉状态: {article.get('appealStatus')}")
                    print(f"   申诉原因: {article.get('appealReason')}")
                    print()
                    
                    print("🎯 功能开关:")
                    print(f"   是否分享: {article.get('isShare')}")
                    print(f"   是否下载: {article.get('isDownload')}")
                    print(f"   点赞对象: {article.get('praiseObj')}")
                    print(f"   关注对象: {article.get('followObj')}")
                    print(f"   收藏对象: {article.get('collectObj')}")
                    print()
                    
                    print("🔗 关联信息:")
                    print(f"   平台数量: {article.get('platformNum')}")
                    print(f"   MCN用户ID: {article.get('mcnUserId')}")
                    print(f"   发布媒体ID: {article.get('publishMediaId')}")
                    print(f"   课程标签ID: {article.get('lessonLabelId')}")
                    print(f"   子任务编号: {article.get('childTaskNumber')}")
                    print(f"   事件ID: {article.get('eventId')}")
                    print(f"   忙碌类型: {article.get('busyType')}")
                    print()
                    
                    print("📱 发布信息:")
                    print(f"   提交场景: {article.get('submitScene')}")
                    print(f"   数据: {article.get('data')}")
                    print(f"   结果项: {article.get('resultItem')}")
                    print()
                    
                    print("🤖 AI相关信息:")
                    ai_result = article.get('aiResultItem', {})
                    if ai_result:
                        print("   AI结果项:")
                        print(f"     匹配信息: {ai_result.get('matchInfo')}")
                        print(f"     追踪ID: {ai_result.get('traceId')}")
                        print(f"     位置: {ai_result.get('position')}")
                        print(f"     项目ID: {ai_result.get('itemId')}")
                        print(f"     项目类型: {ai_result.get('itemType')}")
                        print(f"     追踪信息: {ai_result.get('traceInfo')}")
                        print(f"     权重: {ai_result.get('weight')}")
                        print(f"     流量权重: {ai_result.get('flowWeight')}")
                        print(f"     消息: {ai_result.get('message')}")
                    print()
                    
                    print("🔍 其他字段:")
                    print(f"   关系: {article.get('relation')}")
                    print(f"   数据: {article.get('data')}")
                    print(f"   结果项: {article.get('resultItem')}")
                    print(f"   AI项目ID: {article.get('aiItemId')}")
                    print()
                    
                    print("📋 原始JSON数据:")
                    print("-" * 50)
                    print(json.dumps(article, indent=2, ensure_ascii=False))
                    
                else:
                    print("❌ 没有获取到文章数据")
            else:
                print(f"❌ 接口调用失败: {result.get('msg')}")
            
    except Exception as e:
        print(f"❌ 获取文章信息失败: {e}")

if __name__ == "__main__":
    asyncio.run(print_article_full_info()) 