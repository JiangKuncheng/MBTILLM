 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的MBTI更新逻辑
"""

import asyncio
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mbti_update_logic():
    """测试MBTI更新逻辑"""
    print("🧪 测试新的MBTI更新逻辑")
    print("=" * 50)
    
    try:
        # 导入必要的模块
        from database_service import db_service
        from mbti_service import mbti_service
        
        # 测试用户ID
        test_user_id = 9999
        
        print(f"📋 测试用户ID: {test_user_id}")
        
        # 1. 检查用户当前状态
        print("\n1️⃣ 检查用户当前状态...")
        user_profile = db_service.get_user_profile(test_user_id)
        if user_profile:
            print(f"   ✅ 用户档案存在")
            print(f"   📊 当前MBTI类型: {user_profile.mbti_type}")
            print(f"   📈 行为数: {user_profile.behaviors_since_last_update}")
        else:
            print(f"   ❌ 用户档案不存在")
        
        # 2. 检查用户行为数量
        print("\n2️⃣ 检查用户行为数量...")
        behavior_count = db_service.get_user_behavior_count(test_user_id)
        print(f"   📊 总行为数: {behavior_count}")
        
        # 3. 模拟用户行为记录（每50条触发一次MBTI更新）
        print("\n3️⃣ 模拟用户行为记录...")
        threshold = 50
        
        for i in range(1, 6):  # 模拟5次行为
            print(f"   📝 记录第 {i} 次行为...")
            
            # 记录行为
            behavior = db_service.record_user_behavior(
                user_id=test_user_id,
                content_id=1000 + i,
                action="like",
                source="test",
                weight=0.8
            )
            
            # 增加行为计数
            new_count = db_service.increment_behavior_count(test_user_id)
            print(f"     行为ID: {behavior.id}, 新计数: {new_count}")
            
            # 检查是否达到阈值
            if new_count % threshold == 0:
                print(f"      🎯 达到新的{threshold}条行为阈值！")
                
                # 触发MBTI更新
                print(f"      🔄 触发MBTI更新...")
                update_result = await mbti_service.update_user_mbti_profile(
                    test_user_id, 
                    force_update=True
                )
                
                if update_result.get("updated"):
                    print(f"      ✅ MBTI更新成功")
                    print(f"         📊 新MBTI类型: {update_result.get('new_mbti_type')}")
                    print(f"         📈 分析的行为数: {update_result.get('behaviors_analyzed')}")
                    print(f"         📝 分析的内容数: {update_result.get('contents_analyzed')}")
                else:
                    print(f"      ❌ MBTI更新失败: {update_result.get('reason')}")
            else:
                remaining = threshold - (new_count % threshold)
                print(f"      📍 还需 {remaining} 条行为达到下一个阈值")
        
        # 4. 检查最终状态
        print("\n4️⃣ 检查最终状态...")
        final_profile = db_service.get_user_profile(test_user_id)
        final_behavior_count = db_service.get_user_behavior_count(test_user_id)
        
        print(f"   📊 最终行为数: {final_behavior_count}")
        if final_profile:
            print(f"   🎯 最终MBTI类型: {final_profile.mbti_type}")
            print(f"   📈 档案行为数: {final_profile.behaviors_since_last_update}")
            print(f"   🕒 最后更新: {final_profile.last_updated}")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_mbti_update_logic())