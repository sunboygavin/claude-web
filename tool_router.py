"""
Unified tool router that combines direct tools and MCP tools.
"""

import logging
from typing import Dict, List, Any, Optional
import tools
from mcp.manager import get_mcp_manager
from operation_logger import (
    log_operation,
    update_operation_status,
    check_requires_permission,
    get_operation_preview
)


logger = logging.getLogger(__name__)


class ToolRouter:
    """Routes tool execution between direct tools and MCP tools."""

    def __init__(self):
        """Initialize tool router."""
        self.direct_tools = tools.TOOLS
        self.mcp_manager = get_mcp_manager()

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get combined list of direct tools and MCP tools.

        Returns:
            List of tool definitions for Claude API
        """
        all_tools = []

        # Add direct tools
        all_tools.extend(self.direct_tools)

        # Add MCP tools
        try:
            mcp_tools = self.mcp_manager.get_all_tools()
            all_tools.extend(mcp_tools)
        except Exception as e:
            logger.error(f"Failed to get MCP tools: {e}")

        return all_tools

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any],
                     username: str, session_id: str,
                     auto_approve: bool = False) -> Dict[str, Any]:
        """
        Execute a tool (direct or MCP).

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            username: Username executing the tool
            session_id: Session ID
            auto_approve: Auto-approve operations (for testing)

        Returns:
            Tool execution result with status
        """
        # Determine tool source
        is_mcp = self.mcp_manager.is_mcp_tool(tool_name)
        tool_source = 'mcp' if is_mcp else 'direct'

        # Get MCP server ID if applicable
        mcp_server_id = None
        if is_mcp:
            server_name = tool_name.split(':', 1)[0]
            mcp_server_id = self.mcp_manager.server_names.get(server_name)

        # Log operation
        log_id = log_operation(
            username=username,
            session_id=session_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_source=tool_source,
            mcp_server_id=mcp_server_id
        )

        # Check if permission is required
        requires_permission = check_requires_permission(tool_name, tool_input)

        if requires_permission and not auto_approve:
            # Return pending status - user must approve
            preview = get_operation_preview(tool_name, tool_input)
            return {
                'status': 'pending_permission',
                'log_id': log_id,
                'preview': preview,
                'message': '此操作需要用户批准'
            }

        # Execute the tool
        try:
            if is_mcp:
                result = self._execute_mcp_tool(tool_name, tool_input)
            else:
                result = self._execute_direct_tool(tool_name, tool_input)

            # Update log with success
            update_operation_status(log_id, 'completed', output_data=result)

            return {
                'status': 'success',
                'log_id': log_id,
                'result': result
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")

            # Update log with error
            update_operation_status(log_id, 'failed', error_message=str(e))

            return {
                'status': 'error',
                'log_id': log_id,
                'error': str(e)
            }

    def _execute_direct_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute a direct tool."""
        return tools.execute_tool(tool_name, tool_input)

    def _execute_mcp_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute an MCP tool."""
        return self.mcp_manager.call_tool(tool_name, tool_input)

    def execute_approved_operation(self, log_id: int) -> Dict[str, Any]:
        """
        Execute a previously logged operation that has been approved.

        Args:
            log_id: Operation log ID

        Returns:
            Tool execution result
        """
        from operation_logger import get_operation_logs, update_operation_status
        import json

        # Get the operation log
        logs = get_operation_logs()
        operation = None
        for log in logs:
            if log['id'] == log_id:
                operation = log
                break

        if not operation:
            return {
                'status': 'error',
                'error': '操作未找到'
            }

        if operation['status'] != 'approved':
            return {
                'status': 'error',
                'error': '操作未被批准'
            }

        # Execute the tool
        tool_name = operation['tool_name']
        tool_input = operation['input_data']

        try:
            if self.mcp_manager.is_mcp_tool(tool_name):
                result = self._execute_mcp_tool(tool_name, tool_input)
            else:
                result = self._execute_direct_tool(tool_name, tool_input)

            # Update log with success
            update_operation_status(log_id, 'completed', output_data=result)

            return {
                'status': 'success',
                'log_id': log_id,
                'result': result
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")

            # Update log with error
            update_operation_status(log_id, 'failed', error_message=str(e))

            return {
                'status': 'error',
                'log_id': log_id,
                'error': str(e)
            }

    def refresh_mcp_tools(self):
        """Refresh tools from MCP servers."""
        self.mcp_manager.start_all_servers()


# Global instance
_router = None


def get_tool_router() -> ToolRouter:
    """Get the global tool router instance."""
    global _router
    if _router is None:
        _router = ToolRouter()
    return _router
