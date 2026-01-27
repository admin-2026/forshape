"""
Base class for user input providers.

This module defines the abstract base class that all user input providers must implement,
following the same pattern as ToolBase for tool providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .wait_manager import WaitManager


@dataclass
class UserInputRequest:
    """Represents a request for user input."""
    type_id: str
    data: Dict[str, Any]
    request_id: str = ""


@dataclass
class UserInputResponse:
    """Response to a user input request."""
    request_id: str
    cancelled: bool = False
    data: Any = None  # Response payload (type depends on input type)


class UserInputBase(ABC):
    """
    Abstract base class for user input providers.

    User input providers handle specific types of user interactions.
    They can be registered with the WaitManager to extend its capabilities.
    """

    def __init__(self):
        """Initialize the provider with no manager reference."""
        self._manager: Optional["WaitManager"] = None

    def set_manager(self, manager: "WaitManager") -> None:
        """
        Set the WaitManager reference for this provider.

        Called by WaitManager.register_provider().

        Args:
            manager: The WaitManager instance
        """
        self._manager = manager

    def _do_request(self, data: Dict[str, Any]) -> UserInputResponse:
        """
        Execute a request through the manager.

        Args:
            data: Request data dictionary

        Returns:
            UserInputResponse from the user

        Raises:
            RuntimeError: If provider is not registered with a manager
        """
        if self._manager is None:
            raise RuntimeError(f"Provider '{self.type_id}' is not registered with a WaitManager")
        return self._manager.request(self.type_id, data)

    @property
    @abstractmethod
    def type_id(self) -> str:
        """
        Get the unique identifier for this input type.

        Returns:
            String identifier (e.g., "clarification", "permission", "confirmation")
        """
        pass

    def validate_request_data(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Validate request data before sending to GUI.

        Args:
            data: Request data dictionary

        Returns:
            Error message if validation fails, None if valid
        """
        return None

    def validate_response_data(self, data: Any) -> Optional[str]:
        """
        Validate response data received from GUI.

        Args:
            data: Response data

        Returns:
            Error message if validation fails, None if valid
        """
        return None

    def create_request(self, data: Dict[str, Any], request_id: str = "") -> UserInputRequest:
        """
        Create a UserInputRequest with this provider's type_id.

        Args:
            data: Request-specific data
            request_id: Optional request ID

        Returns:
            UserInputRequest instance
        """
        return UserInputRequest(
            type_id=self.type_id,
            data=data,
            request_id=request_id
        )
