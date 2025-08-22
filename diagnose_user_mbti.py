 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断用户MBTI问题的根源
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_service import db_service
from models import UserProfile, UserBehavior, ContentMBTI
from sqlalchemy import func, desc
from datetime import datetime

def diagnose_user_mbti(user_id: int):
    """诊断用户MBTI问题"""
    print(f"🔍 诊断用户 {user_id} 的MBTI问题")
    print("=" * 80)
    
    try:
        # 1. 检查用户档案
        print("📋 步骤1: 检查用户档案")
        print("-" * 50)
        
        user_profile = db_service.get_user_profile(user_id)
        if user_profile:
            print(f"   ✅ 用户档案存在")
            print(f"   - 用户ID: {user_profile.user_id}")
            print(f"   - MBTI类型: {user_profile.mbti_type or '未设置'}")
            print(f"   - E/I: {user_profile.E}/{user_profile.I}")
            print(f"   - S/N: {user_profile.S}/{user_profile.N}")
            print(f"   - T/F: {user_profile.T}/{user_profile.F}")
            print(f"   - J/P: {user_profile.J}/{user_profile.P}")
            print(f"   - 总行为数: {user_profile.total_behaviors_analyzed or 0}")
            print(f"   - 上次更新后行为数: {user_profile.behaviors_since_last_update or 0}")
            print(f"   - 最后更新时间: {user_profile.last_updated}")
        else:
            print(f"   ❌ 用户档案不存在")
            return
        
        # 2. 检查用户行为统计
        print("\n📋 步骤2: 检查用户行为统计")
        print("-" * 50)
        
        with db_service.get_session() as session:
            # 总行为数
            total_behaviors = session.query(UserBehavior).filter(
                UserBehavior.user_id == user_id
            ).count()
            print(f"   - 总行为数: {total_behaviors}")
            
            # 行为类型分布
            action_stats = session.query(
                UserBehavior.action,
                func.count(UserBehavior.id)
            ).filter(UserBehavior.user_id == user_id).group_by(UserBehavior.action).all()
            
            print(f"   - 行为类型分布:")
            for action, count in action_stats:
                print(f"     * {action}: {count}")
            
            # 最近的行为
            recent_behaviors = session.query(UserBehavior).filter(
                UserBehavior.user_id == user_id
            ).order_by(desc(UserBehavior.timestamp)).limit(5).all()
            
            print(f"   - 最近5个行为:")
            for behavior in recent_behaviors:
                print(f"     * {behavior.action} -> 内容{behavior.content_id} ({behavior.timestamp})")
        
        # 3. 检查用户操作的帖子
        print("\n📋 步骤3: 检查用户操作的帖子")
        print("-" * 50)
        
        user_operation_posts = db_service.get_user_operation_posts(user_id)
        post_count = len(user_operation_posts)
        print(f"   - 操作帖子数量: {post_count}")
        print(f"   - 是否达到50倍数: {post_count % 50 == 0}")
        
        if post_count >= 50:
            print(f"   - 距离下一个50倍数: {50 - (post_count % 50)}")
        else:
            print(f"   - 距离50倍数: {50 - post_count}")
        
        # 4. 检查帖子MBTI评分
        print("\n📋 步骤4: 检查帖子MBTI评分")
        print("-" * 50)
        
        posts_with_mbti = 0
        posts_without_mbti = 0
        
        for post_id in user_operation_posts[:10]:  # 只检查前10个
            post_mbti = db_service.get_content_mbti(post_id)
            if post_mbti:
                posts_with_mbti += 1
            else:
                posts_without_mbti += 1
        
        print(f"   - 前10个帖子中:")
        print(f"     * 有MBTI评分: {posts_with_mbti}")
        print(f"     * 无MBTI评分: {posts_without_mbti}")
        
        # 5. 检查MBTI更新触发条件
        print("\n📋 步骤5: 检查MBTI更新触发条件")
        print("-" * 50)
        
        if post_count % 50 == 0:
            print(f"   ✅ 满足更新条件: 帖子数量({post_count})是50的倍数")
        else:
            print(f"   ❌ 不满足更新条件: 帖子数量({post_count})不是50的倍数")
            print(f"   - 需要达到: {((post_count // 50) + 1) * 50}")
        
        # 6. 手动触发MBTI更新测试
        print("\n📋 步骤6: 手动触发MBTI更新测试")
        print("-" * 50)
        
        if post_count >= 50:
            print(f"   🔄 尝试手动触发MBTI更新...")
            try:
                from mbti_service import mbti_service
                import asyncio
                
                async def test_update():
                    result = await mbti_service.update_user_mbti_when_posts_reach_50_multiple(user_id, force_update=True)
                    return result
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(test_update())
                loop.close()
                
                print(f"   - 更新结果: {result}")
                
            except Exception as e:
                print(f"   ❌ 手动更新失败: {e}")
        else:
            print(f"   ⚠️  帖子数量不足50，无法测试更新")
        
        # 7. 建议和解决方案
        print("\n📋 步骤7: 问题分析和解决方案")
        print("-" * 50)
        
        if not user_profile.mbti_type:
            print(f"   🔴 主要问题: 用户档案存在但没有MBTI类型")
            print(f"   💡 解决方案:")
            print(f"     1. 手动触发MBTI更新: 调用update_user_mbti_when_posts_reach_50_multiple(user_id, force_update=True)")
            print(f"     2. 检查帖子MBTI评分: 确保用户操作的帖子都有MBTI评分")
            print(f"     3. 检查更新逻辑: 确认异步更新是否正常工作")
        
        elif post_count % 50 != 0:
            print(f"   🟡 主要问题: 帖子数量({post_count})不是50的倍数")
            print(f"   💡 解决方案:")
            print(f"     1. 等待达到50倍数: 还需要{50 - (post_count % 50)}个帖子")
            print(f"     2. 强制更新: 使用force_update=True参数")
            print(f"     3. 调整阈值: 修改50倍数的逻辑")
        
        else:
            print(f"   🟢 用户满足更新条件，检查其他可能的问题")
        
        print("\n🎉 诊断完成！")
        
    except Exception as e:
        print(f"❌ 诊断过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python diagnose_user_mbti.py <user_id>")
        print("示例: python diagnose_user_mbti.py 1")
        return
    
    try:
        user_id = int(sys.argv[1])
        diagnose_user_mbti(user_id)
    except ValueError:
        print("错误: user_id必须是整数")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()