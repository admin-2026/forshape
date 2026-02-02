"""
Tool call message element.

This module provides the ToolCallMessage class for building
API messages that represent assistant tool calls (without AI involvement).
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
import uuid

from .message_element import MessageElement


@dataclass
class ToolCall:
    """Represents a tool call to be executed."""
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None
    copy_result_to_response: bool = False

    def __post_init__(self):
        """Generate ID if not provided."""
        if self.id is None:
            self.id = f"call_{uuid.uuid4().hex[:24]}"


class ToolCallMessage(MessageElement):
    """
    Message element that represents an assistant message with tool calls.

    Used by ToolCallStep to create tool calls without AI involvement.
    """

    def __init__(
        self,
        tool_calls: List[ToolCall],
        content: Optional[str] = None
    ):
        """
        Initialize the tool call message.

        Args:
            tool_calls: List of ToolCall objects to execute
            content: Optional text content for the assistant message
        """
        self._tool_calls = tool_calls
        self._content = content

    def get_message(self) -> Optional[Dict[str, Any]]:
        """
        Build an assistant message dict with tool_calls.

        Returns:
            Message dict in OpenAI format with 'role', 'content', and 'tool_calls',
            or None if no tool calls are provided.
        """
        if not self._tool_calls:
            return None

        tool_calls_data = []
        for tc in self._tool_calls:
            tool_calls_data.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": self._serialize_arguments(tc.arguments)
                }
            })

        return {
            "role": "assistant",
            "content": self._content,
            "tool_calls": tool_calls_data
        }

    def get_tool_calls(self) -> List[ToolCall]:
        """
        Get the list of tool calls.

        Returns:
            List of ToolCall objects
        """
        return self._tool_calls

    def _serialize_arguments(self, arguments: Dict[str, Any]) -> str:
        """
        Serialize arguments to JSON string.

        Args:
            arguments: Dictionary of arguments

        Returns:
            JSON string representation of arguments
        """
        import json
        return json.dumps(arguments)
