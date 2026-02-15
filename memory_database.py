"""
Database operations for Conversation Memory.
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


def init_memory_db():
    """Initialize Memory-related database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Memory entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            session_id TEXT,
            memory_type TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            metadata TEXT,
            tags TEXT,
            importance INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_memory_username
        ON memory_entries(username)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_memory_type
        ON memory_entries(memory_type)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_memory_created
        ON memory_entries(created_at)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_importance
        ON memory_entries(importance)
    ''')

    # Memory tags table (for better tag management)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (memory_id) REFERENCES memory_entries(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_memory_tags_memory
        ON memory_tags(memory_id)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_memory_tags_tag
        ON memory_tags(tag)
    ''')

    conn.commit()
    conn.close()


def add_memory_entry(username: str, memory_type: str, content: str,
                     title: str = None, session_id: str = None,
                     metadata: Dict[str, Any] = None, tags: List[str] = None,
                     importance: int = 1) -> int:
    """Add a new memory entry."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO memory_entries
        (username, session_id, memory_type, title, content, metadata, tags, importance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        username,
        session_id,
        memory_type,
        title,
        content,
        json.dumps(metadata) if metadata else None,
        json.dumps(tags) if tags else None,
        importance
    ))

    memory_id = cursor.lastrowid

    # Add tags to tags table
    if tags:
        for tag in tags:
            cursor.execute('''
                INSERT INTO memory_tags (memory_id, tag)
                VALUES (?, ?)
            ''', (memory_id, tag))

    conn.commit()
    conn.close()

    return memory_id


def get_memory_entries(username: str, memory_type: str = None,
                       limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get memory entries for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if memory_type:
        cursor.execute('''
            SELECT * FROM memory_entries
            WHERE username = ? AND memory_type = ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ? OFFSET ?
        ''', (username, memory_type, limit, offset))
    else:
        cursor.execute('''
            SELECT * FROM memory_entries
            WHERE username = ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ? OFFSET ?
        ''', (username, limit, offset))

    entries = []
    for row in cursor.fetchall():
        entry = dict(row)
        if entry['metadata']:
            entry['metadata'] = json.loads(entry['metadata'])
        if entry['tags']:
            entry['tags'] = json.loads(entry['tags'])
        entries.append(entry)

    conn.close()
    return entries


def get_memory_entry(memory_id: int, username: str = None) -> Optional[Dict]:
    """Get a specific memory entry by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if username:
        cursor.execute('SELECT * FROM memory_entries WHERE id = ? AND username = ?',
                      (memory_id, username))
    else:
        cursor.execute('SELECT * FROM memory_entries WHERE id = ?', (memory_id,))

    row = cursor.fetchone()

    if row:
        entry = dict(row)
        if entry['metadata']:
            entry['metadata'] = json.loads(entry['metadata'])
        if entry['tags']:
            entry['tags'] = json.loads(entry['tags'])
        conn.close()
        return entry

    conn.close()
    return None


def update_memory_entry(memory_id: int, username: str = None, **kwargs) -> bool:
    """Update memory entry."""
    conn = get_db_connection()
    cursor = conn.cursor()

    fields = []
    values = []

    for key, value in kwargs.items():
        if key in ['title', 'content', 'memory_type', 'importance']:
            fields.append(f'{key} = ?')
            values.append(value)
        elif key == 'metadata' and value is not None:
            fields.append('metadata = ?')
            values.append(json.dumps(value))
        elif key == 'tags' and value is not None:
            fields.append('tags = ?')
            values.append(json.dumps(value))

    if not fields:
        conn.close()
        return False

    fields.append('updated_at = ?')
    values.append(datetime.now().isoformat())
    values.append(memory_id)

    if username:
        fields.append('username = ?')
        values.append(username)

    query = f"UPDATE memory_entries SET {', '.join(fields)} WHERE id = ?"
    if username:
        query += " AND username = ?"

    cursor.execute(query, values)

    # Update tags table
    if 'tags' in kwargs and kwargs['tags'] is not None:
        cursor.execute('DELETE FROM memory_tags WHERE memory_id = ?', (memory_id,))
        for tag in kwargs['tags']:
            cursor.execute('''
                INSERT INTO memory_tags (memory_id, tag)
                VALUES (?, ?)
            ''', (memory_id, tag))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


