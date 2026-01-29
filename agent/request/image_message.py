"""
Image message element.

This module provides the ImageMessage class for building
API messages with a description and optional image content.
"""

from typing import Dict, List, Optional, Any

from .message_element import MessageElement


class ImageMessage(MessageElement):
    """Message element that handles a description with optional images."""

    def __init__(self, description: str, image_data: Optional[Dict] = None):
        """
        Initialize the image message.

        Args:
            description: A description for the images (e.g., "Here is the reference image")
            image_data: Optional dict or list of dicts containing captured image data.
                        Each dict should have 'success' and 'image_base64' keys.
        """
        self._description = description
        self._image_data = image_data

    def get_message(self) -> Optional[Dict[str, Any]]:
        """
        Build a complete user message, handling optional image data.

        Returns:
            Message dict ready for API call, or None if image data is empty or invalid
        """
        if not self._image_data:
            return None

        # Handle both single image (dict) and multiple images (list)
        images_list = self._image_data if isinstance(self._image_data, list) else [self._image_data]

        # Filter valid images
        valid_images = []
        for img in images_list:
            if img and img.get("success"):
                base64_image = img.get("image_base64")
                if base64_image and not base64_image.startswith("Error"):
                    valid_images.append(base64_image)

        # Create message with description and image(s)
        if valid_images:
            return self._create_multi_image_message(valid_images)
        else:
            # No valid images
            return None

    def _create_multi_image_message(self, base64_images: List[str]) -> Dict[str, Any]:
        """
        Create a message with description and multiple image content.

        Args:
            base64_images: List of base64-encoded image strings

        Returns:
            Message dict with description and multiple image_url content
        """
        content = [
            {
                "type": "text",
                "text": self._description
            }
        ]

        # Add all images to the content array
        for base64_image in base64_images:
            content.append(self._create_image_url_content(base64_image))

        return {
            "role": "user",
            "content": content
        }

    @staticmethod
    def _create_image_url_content(base64_image: str) -> Dict[str, Any]:
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
    def create_image_url_content(base64_image: str) -> Dict[str, Any]:
        """
        Create an image_url content object for OpenAI messages.

        Public static method for external use.

        Args:
            base64_image: Base64-encoded image string

        Returns:
            Image URL content dict
        """
        return ImageMessage._create_image_url_content(base64_image)

    @staticmethod
    def create_image_message(description: str, base64_image: str) -> Dict[str, Any]:
        """
        Create an OpenAI message with both description and image content.

        Args:
            description: A description for the image
            base64_image: Base64-encoded image string

        Returns:
            Message dict with description and image_url content
        """
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": description
                },
                ImageMessage._create_image_url_content(base64_image)
            ]
        }
