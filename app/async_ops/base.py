"""
Base class for GUI user input handlers.

This module defines the abstract base class that all GUI input handlers must implement.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.async_ops import UserInputRequest

    from .user_input_bridge import UserInputBridge


class GuiInputHandlerBase(ABC):
    """
    Abstract base class for GUI user input handlers.

    Handlers are responsible for showing the appropriate dialog/UI
    and sending the response back via the bridge.
    """

    def __init__(self):
        """Initialize the handler with no references."""
        self._bridge: UserInputBridge = None
        self._parent = None
        self._logger = None

    def set_bridge(self, bridge: "UserInputBridge") -> None:
        """
        Set the bridge reference for sending responses.

        Args:
            bridge: The UserInputBridge instance
        """
        self._bridge = bridge

    def set_parent(self, parent) -> None:
        """
        Set the parent widget for dialogs.

        Args:
            parent: Parent QWidget for dialog positioning
        """
        self._parent = parent

    def set_logger(self, logger) -> None:
        """
        Set the logger instance.

        Args:
            logger: Logger instance for logging
        """
        self._logger = logger

    @property
    @abstractmethod
    def type_id(self) -> str:
        """
        Return the type_id this handler handles.

        Must match the type_id of the corresponding agent/async_ops provider.

        Returns:
            String identifier (e.g., "clarification", "permission")
        """
        pass

    @abstractmethod
    def handle(self, request: "UserInputRequest") -> None:
        """
        Handle the user input request.

        Must call self._bridge.send_response() when done.

        Args:
            request: The UserInputRequest to handle
        """
        pass
