"""
Base class for tool providers.

This module defines the abstract base class that all tool providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any


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

    def start_conversation(self, conversation_id: str, user_request: Any = None) -> None:
        """
        Called when a new conversation starts.

        Tool providers can override this to perform setup for a new conversation.
        Default implementation does nothing.

        Args:
            conversation_id: Unique conversation ID
            user_request: Optional user request text
        """
        pass
