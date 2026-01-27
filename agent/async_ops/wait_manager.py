"""
Wait Manager for AI Agent user input.

This module provides a manager that orchestrates user input provider registration
and request handling. All providers are injected via register_provider().

Follows the same pattern as ToolManager for consistency.
"""

import threading
from typing import Dict, List, Optional, Callable, Any

from .base import UserInputBase, UserInputRequest, UserInputResponse


class WaitManager:
    """
    Orchestrates user input provider registration and request handling.

    All providers are injected via register_provider().
    Thread-safe: can be called from any thread.
    """

    def __init__(self):
        """Initialize the wait manager."""
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._response: Optional[UserInputResponse] = None
        self._handler: Optional[Callable[[UserInputRequest], None]] = None
        self._counter = 0

        # Provider storage
        self._providers: Dict[str, UserInputBase] = {}

    def __getattr__(self, name: str):
        """
        Allow attribute-based access to providers by type_id.

        This enables code like: wait_manager.permission.request(...)
        instead of: wait_manager.get_provider("permission").request(...)
        """
        # Avoid recursion for _providers itself
        if name == "_providers":
            raise AttributeError(name)

        providers = object.__getattribute__(self, "_providers")
        provider = providers.get(name)
        if provider is not None:
            return provider
        raise AttributeError(f"'{type(self).__name__}' has no provider '{name}'")

    def register_provider(self, provider: UserInputBase) -> None:
        """
        Register a user input provider.

        Args:
            provider: UserInputBase instance to register
        """
        provider.set_manager(self)
        self._providers[provider.type_id] = provider

    def get_provider(self, type_id: str) -> Optional[UserInputBase]:
        """
        Get a provider by type_id.

        Args:
            type_id: The type identifier

        Returns:
            UserInputBase instance or None if not found
        """
        return self._providers.get(type_id)

    def get_registered_type_ids(self) -> List[str]:
        """
        Get list of registered type IDs.

        Returns:
            List of type_id strings
        """
        return list(self._providers.keys())

    def set_handler(self, handler: Callable[[UserInputRequest], None]) -> None:
        """
        Register the handler that will process user input requests.

        The handler is responsible for showing appropriate UI and calling
        set_response() when the user provides input.

        Args:
            handler: Callback that receives UserInputRequest objects
        """
        self._handler = handler

    def request(self, type_id: str, data: Dict[str, Any]) -> UserInputResponse:
        """
        Request user input and block until response received.

        Args:
            type_id: Type of input needed
            data: Request-specific data

        Returns:
            UserInputResponse with user's input

        Raises:
            RuntimeError: If no handler is registered
            ValueError: If type_id is not registered or data validation fails
        """
        if self._handler is None:
            raise RuntimeError("No user input handler registered")

        # Get provider and validate
        provider = self._providers.get(type_id)
        if provider is None:
            raise ValueError(f"Unknown input type: {type_id}")

        # Validate request data
        error = provider.validate_request_data(data)
        if error:
            raise ValueError(f"Invalid request data for {type_id}: {error}")

        # Generate unique request ID
        with self._lock:
            self._counter += 1
            request_id = f"req_{self._counter}"

        # Reset state
        self._event.clear()
        self._response = None

        request = provider.create_request(data, request_id)

        # Invoke handler (will emit signal to main thread)
        self._handler(request)

        # Block until response is set
        self._event.wait()
        return self._response

    def set_response(self, response: UserInputResponse) -> None:
        """
        Set the response (called from GUI thread after user provides input).

        Args:
            response: The user's response
        """
        self._response = response
        self._event.set()