def delete_memory_entry(memory_id: int, username: str = None) -> bool:
    """Delete a memory entry."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if username:
        cursor.execute('DELETE FROM memory_entries WHERE id = ? AND username = ?',
                      (memory_id, username))
    else:
        cursor.execute('DELETE FROM memory_entries WHERE id = ?', (memory_id,))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


def search_memory_entries(username: str, query: str,
                          limit: int = 50) -> List[Dict]:
    """Search memory entries."""
    conn = get_db_connection()
    cursor = conn.cursor()

    search_query = f'%{query}%'
    cursor.execute('''
        SELECT * FROM memory_entries
        WHERE username = ? AND (content LIKE ? OR title LIKE ?)
        ORDER BY importance DESC, created_at DESC
        LIMIT ?
    ''', (username, search_query, search_query, limit))

    entries = []
    for row in cursor.fetchall():
        entry = dict(row)
        if entry['metadata']:
            entry['metadata'] = json.loads(entry['metadata'])
        if entry['tags']:
            entry['tags'] = json.loads(entry['tags'])
        entries.append(entry)

    conn.close()
    return entries


def get_memory_tags(username: str) -> List[str]:
    """Get all tags for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT mt.tag
        FROM memory_tags mt
        JOIN memory_entries me ON mt.memory_id = me.id
        WHERE me.username = ?
        ORDER BY mt.tag
    ''', (username,))

    tags = [row['tag'] for row in cursor.fetchall()]
    conn.close()
    return tags


def get_memory_by_tag(username: str, tag: str, limit: int = 50) -> List[Dict]:
    """Get memory entries by tag."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT me.*
        FROM memory_entries me
        JOIN memory_tags mt ON me.id = mt.memory_id
        WHERE me.username = ? AND mt.tag = ?
        ORDER BY me.importance DESC, me.created_at DESC
        LIMIT ?
    ''', (username, tag, limit))

    entries = []
    for row in cursor.fetchall():
        entry = dict(row)
        if entry['metadata']:
            entry['metadata'] = json.loads(entry['metadata'])
        if entry['tags']:
            entry['tags'] = json.loads(entry['tags'])
        entries.append(entry)

    conn.close()
    return entries


def get_recent_memories_for_prompt(username: str, limit: int = 10) -> str:
    """Get recent memories formatted for inclusion in prompt."""
    entries = get_memory_entries(username, limit=limit)

    if not entries:
        return ""

    prompt_parts = ["\n## 相关记忆（最近记录）:\n"]

    for entry in entries:
        title = entry.get('title') or '无标题'
        content = entry.get('content', '')[:200]
        prompt_parts.append(f"- [{title}]: {content}...")

    return "\n".join(prompt_parts)


def record_conversation_memory(username: str, session_id: str,
                               role: str, content: str,
                               metadata: Dict[str, Any] = None):
    """Record a conversation turn as memory."""
    memory_type = 'conversation'
    title = f"{role.capitalize()}: {content[:50]}..." if len(content) > 50 else f"{role.capitalize()}"

    return add_memory_entry(
        username=username,
        session_id=session_id,
        memory_type=memory_type,
        title=title,
        content=content,
        metadata=metadata,
        tags=['conversation', role],
        importance=1
    )


def record_fact_memory(username: str, fact: str, source: str = None,
                       importance: int = 3):
    """Record an important fact as memory."""
    metadata = {'source': source} if source else None

    return add_memory_entry(
        username=username,
        memory_type='fact',
        title=fact[:100] if len(fact) > 100 else fact,
        content=fact,
        metadata=metadata,
        tags=['fact', 'important'],
        importance=importance
    )


def export_to_obsidian(username: str, output_dir: str = None,
                       group_by: str = 'date') -> Dict[str, Any]:
    """
    Export memories to Obsidian-compatible Markdown files.

    Args:
        username: Username
        output_dir: Output directory (optional)
        group_by: How to group files ('date', 'type', 'tag')

    Returns:
        Dictionary with export results
    """
    import os
    from datetime import datetime

    memories = get_memory_entries(username, limit=1000)

    if not memories:
        return {'success': False, 'message': 'No memories to export'}

    exported_files = []

    for memory in memories:
        # Generate filename
        title = memory.get('title') or 'Untitled'
        # Clean filename
        filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = filename.replace(' ', '_')[:50] or 'memory'
        filename += '.md'

        # Generate frontmatter
        frontmatter = {
            'title': memory.get('title') or '',
            'type': memory.get('memory_type', 'note'),
            'importance': memory.get('importance', 1),
            'created_at': memory.get('created_at', ''),
            'updated_at': memory.get('updated_at', ''),
            'tags': memory.get('tags', [])
        }

        if memory.get('session_id'):
            frontmatter['session_id'] = memory['session_id']

        # Build content
        content_parts = []
        content_parts.append('---')
        for key, value in frontmatter.items():
            if value:
                if isinstance(value, list):
                    content_parts.append(f'{key}:')
                    for item in value:
                        content_parts.append(f'  - {item}')
                else:
                    content_parts.append(f'{key}: {value}')
        content_parts.append('---')
        content_parts.append('')
        content_parts.append(memory.get('content', ''))

        markdown_content = '\n'.join(content_parts)

        exported_files.append({
            'filename': filename,
            'title': title,
            'content': markdown_content,
            'memory_id': memory['id'],
            'type': memory.get('memory_type', 'note')
        })

    return {
        'success': True,
        'total': len(exported_files),
        'files': exported_files,
        'message': f'Exported {len(exported_files)} memories'
    }
