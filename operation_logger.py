"""
Operation logging and permission management system.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import os
import re


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect('conversations.db')
    conn.row_factory = sqlite3.Row
    return conn


# Permission Rules

DESTRUCTIVE_COMMANDS = [
    r'rm\s+-rf',
    r'rm\s+.*\*',
    r'drop\s+table',
    r'drop\s+database',
    r'delete\s+from',
    r'truncate',
    r'format',
    r'mkfs',
    r'dd\s+if=',
]

# Git commands that require permission
GIT_PERMISSION_COMMANDS = [
    r'git\s+push',
    r'git\s+commit',
    r'git\s+merge',
    r'git\s+rebase',
    r'git\s+reset\s+--hard',
    r'git\s+clean',
    r'git\s+branch\s+-D',
    r'git\s+tag\s+-d',
]

WORKSPACE_PATH = '/root/claude-web'


def check_requires_permission(tool_name: str, tool_input: Dict[str, Any]) -> bool:
    """
    Check if a tool operation requires user permission.

    Args:
        tool_name: Name of the tool
        tool_input: Tool input parameters

    Returns:
        True if permission is required, False otherwise
    """
    # Disable automatic permission checks - let Claude decide when to ask
    return False


def get_operation_preview(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """
    Generate a human-readable preview of what the operation will do.

    Args:
        tool_name: Name of the tool
        tool_input: Tool input parameters

    Returns:
        Preview description string
    """
    if tool_name == 'write_file':
        file_path = tool_input.get('file_path', '')
        content = tool_input.get('content', '')
        preview = f"📝 写入文件: {file_path}\n"
        preview += f"内容长度: {len(content)} 字符\n"
        preview += f"内容预览:\n{content[:200]}{'...' if len(content) > 200 else ''}"
        return preview

    elif tool_name == 'edit_file':
        file_path = tool_input.get('file_path', '')
        old_string = tool_input.get('old_string', '')
        new_string = tool_input.get('new_string', '')
        preview = f"✏️ 编辑文件: {file_path}\n"
        preview += f"替换内容:\n旧: {old_string[:100]}{'...' if len(old_string) > 100 else ''}\n"
        preview += f"新: {new_string[:100]}{'...' if len(new_string) > 100 else ''}"
        return preview

    elif tool_name == 'bash':
        command = tool_input.get('command', '')
        description = tool_input.get('description', '')
        preview = f"💻 执行命令:\n{command}\n"
        if description:
            preview += f"说明: {description}"
        return preview

    elif tool_name == 'read_file':
        file_path = tool_input.get('file_path', '')
        return f"📖 读取文件: {file_path}"

    elif tool_name == 'glob':
        pattern = tool_input.get('pattern', '')
        path = tool_input.get('path', '.')
        return f"🔍 搜索文件: {pattern} (路径: {path})"

    elif tool_name == 'grep':
        pattern = tool_input.get('pattern', '')
        path = tool_input.get('path', '.')
        return f"🔎 搜索内容: {pattern} (路径: {path})"

    elif ':' in tool_name:
        # MCP tool
        server_name, tool = tool_name.split(':', 1)
        preview = f"🔌 MCP工具调用\n服务器: {server_name}\n工具: {tool}\n"
        preview += f"参数:\n{json.dumps(tool_input, indent=2, ensure_ascii=False)}"
        return preview

    return f"🔧 执行工具: {tool_name}\n参数: {json.dumps(tool_input, indent=2, ensure_ascii=False)}"


# Operation Logging

def log_operation(username: str, session_id: str, tool_name: str,
                  tool_input: Dict[str, Any], tool_source: str = 'direct',
                  mcp_server_id: Optional[int] = None) -> int:
    """
    Log a tool operation.

    Args:
        username: Username executing the operation
        session_id: Session ID
        tool_name: Name of the tool
        tool_input: Tool input parameters
        tool_source: 'direct' or 'mcp'
        mcp_server_id: MCP server ID if source is 'mcp'

    Returns:
        Operation log ID
    """
    requires_permission = check_requires_permission(tool_name, tool_input)
    operation_type = 'tool_call'

    # Determine operation type
    if tool_name in ['write_file', 'edit_file']:
        operation_type = 'file_write'
    elif tool_name == 'bash':
        operation_type = 'command'
    elif ':' in tool_name:
        operation_type = 'api_call'

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO operation_logs
        (username, session_id, operation_type, tool_name, tool_source,
         mcp_server_id, input_data, status, requires_permission)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        username,
        session_id,
        operation_type,
        tool_name,
        tool_source,
        mcp_server_id,
        json.dumps(tool_input),
        'pending' if requires_permission else 'completed',
        requires_permission
    ))

    log_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return log_id


def update_operation_status(log_id: int, status: str,
                            output_data: Any = None,
                            error_message: str = None,
                            permission_granted: bool = None):
    """
    Update operation log status.

    Args:
        log_id: Operation log ID
        status: New status ('pending', 'approved', 'rejected', 'completed', 'failed')
        output_data: Operation output data
        error_message: Error message if failed
        permission_granted: Whether permission was granted
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    updates = ['status = ?', 'completed_at = ?']
    values = [status, datetime.now().isoformat()]

    if output_data is not None:
        updates.append('output_data = ?')
        values.append(json.dumps(output_data) if not isinstance(output_data, str) else output_data)

    if error_message is not None:
        updates.append('error_message = ?')
        values.append(error_message)

    if permission_granted is not None:
        updates.append('permission_granted = ?')
        values.append(permission_granted)

    values.append(log_id)

    query = f"UPDATE operation_logs SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, values)

    conn.commit()
    conn.close()


