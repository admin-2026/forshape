"""
Instruction element.

This module provides an Instruction class for holding
instruction text content.
"""

from typing import Optional

from .request_element import RequestElement


class Instruction(RequestElement):
    """Holds instruction text content."""

    def __init__(self, instruction: str, description: Optional[str] = None):
        """
        Initialize the instruction element.

        Args:
            instruction: The instruction text content
            description: Optional description for this instruction
        """
        super().__init__(description)
        self._instruction = instruction

    def get_content(self) -> str:
        """
        Get the instruction content.

        Returns:
            The instruction text as a string.
        """
        return self._instruction
