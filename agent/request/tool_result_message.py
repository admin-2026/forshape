"""
Tool result message element.

This module provides the ToolResultMessage class for building
API messages that return tool execution results.
"""

from typing import Any, Optional

from .message_element import MessageElement


class ToolResultMessage(MessageElement):
    """Message element that handles tool execution results."""

    def __init__(self, tool_call_id: str, tool_name: str, tool_result: str):
        """
        Initialize the tool result message.

        Args:
            tool_call_id: The ID of the tool call this result responds to
            tool_name: The name of the tool that was called
            tool_result: The result content from the tool execution
        """
        self._tool_call_id = tool_call_id
        self._tool_name = tool_name
        self._tool_result = tool_result

    def get_message(self) -> Optional[dict[str, Any]]:
        """
        Build a complete tool result message dict.

        Returns:
            Message dict ready for API call with 'role', 'tool_call_id',
            'name', and 'content' keys, or None if required fields are empty.
        """
        if not self._tool_call_id or not self._tool_name:
            return None

        return {
            "role": "tool",
            "tool_call_id": self._tool_call_id,
            "name": self._tool_name,
            "content": self._tool_result,
        }