def get_operation_logs(username: str = None, session_id: str = None,
                       status: str = None, limit: int = 100) -> List[Dict]:
    """
    Get operation logs.

    Args:
        username: Filter by username
        session_id: Filter by session ID
        status: Filter by status
        limit: Maximum number of logs to return

    Returns:
        List of operation log dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM operation_logs WHERE 1=1'
    params = []

    if username:
        query += ' AND username = ?'
        params.append(username)

    if session_id:
        query += ' AND session_id = ?'
        params.append(session_id)

    if status:
        query += ' AND status = ?'
        params.append(status)

    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)

    cursor.execute(query, params)

    logs = []
    for row in cursor.fetchall():
        log = dict(row)
        if log['input_data']:
            log['input_data'] = json.loads(log['input_data'])
        if log['output_data']:
            try:
                log['output_data'] = json.loads(log['output_data'])
            except:
                pass  # Keep as string if not JSON
        logs.append(log)

    conn.close()
    return logs


def get_pending_operations(username: str = None, session_id: str = None) -> List[Dict]:
    """Get operations pending permission approval."""
    return get_operation_logs(username=username, session_id=session_id, status='pending')


def grant_permission(log_id: int) -> bool:
    """Grant permission for a pending operation."""
    update_operation_status(log_id, 'approved', permission_granted=True)
    return True


def reject_permission(log_id: int, reason: str = None) -> bool:
    """Reject permission for a pending operation."""
    update_operation_status(
        log_id,
        'rejected',
        permission_granted=False,
        error_message=reason or '用户拒绝了操作'
    )
    return True


def cleanup_old_logs(days: int = 30):
    """Delete operation logs older than specified days."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

    cursor.execute('''
        DELETE FROM operation_logs
        WHERE created_at < ?
    ''', (cutoff_date,))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted


def get_operation_stats(username: str = None, session_id: str = None) -> Dict:
    """Get operation statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT status, COUNT(*) as count FROM operation_logs WHERE 1=1'
    params = []

    if username:
        query += ' AND username = ?'
        params.append(username)

    if session_id:
        query += ' AND session_id = ?'
        params.append(session_id)

    query += ' GROUP BY status'

    cursor.execute(query, params)

    stats = {
        'total': 0,
        'by_status': {}
    }

    for row in cursor.fetchall():
        status = row['status']
        count = row['count']
        stats['by_status'][status] = count
        stats['total'] += count

    conn.close()
    return stats
