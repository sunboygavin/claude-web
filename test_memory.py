#!/usr/bin/env python3
"""
测试对话记忆和搜索功能
"""

import database
import sys

def test_database():
    """测试数据库功能"""
    print("=" * 60)
    print("测试对话记忆和搜索功能")
    print("=" * 60)

    # 测试 1: 保存消息
    print("\n[测试 1] 保存消息...")
    try:
        msg_id = database.save_message(
            username="test_user",
            role="user",
            content="这是一条测试消息，包含关键词：Python",
            model="sonnet",
            session_id="test_session_1"
        )
        print(f"✓ 消息保存成功，ID: {msg_id}")
    except Exception as e:
        print(f"✗ 保存失败: {e}")
        return False

    # 测试 2: 保存 assistant 消息
    print("\n[测试 2] 保存 assistant 消息...")
    try:
        msg_id = database.save_message(
            username="test_user",
            role="assistant",
            content="我可以帮你学习 Python 编程",
            model="sonnet",
            session_id="test_session_1"
        )
        print(f"✓ 消息保存成功，ID: {msg_id}")
    except Exception as e:
        print(f"✗ 保存失败: {e}")
        return False

    # 测试 3: 获取历史记录
    print("\n[测试 3] 获取历史记录...")
    try:
        history = database.get_conversation_history("test_user", limit=10)
        print(f"✓ 获取到 {len(history)} 条历史记录")
        for msg in history:
            print(f"  - [{msg['role']}] {msg['content'][:50]}...")
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        return False

    # 测试 4: 搜索对话
    print("\n[测试 4] 搜索对话...")
    try:
        results = database.search_conversations("test_user", "Python", limit=10)
        print(f"✓ 搜索到 {len(results)} 条匹配记录")
        for result in results:
            print(f"  - [{result['role']}] {result['content'][:50]}...")
    except Exception as e:
        print(f"✗ 搜索失败: {e}")
        return False

    # 测试 5: 获取统计信息
    print("\n[测试 5] 获取统计信息...")
    try:
        stats = database.get_conversation_stats("test_user")
        print(f"✓ 统计信息:")
        print(f"  - 总消息数: {stats['total_messages']}")
        print(f"  - 总会话数: {stats['total_sessions']}")
        print(f"  - 首次消息: {stats['first_message']}")
        print(f"  - 最后消息: {stats['last_message']}")
    except Exception as e:
        print(f"✗ 获取统计失败: {e}")
        return False

    # 测试 6: 清除历史
    print("\n[测试 6] 清除测试数据...")
    try:
        deleted = database.clear_user_history("test_user")
        print(f"✓ 清除了 {deleted} 条记录")
    except Exception as e:
        print(f"✗ 清除失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ 所有测试通过！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
