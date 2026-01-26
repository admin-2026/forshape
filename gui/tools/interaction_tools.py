"""
User interaction tools for AI Agent.

This module provides tools for interacting with the user,
such as asking clarification questions via GUI dialogs.
"""

import json
import threading
from typing import Dict, List, Callable, Optional, Any, TYPE_CHECKING

from agent.tools.base import ToolBase

if TYPE_CHECKING:
    from agent.tool_manager import ToolManager


class InteractionTools(ToolBase):
    """
    User interaction tools - injected into ToolManager.

    Provides: ask_user_clarification
    """

    def __init__(self, tool_manager: "ToolManager"):
        """
        Initialize interaction tools.

        Args:
            tool_manager: Parent ToolManager instance (for signal emission)
        """
        self.tool_manager = tool_manager

        # Threading primitives for clarification dialog
        self._clarification_event = threading.Event()
        self._clarification_response: Optional[Dict[str, Any]] = None

    def get_definitions(self) -> List[Dict]:
        """Get tool definitions in OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "ask_user_clarification",
                    "description": "Ask the user one or more clarification questions and collect their responses. Use this when you need user input to proceed with a task. The user will see a dialog with all questions and can provide responses for each.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "questions": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "List of questions to ask the user. Each question should be clear and specific."
                            }
                        },
                        "required": ["questions"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "ask_user_clarification": self._tool_ask_user_clarification,
        }

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _json_success(self, **kwargs) -> str:
        """Create a JSON success response."""
        response = {"success": True}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _tool_ask_user_clarification(self, questions: List[str]) -> str:
        """
        Implementation of the ask_user_clarification tool.
        Shows a dialog to ask the user clarification questions.

        This method emits a signal to request the dialog be shown on the main thread,
        then waits for the response using a threading event.

        Args:
            questions: List of questions to ask the user

        Returns:
            JSON string with user responses or error message
        """
        try:
            # Validate questions
            if not questions or not isinstance(questions, list):
                return self._json_error("questions must be a non-empty list")

            if len(questions) == 0:
                return self._json_error("At least one question is required")

            # Reset the event and response before requesting
            self._clarification_event.clear()
            self._clarification_response = None

            # Emit signal to show dialog on main thread
            self.tool_manager.clarification_requested.emit(questions)

            # Wait for the response (blocking until main thread responds)
            self._clarification_event.wait()

            # Process the response
            response = self._clarification_response
            if response is None:
                return self._json_error("No response received from clarification dialog")

            if response.get("cancelled", False):
                return json.dumps({
                    "success": False,
                    "message": "User cancelled the clarification dialog",
                    "cancelled": True
                }, indent=2)

            return self._json_success(
                message="User provided clarification responses",
                responses=response.get("responses", {})
            )

        except Exception as e:
            return self._json_error(f"Error asking user clarification: {str(e)}")

    def set_clarification_response(self, responses: Optional[Dict], cancelled: bool = False) -> None:
        """
        Set the clarification response from the main thread.

        This method should be called from the main GUI thread after the
        clarification dialog is closed.

        Args:
            responses: Dictionary of responses from the dialog, or None if cancelled
            cancelled: Whether the user cancelled the dialog
        """
        if cancelled:
            self._clarification_response = {"cancelled": True}
        else:
            self._clarification_response = {"responses": responses, "cancelled": False}
        # Signal the waiting thread that the response is ready
        self._clarification_event.set()
