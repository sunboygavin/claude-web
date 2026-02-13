"""
MCP server lifecycle management.
Manages multiple MCP server connections.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from mcp.client import MCPClient
from mcp.transport import create_transport
from mcp_database import get_mcp_servers, get_credentials, update_server_status


logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages multiple MCP server connections."""

    _instance = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize manager."""
        if self._initialized:
            return

        self.clients: Dict[int, MCPClient] = {}  # server_id -> client
        self.server_names: Dict[str, int] = {}  # server_name -> server_id
        self.loop = None
        self._initialized = True

    def _get_or_create_loop(self):
        """Get or create event loop."""
        if self.loop is None or self.loop.is_closed():
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        return self.loop

    async def _start_server(self, server_config: Dict[str, Any]) -> bool:
        """
        Start a single MCP server.

        Args:
            server_config: Server configuration from database

        Returns:
            True if started successfully
        """
        server_id = server_config['id']
        server_name = server_config['name']

        try:
            # Get credentials
            credentials = get_credentials(server_id)

            # Merge credentials into environment
            env = server_config.get('env') or {}
            env.update(credentials)

            # Create transport
            transport = create_transport(
                server_type=server_config['server_type'],
                command=server_config.get('command'),
                args=server_config.get('args'),
                env=env,
                url=server_config.get('url')
            )

            # Create and connect client
            client = MCPClient(transport, server_name)
            await client.connect()

            # Store client
            self.clients[server_id] = client
            self.server_names[server_name] = server_id

            # Update status
            tools = [tool['name'] for tool in client.tools]
            update_server_status(server_id, 'connected', tools)

            logger.info(f"Started MCP server: {server_name} ({len(tools)} tools)")
            return True

        except Exception as e:
            logger.error(f"Failed to start MCP server {server_name}: {e}")
            update_server_status(server_id, 'error', error_message=str(e))
            return False

    async def _stop_server(self, server_id: int):
        """Stop a single MCP server."""
        if server_id in self.clients:
            client = self.clients[server_id]
            await client.close()
            del self.clients[server_id]

            # Remove from name mapping
            for name, sid in list(self.server_names.items()):
                if sid == server_id:
                    del self.server_names[name]
                    break

            update_server_status(server_id, 'disconnected')

    def start_all_servers(self):
        """Start all enabled MCP servers."""
        loop = self._get_or_create_loop()

        servers = get_mcp_servers(enabled_only=True)

        async def start_all():
            tasks = [self._start_server(server) for server in servers]
            await asyncio.gather(*tasks, return_exceptions=True)

        if loop.is_running():
            # If loop is already running, schedule the coroutine
            asyncio.create_task(start_all())
        else:
            # Run in the loop
            loop.run_until_complete(start_all())

    def stop_all_servers(self):
        """Stop all MCP servers."""
        loop = self._get_or_create_loop()

        async def stop_all():
            tasks = [self._stop_server(sid) for sid in list(self.clients.keys())]
            await asyncio.gather(*tasks, return_exceptions=True)

        if loop.is_running():
            asyncio.create_task(stop_all())
        else:
            loop.run_until_complete(stop_all())

    def restart_server(self, server_id: int) -> bool:
        """Restart a specific MCP server."""
        loop = self._get_or_create_loop()

        async def restart():
            await self._stop_server(server_id)
            from mcp_database import get_mcp_server
            server_config = get_mcp_server(server_id)
            if server_config and server_config['enabled']:
                return await self._start_server(server_config)
            return False

        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(restart(), loop)
            return future.result(timeout=30)
        else:
            return loop.run_until_complete(restart())

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from all connected servers."""
        all_tools = []

        for client in self.clients.values():
            all_tools.extend(client.get_tool_definitions())

        return all_tools

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool.

        Args:
            tool_name: Tool name in format "server:tool"
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if ':' not in tool_name:
            raise ValueError(f"Invalid MCP tool name: {tool_name}")

        server_name, actual_tool_name = tool_name.split(':', 1)

        if server_name not in self.server_names:
            raise ValueError(f"MCP server not found: {server_name}")

        server_id = self.server_names[server_name]
        client = self.clients.get(server_id)

        if not client:
            raise RuntimeError(f"MCP server not connected: {server_name}")

        loop = self._get_or_create_loop()

        async def call():
            return await client.call_tool(actual_tool_name, arguments)

        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(call(), loop)
            return future.result(timeout=60)
        else:
            return loop.run_until_complete(call())

    def is_mcp_tool(self, tool_name: str) -> bool:
        """Check if a tool name is an MCP tool."""
        return ':' in tool_name

    def get_server_status(self) -> Dict[str, str]:
        """Get status of all servers."""
        status = {}
        for server_name, server_id in self.server_names.items():
            if server_id in self.clients:
                status[server_name] = 'connected'
            else:
                status[server_name] = 'disconnected'
        return status


# Global instance
_manager = None


def get_mcp_manager() -> MCPServerManager:
    """Get the global MCP manager instance."""
    global _manager
    if _manager is None:
        _manager = MCPServerManager()
    return _manager
