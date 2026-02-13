"""
Transport layer for MCP communication.
Supports stdio, SSE, and HTTP transports.
"""

import asyncio
import json
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import aiohttp


class MCPTransport(ABC):
    """Abstract base class for MCP transports."""

    @abstractmethod
    async def connect(self):
        """Establish connection."""
        pass

    @abstractmethod
    async def send(self, message: Dict[str, Any]):
        """Send a message."""
        pass

    @abstractmethod
    async def receive(self) -> Dict[str, Any]:
        """Receive a message."""
        pass

    @abstractmethod
    async def close(self):
        """Close connection."""
        pass


class StdioTransport(MCPTransport):
    """Transport for local process communication via stdin/stdout."""

    def __init__(self, command: str, args: list = None, env: Dict[str, str] = None):
        """
        Initialize stdio transport.

        Args:
            command: Command to execute
            args: Command arguments
            env: Environment variables
        """
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.process = None
        self.connected = False

    async def connect(self):
        """Start the process."""
        import os
        full_env = os.environ.copy()
        full_env.update(self.env)

        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=full_env
        )
        self.connected = True

    async def send(self, message: Dict[str, Any]):
        """Send a JSON message to the process."""
        if not self.connected or not self.process:
            raise RuntimeError("Not connected")

        json_str = json.dumps(message) + '\n'
        self.process.stdin.write(json_str.encode())
        await self.process.stdin.drain()

    async def receive(self) -> Dict[str, Any]:
        """Receive a JSON message from the process."""
        if not self.connected or not self.process:
            raise RuntimeError("Not connected")

        line = await self.process.stdout.readline()
        if not line:
            raise EOFError("Process closed")

        return json.loads(line.decode())

    async def close(self):
        """Terminate the process."""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            self.connected = False


class SSETransport(MCPTransport):
    """Transport for Server-Sent Events."""

    def __init__(self, url: str, headers: Dict[str, str] = None):
        """
        Initialize SSE transport.

        Args:
            url: SSE endpoint URL
            headers: HTTP headers
        """
        self.url = url
        self.headers = headers or {}
        self.session = None
        self.response = None
        self.connected = False

    async def connect(self):
        """Connect to SSE endpoint."""
        self.session = aiohttp.ClientSession()
        self.response = await self.session.get(self.url, headers=self.headers)
        self.connected = True

    async def send(self, message: Dict[str, Any]):
        """SSE is read-only, use HTTP POST for sending."""
        raise NotImplementedError("SSE transport is read-only")

    async def receive(self) -> Dict[str, Any]:
        """Receive an SSE event."""
        if not self.connected or not self.response:
            raise RuntimeError("Not connected")

        async for line in self.response.content:
            line = line.decode().strip()
            if line.startswith('data: '):
                data = line[6:]  # Remove 'data: ' prefix
                return json.loads(data)

        raise EOFError("SSE stream closed")

    async def close(self):
        """Close SSE connection."""
        if self.response:
            self.response.close()
        if self.session:
            await self.session.close()
        self.connected = False


class HTTPTransport(MCPTransport):
    """Transport for HTTP/REST API communication."""

    def __init__(self, base_url: str, headers: Dict[str, str] = None):
        """
        Initialize HTTP transport.

        Args:
            base_url: Base URL for API
            headers: HTTP headers
        """
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.session = None
        self.connected = False

    async def connect(self):
        """Create HTTP session."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        self.connected = True

    async def send(self, message: Dict[str, Any]):
        """Send HTTP POST request."""
        if not self.connected or not self.session:
            raise RuntimeError("Not connected")

        async with self.session.post(
            f"{self.base_url}/messages",
            json=message
        ) as response:
            response.raise_for_status()

    async def receive(self) -> Dict[str, Any]:
        """Receive HTTP response."""
        if not self.connected or not self.session:
            raise RuntimeError("Not connected")

        async with self.session.get(f"{self.base_url}/messages") as response:
            response.raise_for_status()
            return await response.json()

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
        self.connected = False


def create_transport(server_type: str, **kwargs) -> MCPTransport:
    """
    Factory function to create appropriate transport.

    Args:
        server_type: 'stdio', 'sse', or 'http'
        **kwargs: Transport-specific parameters

    Returns:
        MCPTransport instance
    """
    if server_type == 'stdio':
        return StdioTransport(
            command=kwargs.get('command'),
            args=kwargs.get('args'),
            env=kwargs.get('env')
        )
    elif server_type == 'sse':
        return SSETransport(
            url=kwargs.get('url'),
            headers=kwargs.get('headers')
        )
    elif server_type == 'http':
        return HTTPTransport(
            base_url=kwargs.get('url'),
            headers=kwargs.get('headers')
        )
    else:
        raise ValueError(f"Unknown transport type: {server_type}")
