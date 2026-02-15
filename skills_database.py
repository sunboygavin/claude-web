"""
Database operations for Skills management.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect('conversations.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_skills_db():
    """Initialize Skills-related database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Skills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            skill_type TEXT NOT NULL,
            code TEXT NOT NULL,
            config TEXT,
            enabled BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_skills_enabled
        ON skills(enabled)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_skills_type
        ON skills(skill_type)
    ''')

    conn.commit()
    conn.close()


def add_skill(name: str, description: str, skill_type: str,
              code: str, config: Dict[str, Any] = None) -> int:
    """Add a new skill."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO skills (name, description, skill_type, code, config)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        name,
        description,
        skill_type,
        code,
        json.dumps(config) if config else None
    ))

    skill_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return skill_id


def get_skills(enabled_only: bool = True) -> List[Dict]:
    """Get all skills."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if enabled_only:
        cursor.execute('SELECT * FROM skills WHERE enabled = 1 ORDER BY name')
    else:
        cursor.execute('SELECT * FROM skills ORDER BY name')

    skills = []
    for row in cursor.fetchall():
        skill = dict(row)
        if skill['config']:
            skill['config'] = json.loads(skill['config'])
        skills.append(skill)

    conn.close()
    return skills


def get_skill(skill_id: int) -> Optional[Dict]:
    """Get a specific skill by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM skills WHERE id = ?', (skill_id,))
    row = cursor.fetchone()

    if row:
        skill = dict(row)
        if skill['config']:
            skill['config'] = json.loads(skill['config'])
        conn.close()
        return skill

    conn.close()
    return None


def update_skill(skill_id: int, **kwargs) -> bool:
    """Update skill configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()

    fields = []
    values = []

    for key, value in kwargs.items():
        if key in ['name', 'description', 'skill_type', 'code', 'enabled']:
            fields.append(f'{key} = ?')
            values.append(value)
        elif key == 'config' and value is not None:
            fields.append('config = ?')
            values.append(json.dumps(value))

    if not fields:
        conn.close()
        return False

    fields.append('updated_at = ?')
    values.append(datetime.now().isoformat())
    values.append(skill_id)

    query = f"UPDATE skills SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


def delete_skill(skill_id: int) -> bool:
    """Delete a skill."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM skills WHERE id = ?', (skill_id,))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


def load_predefined_skills():
    """Load predefined skills into the database."""
    import os

    skills_dir = os.path.join(os.path.dirname(__file__), 'skills')
    if not os.path.exists(skills_dir):
        return

    predefined_skills = [
        {
            'name': '文件操作',
            'description': '提供文件读写、复制、移动、删除等功能',
            'skill_type': 'python',
            'module': 'file_operations'
        },
        {
            'name': '文本处理',
            'description': '文本统计、词频分析、格式转换等',
            'skill_type': 'python',
            'module': 'text_processing'
        },
        {
            'name': '数据处理',
            'description': 'JSON/CSV 读写、数据过滤、排序等',
            'skill_type': 'python',
            'module': 'data_processing'
        },
        {
            'name': '网络爬虫',
            'description': 'URL 内容获取、文件下载、链接提取等',
            'skill_type': 'python',
            'module': 'web_scraping'
        },
        {
            'name': 'Git 操作',
            'description': 'Git 命令封装、仓库操作等',
            'skill_type': 'python',
            'module': 'git_operations'
        },
        {
            'name': '系统工具',
            'description': '系统信息获取、进程管理、环境变量操作',
            'skill_type': 'python',
            'module': 'system_utils'
        }
    ]

    for skill_info in predefined_skills:
        module_path = os.path.join(skills_dir, f"{skill_info['module']}.py")
        if os.path.exists(module_path):
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                # Check if skill already exists
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM skills WHERE name = ?', (skill_info['name'],))
                exists = cursor.fetchone()
                conn.close()

                if not exists:
                    add_skill(
                        name=skill_info['name'],
                        description=skill_info['description'],
                        skill_type=skill_info['skill_type'],
                        code=code,
                        config={'module': skill_info['module']}
                    )
            except Exception as e:
                print(f"Failed to load skill {skill_info['name']}: {e}")
