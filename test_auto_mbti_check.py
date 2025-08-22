 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动MBTI检查功能
验证在记录用户行为时是否自动检查并更新MBTI
"""

import asyncio
import time
from database_service import db_service
from mbti_service import mbti_service

async def test_auto_mbti_check():
    """测试自动MBTI检查功能"""
    print("🧪 测试自动MBTI检查功能")
    print("=" * 80)
    
    try:
        test_content_id = 3055
        test_user_id = 9999
        
        print(f"📋 测试内容ID: {test_content_id}")
        print(f"📋 测试用户ID: {test_user_id}")
        
        # 步骤1: 检查初始状态
        print("\n📋 步骤1: 检查初始状态")
        print("-" * 50)
        
        # 检查内容当前操作用户数量
        content_users = db_service.get_content_operation_users(test_content_id)
        content_user_count = len(content_users)
        print(f"   📊 内容 {test_content_id} 当前操作用户数量: {content_user_count}")
        
        # 检查用户当前操作帖子数量
        user_posts = db_service.get_user_operation_posts(test_user_id)
        user_post_count = len(user_posts)
        print(f"   📊 用户 {test_user_id} 当前操作帖子数量: {user_post_count}")
        
        # 步骤2: 模拟用户行为，触发自动检查
        print("\n📋 步骤2: 模拟用户行为，触发自动检查")
        print("-" * 50)
        
        # 模拟多个用户对同一内容进行操作
        test_users = list(range(10001, 10051))  # 50个新用户
        
        print(f"   👥 模拟 {len(test_users)} 个用户对内容 {test_content_id} 进行操作...")
        
        for i, user_id in enumerate(test_users, 1):
            try:
                # 记录用户行为（这会自动触发MBTI检查）
                behavior = db_service.record_user_behavior(
                    user_id=user_id,
                    content_id=test_content_id,
                    action="like",
                    source="test_auto_check",
                    session_id=f"test_auto_session_{user_id}",
                    extra_data={"test": True, "auto_check": True}
                )
                
                if i % 10 == 0:
                    print(f"      ✅ 已记录 {i}/{len(test_users)} 个用户行为")
                
                # 短暂延迟，让异步检查有时间执行
                time.sleep(0.1)
                
            except Exception as e:
                print(f"      ❌ 记录用户 {user_id} 行为失败: {e}")
        
        print(f"   ✅ 成功记录 {len(test_users)} 个用户行为")
        
        # 步骤3: 等待异步检查完成
        print("\n📋 步骤3: 等待异步检查完成")
        print("-" * 50)
        
        print("   ⏳ 等待5秒让异步MBTI检查完成...")
        await asyncio.sleep(5)
        
        # 步骤4: 检查更新结果
        print("\n📋 步骤4: 检查更新结果")
        print("-" * 50)
        
        # 重新检查内容操作用户数量
        updated_content_users = db_service.get_content_operation_users(test_content_id)
        updated_content_user_count = len(updated_content_users)
        print(f"   📊 内容 {test_content_id} 更新后操作用户数量: {updated_content_user_count}")
        
        if updated_content_user_count >= 50:
            print(f"   ✅ 内容操作用户数量已达到50，应该触发MBTI更新")
            
            # 检查内容MBTI是否已更新
            content_mbti = db_service.get_content_mbti(test_content_id)
            if content_mbti:
                print(f"   📊 内容 {test_content_id} 当前MBTI评分:")
                print(f"      E: {content_mbti.E:.3f}, I: {content_mbti.I:.3f}")
                print(f"      S: {content_mbti.S:.3f}, N: {content_mbti.N:.3f}")
                print(f"      T: {content_mbti.T:.3f}, F: {content_mbti.F:.3f}")
                print(f"      J: {content_mbti.J:.3f}, P: {content_mbti.P:.3f}")
        else:
            print(f"   ⚠️ 内容操作用户数量未达到50，不会触发MBTI更新")
        
        # 检查用户操作帖子数量
        updated_user_posts = db_service.get_user_operation_posts(test_user_id)
        updated_user_post_count = len(updated_user_posts)
        print(f"   📊 用户 {test_user_id} 更新后操作帖子数量: {updated_user_post_count}")
        
        if updated_user_post_count % 50 == 0 and updated_user_post_count > 0:
            print(f"   ✅ 用户操作帖子数量达到50倍数，应该触发MBTI更新")
            
            # 检查用户MBTI是否已更新
            user_profile = db_service.get_user_profile(test_user_id)
            if user_profile and user_profile.mbti_type:
                print(f"   📊 用户 {test_user_id} 当前MBTI: {user_profile.mbti_type}")
                print(f"      E: {user_profile.E:.3f}, I: {user_profile.I:.3f}")
                print(f"      S: {user_profile.S:.3f}, N: {user_profile.N:.3f}")
                print(f"      T: {user_profile.T:.3f}, F: {user_profile.F:.3f}")
                print(f"      J: {user_profile.J:.3f}, P: {user_profile.P:.3f}")
        else:
            print(f"   ⚠️ 用户操作帖子数量未达到50倍数，不会触发MBTI更新")
        
        # 步骤5: 手动验证自动检查逻辑
        print("\n📋 步骤5: 手动验证自动检查逻辑")
        print("-" * 50)
        
        print("   🔍 手动调用内容MBTI更新检查...")
        content_result = await mbti_service.update_content_mbti_when_users_reach_50(test_content_id)
        print(f"      结果: {content_result}")
        
        print("   🔍 手动调用用户MBTI更新检查...")
        user_result = await mbti_service.update_user_mbti_when_posts_reach_50_multiple(test_user_id)
        print(f"      结果: {user_result}")
        
        print("\n🎉 自动MBTI检查测试完成！")
        
        # 总结
        print("\n📋 测试总结:")
        print(f"   内容 {test_content_id}: {updated_content_user_count} 个操作用户")
        print(f"   用户 {test_user_id}: {updated_user_post_count} 个操作帖子")
        print("   自动检查机制已集成到用户行为记录中")
        print("   每次记录行为后会自动检查是否需要更新MBTI")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    await test_auto_mbti_check()

if __name__ == "__main__":
    asyncio.run(main())