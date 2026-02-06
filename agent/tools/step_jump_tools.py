"""Tools for controlling step flow in AI agent execution."""

import json
from typing import Callable

from ..step_jump_controller import StepJumpController
from .base import ToolBase


class StepJumpTools(ToolBase):
    """Tools for jumping to or calling other workflow steps."""

    def __init__(self, controller: StepJumpController, current_step: str):
        """
        Initialize step jump tools.

        Args:
            controller: StepJumpController instance
            current_step: Name of the step these tools are registered to
        """
        self._controller = controller
        self._current_step = current_step

    def get_definitions(self) -> list[dict]:
        """Get tool definitions in OpenAI function format."""
        valid_destinations = self._controller.get_valid_destinations(self._current_step)

        if not valid_destinations:
            return []

        return [
            {
                "type": "function",
                "function": {
                    "name": "jump_to_step",
                    "description": (
                        "Jump to another workflow step. Execution will NOT return to the current step. "
                        f"Valid destinations: {valid_destinations}"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "step_name": {
                                "type": "string",
                                "description": "Name of the step to jump to",
                                "enum": valid_destinations,
                            }
                        },
                        "required": ["step_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "call_step",
                    "description": (
                        "Call another workflow step. After it completes, execution returns to the current step. "
                        f"Valid destinations: {valid_destinations}"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "step_name": {
                                "type": "string",
                                "description": "Name of the step to call",
                                "enum": valid_destinations,
                            }
                        },
                        "required": ["step_name"],
                    },
                },
            },
        ]

    def get_functions(self) -> dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "jump_to_step": self._tool_jump_to_step,
            "call_step": self._tool_call_step,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for step jump tools."""
        valid_destinations = self._controller.get_valid_destinations(self._current_step)
        if not valid_destinations:
            return ""

        return f"""
### Step Flow Control Tools

1. **jump_to_step** - Jump to another step (no return)
   - Use when you're done and want to hand off to another step
   - Valid destinations: {valid_destinations}

2. **call_step** - Call another step and return
   - Use when you want another step to run, then continue your work
   - Valid destinations: {valid_destinations}
"""

    def _tool_jump_to_step(self, step_name: str) -> str:
        """Jump to another step without returning."""
        success, message = self._controller.request_jump(self._current_step, step_name)
        return json.dumps({"success": success, "message": message})

    def _tool_call_step(self, step_name: str) -> str:
        """Call another step and return after it completes."""
        success, message = self._controller.request_call(self._current_step, step_name)
        return json.dumps({"success": success, "message": message})
