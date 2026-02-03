"""
Request builder for ForShape AI agent.

This module builds requests for AI interactions by combining:
- System message from a list of RequestElement objects
- User message from a list of RequestElement objects
- Message elements for multimodal messages
"""

from typing import Any, Optional

from .message_element import MessageElement
from .request_element import RequestElement
from .text_message import TextMessage


class RequestBuilder:
    """Builds context and messages for AI requests."""

    def __init__(self, system_elements: list[RequestElement], user_elements: list[RequestElement]):
        """
        Initialize the request builder.

        Args:
            system_elements: List of RequestElement objects for building the system message
            user_elements: List of RequestElement objects for building the user message context
        """
        self._base_system_elements = system_elements
        self._base_user_elements = user_elements

    def _concatenate_elements(self, elements: list[RequestElement]) -> str:
        """
        Concatenate description and content from a list of RequestElement objects.

        Args:
            elements: List of RequestElement objects

        Returns:
            Concatenated content string with elements separated by newlines.
            Each element includes its description (if present) followed by its content.
        """
        parts = []
        for element in elements:
            content = element.get_content()
            if content:
                description = element.get_description()
                if description:
                    parts.append(f"# {description}\n\n{content}")
                else:
                    parts.append(content)
        return "\n\n".join(parts)

    def build_messages(
        self,
        history: list[dict[str, Any]],
        init_elements: list[RequestElement],
        message_elements: Optional[list[MessageElement]] = None,
    ) -> list[dict]:
        """
        Build complete message list for OpenAI API call.

        Combines system message, conversation history, and user message into
        a single list ready for the API.

        Args:
            history: List of message dicts with 'role' and 'content' keys
            init_elements: List of RequestElement objects containing the user's initial message/request
            message_elements: Optional list of MessageElement objects for additional content
                              (e.g., images with descriptions). These are appended after the
                              init user message.

        Returns:
            List of messages formatted for OpenAI API
        """
        messages = []

        # Build and add system message from system elements
        system_message = self._concatenate_elements(self._base_system_elements)
        if system_message:
            messages.append(TextMessage("system", system_message).get_message())

        # Add conversation history
        messages.extend(history)

        # Add init user message
        user_content = self._concatenate_elements(self._base_user_elements + init_elements)
        messages.append(TextMessage("user", user_content).get_message())

        # Add any additional message elements (e.g., images with descriptions)
        if message_elements:
            for element in message_elements:
                messages.append(element.get_message())

        return messages
