"""
Base class for tool providers.

This module defines the abstract base class that all tool providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any

from ..request import MessageElement, ToolResultMessage


class ToolBase(ABC):
    """
    Abstract base class for tool providers.

    Tool providers encapsulate a group of related tools and their implementations.
    They can be registered with the ToolManager to extend its capabilities.
    """

    @abstractmethod
    def get_definitions(self) -> List[Dict]:
        """
        Get tool definitions in OpenAI function format.

        Returns:
            List of tool definition dictionaries
        """
        pass

    @abstractmethod
    def get_functions(self) -> Dict[str, Callable[..., str]]:
        """
        Get mapping of tool names to their implementation functions.

        Returns:
            Dictionary mapping tool names to callable implementations
        """
        pass

    def get_names(self) -> List[str]:
        """
        Get list of tool names this provider offers.

        Returns:
            List of tool name strings
        """
        return list(self.get_functions().keys())

    def get_tool_instructions(self) -> str:
        """
        Get user-facing instructions for this tool provider's tools.

        Override this method to provide detailed usage instructions and examples
        for the tools provided by this class. These instructions will be assembled
        by ToolManager and presented to the AI agent.

        Returns:
            Formatted string with tool usage instructions, or empty string if none.
        """
        return ""

    def process_result(
        self,
        tool_call_id: str,
        tool_name: str,
        tool_result: str
    ) -> List[MessageElement]:
        """
        Process a tool result and return MessageElements for the conversation.

        Override this method to customize how tool results are processed and
        formatted for the API messages. The default implementation returns a
        list with a single standard ToolResultMessage.

        Args:
            tool_call_id: The ID of the tool call
            tool_name: The name of the tool that was called
            tool_result: The result from the tool execution

        Returns:
            List of MessageElements to add to the conversation
        """
        return [ToolResultMessage(tool_call_id, tool_name, tool_result)]
