#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试数据库操作
"""

import sqlite3
from pathlib import Path

def clear_database():
    """清空数据库"""
    
    db_path = "mbti_system.db"
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件 {db_path} 不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🗑️ 清空数据库")
        print("=" * 40)
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 清空每个表
        for table in tables:
            if table != "sqlite_sequence":  # 跳过系统表
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    cursor.execute(f"DELETE FROM {table}")
                    print(f"✅ 清空表 {table}: 删除了 {count} 条记录")
                except Exception as e:
                    print(f"❌ 清空表 {table} 时出错: {e}")
        
        # 重置自增ID
        cursor.execute("DELETE FROM sqlite_sequence")
        print("✅ 重置自增ID")
        
        conn.commit()
        conn.close()
        
        print("🎉 数据库清空完成！")
        
    except Exception as e:
        print(f"❌ 清空数据库时出错: {e}")

def test_database():
    """测试数据库操作"""
    
    db_path = "mbti_system.db"
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件 {db_path} 不存在")
        return
    
    print("🧪 简单数据库测试")
    print("=" * 40)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查表结构
        print("\n📋 1. 检查表结构")
        print("-" * 20)
        
        cursor.execute("PRAGMA table_info(mbti_post_evaluations)")
        columns = cursor.fetchall()
        
        print("mbti_post_evaluations表字段:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # 2. 检查现有数据
        print("\n📊 2. 检查现有数据")
        print("-" * 20)
        
        cursor.execute("SELECT COUNT(*) FROM mbti_post_evaluations")
        count = cursor.fetchone()[0]
        print(f"mbti_post_evaluations表记录数: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM mbti_post_evaluations LIMIT 3")
            rows = cursor.fetchall()
            print("前3条记录:")
            for row in rows:
                print(f"  {row}")
        
        # 3. 尝试插入测试数据
        print("\n➕ 3. 插入测试数据")
        print("-" * 20)
        
        try:
            cursor.execute("""
                INSERT INTO mbti_post_evaluations 
                (content_id, E, I, S, N, T, F, J, P, model_version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                9999,  # content_id
                0.7, 0.3,  # E, I
                0.6, 0.4,  # S, N
                0.5, 0.5,  # T, F
                0.8, 0.2,  # J, P
                "v1.0",    # model_version
            ))
            
            conn.commit()
            print("✅ 测试数据插入成功")
            
            # 验证插入
            cursor.execute("SELECT COUNT(*) FROM mbti_post_evaluations")
            new_count = cursor.fetchone()[0]
            print(f"插入后记录数: {new_count}")
            
            # 查看插入的数据
            cursor.execute("SELECT * FROM mbti_post_evaluations WHERE content_id = 9999")
            row = cursor.fetchone()
            if row:
                print("插入的数据:")
                print(f"  ID: {row[0]}")
                print(f"  content_id: {row[1]}")
                print(f"  E: {row[2]}, I: {row[3]}")
                print(f"  S: {row[4]}, N: {row[5]}")
                print(f"  T: {row[6]}, F: {row[7]}")
                print(f"  J: {row[8]}, P: {row[9]}")
                print(f"  model_version: {row[10]}")
                print(f"  created_at: {row[11]}")
            
        except Exception as e:
            print(f"❌ 插入测试数据失败: {e}")
        
        # 4. 测试MBTI评价功能（通过API）
        print("\n🧠 4. 测试MBTI评价功能")
        print("-" * 20)
        
        try:
            # 这里可以添加调用MBTI评价API的测试
            print("📝 准备测试MBTI评价...")
            print("💡 提示：可以运行 test_mbti_evaluation.py 来测试完整的MBTI评价功能")
            
        except Exception as e:
            print(f"❌ MBTI评价测试失败: {e}")
        
        # 5. 测试主要API接口
        print("\n🌐 5. 测试主要API接口")
        print("-" * 20)
        
        try:
            import requests
            import json
            
            base_url = "http://localhost:8000"
            
            # 测试健康检查API
            print("🔍 测试健康检查API...")
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ 健康检查API正常")
                    print(f"   响应: {response.json()}")
                else:
                    print(f"❌ 健康检查API异常: {response.status_code}")
            except Exception as e:
                print(f"❌ 健康检查API连接失败: {e}")
            
            # 测试系统信息API
            print("\n🔍 测试系统信息API...")
            try:
                response = requests.get(f"{base_url}/api/v1/system/info", timeout=5)
                if response.status_code == 200:
                    print("✅ 系统信息API正常")
                    data = response.json()
                    if data.get("success"):
                        stats = data["data"]["database_stats"]
                        print(f"   用户总数: {stats['total_users']}")
                        print(f"   行为记录数: {stats['total_behaviors']}")
                        print(f"   内容MBTI评价数: {stats['total_contents']}")
                        print(f"   推荐日志数: {stats['total_recommendations']}")
                    else:
                        print(f"   响应异常: {data.get('message', '未知错误')}")
                else:
                    print(f"❌ 系统信息API异常: {response.status_code}")
            except Exception as e:
                print(f"❌ 系统信息API连接失败: {e}")
            
            # 测试内容评价API
            print("\n🔍 测试内容评价API...")
            try:
                test_content_id = 1001
                response = requests.post(f"{base_url}/api/v1/admin/content/{test_content_id}/evaluate", timeout=10)
                if response.status_code == 200:
                    print("✅ 内容评价API正常")
                    data = response.json()
                    if data.get("success"):
                        if data["data"].get("already_evaluated"):
                            print(f"   内容 {test_content_id} 已评价")
                        else:
                            print(f"   内容 {test_content_id} 评价已开始")
                    else:
                        print(f"   响应异常: {data.get('message', '未知错误')}")
                else:
                    print(f"❌ 内容评价API异常: {response.status_code}")
            except Exception as e:
                print(f"❌ 内容评价API连接失败: {e}")
            
            # 测试用户行为记录API
            print("\n🔍 测试用户行为记录API...")
            try:
                behavior_data = {
                    "user_id": 9999,
                    "content_id": 9999,
                    "action": "like",
                    "source": "api_test"
                }
                response = requests.post(f"{base_url}/api/v1/behavior/record", json=behavior_data, timeout=5)
                if response.status_code == 200:
                    print("✅ 用户行为记录API正常")
                    data = response.json()
                    if data.get("success"):
                        print("   行为记录成功")
                    else:
                        print(f"   响应异常: {data.get('message', '未知错误')}")
                else:
                    print(f"❌ 用户行为记录API异常: {response.status_code}")
            except Exception as e:
                print(f"❌ 用户行为记录API连接失败: {e}")
            
            print("\n💡 API测试完成！如果大部分API都正常，说明系统运行良好")
            
        except ImportError:
            print("⚠️  缺少requests库，跳过API测试")
            print("   可以运行: pip install requests")
        except Exception as e:
            print(f"❌ API测试失败: {e}")
        
        # 6. 测试数据库连接和查询
        print("\n🔍 6. 测试数据库查询功能")
        print("-" * 20)
        
        try:
            # 测试复杂查询
            cursor.execute("""
                SELECT content_id, E, I, S, N, T, F, J, P, model_version
                FROM mbti_post_evaluations 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            if rows:
                print("最新5条MBTI评价记录:")
                for i, row in enumerate(rows, 1):
                    print(f"  {i}. 内容ID: {row[0]}")
                    print(f"     E: {row[1]:.3f}, I: {row[2]:.3f}")
                    print(f"     S: {row[3]:.3f}, N: {row[4]:.3f}")
                    print(f"     T: {row[5]:.3f}, F: {row[6]:.3f}")
                    print(f"     J: {row[7]:.3f}, P: {row[8]:.3f}")
                    print(f"     版本: {row[9]}")
                    print()
            else:
                print("暂无MBTI评价记录")
                
        except Exception as e:
            print(f"❌ 查询测试失败: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 数据库操作工具")
    print("=" * 40)
    print("1. 清空数据库")
    print("2. 测试数据库")
    print("3. 退出")
    print()
    
    choice = input("请选择操作 (1-3): ").strip()
    
    if choice == "1":
        confirm = input("确认要清空数据库吗？输入 'YES' 确认: ").strip()
        if confirm == "YES":
            clear_database()
        else:
            print("❌ 操作已取消")
    elif choice == "2":
        test_database()
    elif choice == "3":
        print("👋 再见！")
    else:
        print("❌ 无效选择")
