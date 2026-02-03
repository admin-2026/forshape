"""
Text message element.

This module provides the TextMessage class for building
API messages with a role and text content.
"""

from typing import Any, Dict, Optional

from .message_element import MessageElement


class TextMessage(MessageElement):
    """Message element that handles simple text messages with a role."""

    def __init__(self, role: str, text: str):
        """
        Initialize the text message.

        Args:
            role: The message role (e.g., "user", "assistant", "system")
            text: The text content of the message
        """
        self._role = role
        self._text = text

    def get_message(self) -> Optional[Dict[str, Any]]:
        """
        Build a complete message dict.

        Returns:
            Message dict ready for API call with 'role' and 'content' keys,
            or None if the text is empty.
        """
        if not self._text:
            return None

        return {"role": self._role, "content": self._text}
