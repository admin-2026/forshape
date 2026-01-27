"""
User interaction tools for AI Agent.

This module provides tools for interacting with the user,
such as asking clarification questions. Uses WaitManager
for GUI interaction without direct GUI dependencies.
"""

import json
from typing import Dict, List, Callable

from .base import ToolBase
from ..async_ops import WaitManager


class InteractionTools(ToolBase):
    """
    User interaction tools.

    Uses WaitManager for user interaction - no GUI dependencies.
    """

    def __init__(self, wait_manager: WaitManager):
        """
        Initialize interaction tools.

        Args:
            wait_manager: WaitManager for requesting user input
        """
        self._manager = wait_manager

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

        Uses UserInputWaiter to request input without GUI dependencies.

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

            # Request through manager (blocks until response)
            response = self._manager.clarification.request(questions)

            # Process the response
            if response.cancelled:
                return json.dumps({
                    "success": False,
                    "message": "User cancelled the clarification dialog",
                    "cancelled": True
                }, indent=2)

            return self._json_success(
                message="User provided clarification responses",
                responses=response.data.get("responses", {}) if response.data else {}
            )

        except Exception as e:
            return self._json_error(f"Error asking user clarification: {str(e)}")
