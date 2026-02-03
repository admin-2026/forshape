"""
Bridge connecting agent's WaitManager to GUI dialogs.

This module handles the Qt signal emission to ensure dialogs
are shown on the main thread. Provides paired registration of
providers and handlers for simplified setup.
"""

from typing import TYPE_CHECKING, Dict, Optional

from PySide2.QtCore import QObject, Signal

from agent.async_ops import UserInputBase, UserInputRequest, UserInputResponse, WaitManager

if TYPE_CHECKING:
    from .user_input import GuiInputHandlerBase


class UserInputBridge(QObject):
    """
    Bridges the agent's WaitManager to GUI dialogs.

    Receives requests from any thread, emits a generic signal to trigger
    dialog display on the main thread, and sends responses back to the manager.

    Provides paired registration - use register_input_type() to register
    both provider and handler together, ensuring type_id matching.
    """

    # Generic signal for all input types
    # Passes the full request object so slots have all context
    input_requested = Signal(object)  # UserInputRequest

    def __init__(self, wait_manager: WaitManager, parent=None, logger=None):
        """
        Initialize the bridge.

        Args:
            wait_manager: The WaitManager to bridge to GUI
            parent: Optional Qt parent object (also used as dialog parent)
            logger: Optional logger instance for handlers
        """
        super().__init__(parent)
        self._manager = wait_manager
        self._parent = parent
        self._logger = logger
        self._handlers: Dict[str, GuiInputHandlerBase] = {}

        # Register as the handler for user input requests
        self._manager.set_handler(self._handle_request)

        # Connect the generic signal to dispatch handler
        self.input_requested.connect(self._dispatch_request)

    def register_input_type(self, provider: UserInputBase, handler: "GuiInputHandlerBase") -> None:
        """
        Register a provider/handler pair for a user input type.

        This is the primary registration method. It:
        - Validates that provider and handler have matching type_ids
        - Registers the provider with the WaitManager
        - Stores the handler and configures it with bridge/parent/logger

        Args:
            provider: The agent-side UserInputBase provider
            handler: The GUI-side GuiInputHandlerBase handler

        Raises:
            ValueError: If type_ids don't match
        """
        if provider.type_id != handler.type_id:
            raise ValueError(f"type_id mismatch: provider has '{provider.type_id}', handler has '{handler.type_id}'")

        # Register provider with wait manager
        self._manager.register_provider(provider)

        # Configure and store handler
        handler.set_bridge(self)
        if self._parent is not None:
            handler.set_parent(self._parent)
        if self._logger is not None:
            handler.set_logger(self._logger)
        self._handlers[handler.type_id] = handler

    def get_handler(self, type_id: str) -> Optional["GuiInputHandlerBase"]:
        """
        Get a handler by type_id.

        Args:
            type_id: The type identifier

        Returns:
            GuiInputHandlerBase instance or None if not found
        """
        return self._handlers.get(type_id)

    def _handle_request(self, request: UserInputRequest) -> None:
        """
        Handle incoming user input request from agent.

        Emits a signal to ensure processing happens on the main thread.

        Args:
            request: The user input request to handle
        """
        self.input_requested.emit(request)

    def _dispatch_request(self, request: UserInputRequest) -> None:
        """
        Dispatch request to the appropriate handler.

        Called on the main thread via the signal.

        Args:
            request: The user input request to dispatch
        """
        handler = self._handlers.get(request.type_id)
        if handler is not None:
            handler.handle(request)
        else:
            # Unknown type - send cancelled response
            self.send_response(request.request_id, cancelled=True)

    def send_response(self, request_id: str, data=None, cancelled: bool = False) -> None:
        """
        Send response back to the manager.

        Call this from dialog handlers after user provides input.

        Args:
            request_id: ID of the request being responded to
            data: Response payload (type depends on request type)
            cancelled: Whether user cancelled the dialog
        """
        response = UserInputResponse(request_id=request_id, cancelled=cancelled, data=data)
        self._manager.set_response(response)
