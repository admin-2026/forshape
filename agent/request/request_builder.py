"""
Request builder for ForShape AI agent.

This module builds requests for AI interactions by combining:
- System message from a list of RequestElement objects
- User message from a list of RequestElement objects
- Message elements for multimodal messages
"""

from typing import Optional, Dict, List, Any

from .request_element import RequestElement
from .message_element import MessageElement
from .image_message import ImageMessage
from .text_message import TextMessage


class RequestBuilder:
    """Builds context and messages for AI requests."""

    def __init__(
        self,
        system_elements: List[RequestElement],
        user_elements: List[RequestElement]
    ):
        """
        Initialize the request builder.

        Args:
            system_elements: List of RequestElement objects for building the system message
            user_elements: List of RequestElement objects for building the user message context
        """
        self._base_system_elements = system_elements
        self._base_user_elements = user_elements

    def _concatenate_elements(self, elements: List[RequestElement]) -> str:
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

    def build_messages(self, history: List[Dict[str, Any]],
                       init_elements: List[RequestElement],
                       message_elements: Optional[List[MessageElement]] = None) -> List[Dict]:
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

    def build_screenshot_messages(self, result_data: Dict) -> List[Dict]:
        """
        Build conversation messages from screenshot tool result data.

        Args:
            result_data: Parsed screenshot result dict (already verified successful)

        Returns:
            List of message dicts to append to conversation
        """
        messages = []

        # Check if we have single or multiple images
        if "image_base64" in result_data:
            # Single image
            base64_image = result_data["image_base64"]
            if base64_image and not base64_image.startswith("Error"):
                messages.append(ImageMessage.create_image_message(
                    "Here is the screenshot that was just captured:",
                    base64_image
                ))

        elif "images" in result_data:
            # Multiple images
            content = [{"type": "text", "text": "Here are the screenshots that were just captured:"}]

            for perspective, image_data in result_data["images"].items():
                base64_image = image_data.get("image_base64")
                if base64_image and not base64_image.startswith("Error"):
                    content.append({"type": "text", "text": f"\n{perspective} view:"})
                    content.append(ImageMessage.create_image_url_content(base64_image))

            if len(content) > 1:  # More than just the intro text
                messages.append({
                    "role": "user",
                    "content": content
                })

        return messages
