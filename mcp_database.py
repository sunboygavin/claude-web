"""
Database operations for MCP server configuration and operation logging.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from mcp.security import get_encryption


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect('conversations.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_mcp_db():
    """Initialize MCP-related database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # MCP Servers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mcp_servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            server_type TEXT NOT NULL,
            command TEXT,
            args TEXT,
            env TEXT,
            url TEXT,
            config TEXT,
            enabled BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_mcp_servers_enabled
        ON mcp_servers(enabled)
    ''')

    # MCP Credentials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mcp_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            credential_type TEXT NOT NULL,
            credential_key TEXT NOT NULL,
            credential_value TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_mcp_credentials_server
        ON mcp_credentials(server_id)
    ''')

    # Operation Logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            session_id TEXT,
            operation_type TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            tool_source TEXT NOT NULL,
            mcp_server_id INTEGER,
            input_data TEXT,
            output_data TEXT,
            status TEXT NOT NULL,
            requires_permission BOOLEAN DEFAULT 0,
            permission_granted BOOLEAN,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            FOREIGN KEY (mcp_server_id) REFERENCES mcp_servers(id) ON DELETE SET NULL
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_operation_logs_username
        ON operation_logs(username)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_operation_logs_session
        ON operation_logs(session_id)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_operation_logs_status
        ON operation_logs(status)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_operation_logs_created
        ON operation_logs(created_at)
    ''')

    # MCP Server Status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mcp_server_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            last_check DATETIME DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT,
            available_tools TEXT,
            FOREIGN KEY (server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_mcp_server_status_server
        ON mcp_server_status(server_id)
    ''')

    conn.commit()
    conn.close()


# MCP Server Operations

def add_mcp_server(name: str, server_type: str, command: str = None,
                   args: List[str] = None, env: Dict[str, str] = None,
                   url: str = None, config: Dict[str, Any] = None) -> int:
    """Add a new MCP server configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO mcp_servers (name, server_type, command, args, env, url, config)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        name,
        server_type,
        command,
        json.dumps(args) if args else None,
        json.dumps(env) if env else None,
        url,
        json.dumps(config) if config else None
    ))

    server_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return server_id


def get_mcp_servers(enabled_only: bool = True) -> List[Dict]:
    """Get all MCP servers."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if enabled_only:
        cursor.execute('SELECT * FROM mcp_servers WHERE enabled = 1')
    else:
        cursor.execute('SELECT * FROM mcp_servers')

    servers = []
    for row in cursor.fetchall():
        server = dict(row)
        # Parse JSON fields
        if server['args']:
            server['args'] = json.loads(server['args'])
        if server['env']:
            server['env'] = json.loads(server['env'])
        if server['config']:
            server['config'] = json.loads(server['config'])
        servers.append(server)

    conn.close()
    return servers


def get_mcp_server(server_id: int) -> Optional[Dict]:
    """Get a specific MCP server by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM mcp_servers WHERE id = ?', (server_id,))
    row = cursor.fetchone()

    if row:
        server = dict(row)
        if server['args']:
            server['args'] = json.loads(server['args'])
        if server['env']:
            server['env'] = json.loads(server['env'])
        if server['config']:
            server['config'] = json.loads(server['config'])
        conn.close()
        return server

    conn.close()
    return None


def update_mcp_server(server_id: int, **kwargs) -> bool:
    """Update MCP server configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build update query dynamically
    fields = []
    values = []

    for key, value in kwargs.items():
        if key in ['name', 'server_type', 'command', 'url', 'enabled']:
            fields.append(f'{key} = ?')
            values.append(value)
        elif key in ['args', 'env', 'config'] and value is not None:
            fields.append(f'{key} = ?')
            values.append(json.dumps(value))

    if not fields:
        conn.close()
        return False

    fields.append('updated_at = ?')
    values.append(datetime.now().isoformat())
    values.append(server_id)

    query = f"UPDATE mcp_servers SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


def delete_mcp_server(server_id: int) -> bool:
    """Delete an MCP server."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM mcp_servers WHERE id = ?', (server_id,))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


# Credential Operations

def save_credential(server_id: int, credential_type: str,
                    credential_key: str, credential_value: str) -> int:
    """Save an encrypted credential for an MCP server."""
    encryption = get_encryption()
    encrypted_value = encryption.encrypt(credential_value)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if credential already exists
    cursor.execute('''
        SELECT id FROM mcp_credentials
        WHERE server_id = ? AND credential_key = ?
    ''', (server_id, credential_key))

    existing = cursor.fetchone()

    if existing:
        # Update existing credential
        cursor.execute('''
            UPDATE mcp_credentials
            SET credential_type = ?, credential_value = ?, updated_at = ?
            WHERE id = ?
        ''', (credential_type, encrypted_value, datetime.now().isoformat(), existing['id']))
        credential_id = existing['id']
    else:
        # Insert new credential
        cursor.execute('''
            INSERT INTO mcp_credentials
            (server_id, credential_type, credential_key, credential_value)
            VALUES (?, ?, ?, ?)
        ''', (server_id, credential_type, credential_key, encrypted_value))
        credential_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return credential_id


def get_credentials(server_id: int) -> Dict[str, str]:
    """Get decrypted credentials for an MCP server."""
    encryption = get_encryption()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT credential_key, credential_value
        FROM mcp_credentials
        WHERE server_id = ?
    ''', (server_id,))

    credentials = {}
    for row in cursor.fetchall():
        key = row['credential_key']
        encrypted_value = row['credential_value']
        credentials[key] = encryption.decrypt(encrypted_value)

    conn.close()
    return credentials


def delete_credential(server_id: int, credential_key: str) -> bool:
    """Delete a credential."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM mcp_credentials
        WHERE server_id = ? AND credential_key = ?
    ''', (server_id, credential_key))

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


# Server Status Operations

def update_server_status(server_id: int, status: str,
                         available_tools: List[str] = None,
                         error_message: str = None):
    """Update MCP server status."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete old status
    cursor.execute('DELETE FROM mcp_server_status WHERE server_id = ?', (server_id,))

    # Insert new status
    cursor.execute('''
        INSERT INTO mcp_server_status
        (server_id, status, error_message, available_tools)
        VALUES (?, ?, ?, ?)
    ''', (
        server_id,
        status,
        error_message,
        json.dumps(available_tools) if available_tools else None
    ))

    conn.commit()
    conn.close()


def get_server_status(server_id: int) -> Optional[Dict]:
    """Get MCP server status."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM mcp_server_status
        WHERE server_id = ?
        ORDER BY last_check DESC
        LIMIT 1
    ''', (server_id,))

    row = cursor.fetchone()

    if row:
        status = dict(row)
        if status['available_tools']:
            status['available_tools'] = json.loads(status['available_tools'])
        conn.close()
        return status

    conn.close()
    return None
