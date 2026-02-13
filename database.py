import sqlite3
import json
from datetime import datetime
import os
from contextlib import contextmanager

DATABASE_PATH = '/root/claude-web/conversations.db'

@contextmanager
def get_db_connection():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """初始化数据库"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 创建对话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                metadata TEXT
            )
        ''')

        # 创建索引以提高搜索性能
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_username ON conversations(username)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_content ON conversations(content)
        ''')

    # 初始化MCP相关表
    from mcp_database import init_mcp_db
    init_mcp_db()

def save_message(username, role, content, model=None, session_id=None, metadata=None):
    """保存单条消息"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        metadata_json = json.dumps(metadata) if metadata else None

        cursor.execute('''
            INSERT INTO conversations (username, role, content, model, session_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, role, content, model, session_id, metadata_json))

        message_id = cursor.lastrowid

    return message_id

def get_conversation_history(username, limit=100):
    """获取用户的对话历史"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, role, content, model, timestamp, session_id, metadata
            FROM conversations
            WHERE username = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (username, limit))

        rows = cursor.fetchall()

    # 反转顺序，使最新的在最后
    messages = []
    for row in reversed(rows):
        metadata = json.loads(row[6]) if row[6] else None
        messages.append({
            'id': row[0],
            'role': row[1],
            'content': row[2],
            'model': row[3],
            'timestamp': row[4],
            'session_id': row[5],
            'metadata': metadata
        })

    return messages

def search_conversations(username, query, limit=50):
    """搜索对话内容"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 使用 LIKE 进行模糊搜索
        search_pattern = f'%{query}%'

        cursor.execute('''
            SELECT id, role, content, model, timestamp, session_id
            FROM conversations
            WHERE username = ? AND content LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (username, search_pattern, limit))

        rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            'id': row[0],
            'role': row[1],
            'content': row[2],
            'model': row[3],
            'timestamp': row[4],
            'session_id': row[5]
        })

    return results

def clear_user_history(username):
    """清除用户的所有对话历史"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('DELETE FROM conversations WHERE username = ?', (username,))

        deleted_count = cursor.rowcount

    return deleted_count

def get_conversation_stats(username):
    """获取用户的对话统计信息"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as total_messages,
                COUNT(DISTINCT session_id) as total_sessions,
                MIN(timestamp) as first_message,
                MAX(timestamp) as last_message
            FROM conversations
            WHERE username = ?
        ''', (username,))

        row = cursor.fetchone()

    return {
        'total_messages': row[0],
        'total_sessions': row[1],
        'first_message': row[2],
        'last_message': row[3]
    }

# 初始化数据库
if not os.path.exists(DATABASE_PATH):
    init_db()
