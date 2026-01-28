"""
Request builder for ForShape AI agent.

This module builds requests for AI interactions by combining:
- System message from a list of RequestElement objects
- User message from a list of RequestElement objects
- Image handling for multimodal messages
"""

from typing import Optional, Tuple, Dict, List

from .request_element import RequestElement


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

    def build_request(self, init_element: RequestElement) -> Tuple[str, str]:
        """
        Build the system message and augmented user input for an AI request.

        The user message is augmented with user context if available.

        Args:
            init_element: RequestElement containing the user's initial message/request

        Returns:
            Tuple of (system_message, user_context)
            - system_message: Built from system elements
            - user_context: User message augmented with user context
        """
        # Get system message and user context
        system_message = self._concatenate_elements(self._base_system_elements)
        user_context = self._concatenate_elements(self._base_user_elements+[init_element])

        return system_message, user_context

    # ========== Image Message Building ==========

    @staticmethod
    def create_image_url_content(base64_image: str) -> Dict:
        """
        Create an image_url content object for OpenAI messages.

        Args:
            base64_image: Base64-encoded image string

        Returns:
            Image URL content dict
        """
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
                "detail": "high"
            }
        }

    @staticmethod
    def create_image_message(text: str, base64_image: str) -> Dict:
        """
        Create an OpenAI message with both text and image content.

        Args:
            text: The text content to include with the image
            base64_image: Base64-encoded image string

        Returns:
            Message dict with text and image_url content
        """
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                RequestBuilder.create_image_url_content(base64_image)
            ]
        }

    @staticmethod
    def create_multi_image_message(text: str, base64_images: List[str]) -> Dict:
        """
        Create an OpenAI message with text and multiple image content.

        Args:
            text: The text content to include with the images
            base64_images: List of base64-encoded image strings

        Returns:
            Message dict with text and multiple image_url content
        """
        content = [
            {
                "type": "text",
                "text": text
            }
        ]

        # Add all images to the content array
        for base64_image in base64_images:
            content.append(RequestBuilder.create_image_url_content(base64_image))

        return {
            "role": "user",
            "content": content
        }

    def build_user_message(self, text: str, image_data: Optional[Dict] = None) -> Dict:
        """
        Build a complete user message, handling optional image data.

        Args:
            text: The text content of the message
            image_data: Optional dict or list of dicts containing captured image data

        Returns:
            Message dict ready for API call
        """
        if not image_data:
            return {"role": "user", "content": text}

        # Handle both single image (dict) and multiple images (list)
        images_list = image_data if isinstance(image_data, list) else [image_data]

        # Filter valid images
        valid_images = []
        for img in images_list:
            if img and img.get("success"):
                base64_image = img.get("image_base64")
                if base64_image and not base64_image.startswith("Error"):
                    valid_images.append(base64_image)

        # Create message with text and image(s)
        if valid_images:
            return self.create_multi_image_message(text, valid_images)
        else:
            # No valid images, just send text
            return {"role": "user", "content": text}
