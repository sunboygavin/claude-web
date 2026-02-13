"""
MCP client implementation.
Handles connection, tool discovery, and tool execution.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from mcp.transport import MCPTransport


class MCPClient:
    """MCP protocol client."""

    def __init__(self, transport: MCPTransport, server_name: str):
        """
        Initialize MCP client.

        Args:
            transport: Transport layer instance
            server_name: Name of the MCP server
        """
        self.transport = transport
        self.server_name = server_name
        self.connected = False
        self.tools = []
        self.server_info = {}

    async def connect(self):
        """Establish connection and initialize."""
        await self.transport.connect()

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "claude-web",
                    "version": "1.0.0"
                }
            }
        }

        await self.transport.send(init_request)
        response = await self.transport.receive()

        if "error" in response:
            raise RuntimeError(f"Initialize failed: {response['error']}")

        self.server_info = response.get("result", {})
        self.connected = True

        # Discover tools
        await self.discover_tools()

    async def discover_tools(self):
        """Discover available tools from the server."""
        tools_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }

        await self.transport.send(tools_request)
        response = await self.transport.receive()

        if "error" in response:
            raise RuntimeError(f"Tool discovery failed: {response['error']}")

        self.tools = response.get("result", {}).get("tools", [])

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool call.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self.connected:
            raise RuntimeError("Not connected")

        call_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        await self.transport.send(call_request)
        response = await self.transport.receive()

        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"Tool call failed: {error.get('message', str(error))}")

        return response.get("result")

    async def get_server_info(self) -> Dict[str, Any]:
        """Get server capabilities and information."""
        return self.server_info

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return self.tools

    async def close(self):
        """Close the connection."""
        if self.connected:
            await self.transport.close()
            self.connected = False

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions in Claude API format.

        Returns:
            List of tool definitions
        """
        claude_tools = []

        for tool in self.tools:
            # Convert MCP tool schema to Claude tool schema
            claude_tool = {
                "name": f"{self.server_name}:{tool['name']}",
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema", {
                    "type": "object",
                    "properties": {},
                    "required": []
                })
            }
            claude_tools.append(claude_tool)

        return claude_tools
