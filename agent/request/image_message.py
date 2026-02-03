"""
Image message element.

This module provides the ImageMessage class for building
API messages with a description and optional image content.
"""

from typing import Any, Optional

from .message_element import MessageElement


class ImageMessage(MessageElement):
    """Message element that handles a description with optional images."""

    def __init__(self, description: str, image_data: Optional[dict] = None):
        """
        Initialize the image message.

        Args:
            description: A description for the images (e.g., "Here is the reference image")
            image_data: Optional dict or list of dicts containing captured image data.
                        Supported formats:
                        - Single image: {"success": True, "image_base64": "..."}
                        - List of images: [{"success": True, "image_base64": "..."}, ...]
                        - Labeled images: {"front": {"image_base64": "..."}, "top": {"image_base64": "..."}}
        """
        self._description = description
        self._image_data = image_data

    def get_message(self) -> Optional[dict[str, Any]]:
        """
        Build a complete user message, handling optional image data.

        Returns:
            Message dict ready for API call, or None if image data is empty or invalid
        """
        if not self._image_data:
            return None

        # Check if this is a labeled images dict (dict-of-dicts format)
        if self._is_labeled_images():
            return self._create_labeled_images_message()

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

    def _is_labeled_images(self) -> bool:
        """
        Check if image_data is in labeled format (dict-of-dicts).

        Returns:
            True if image_data is a dict where values are dicts with image_base64
        """
        if not isinstance(self._image_data, dict):
            return False

        # If it has 'success' or 'image_base64' at top level, it's a single image
        if "success" in self._image_data or "image_base64" in self._image_data:
            return False

        # Check if any value is a dict with image_base64
        for value in self._image_data.values():
            if isinstance(value, dict) and "image_base64" in value:
                return True

        return False

    def _create_labeled_images_message(self) -> Optional[dict[str, Any]]:
        """
        Create a message with labeled images (e.g., perspective views).

        Returns:
            Message dict with description and labeled images, or None if no valid images
        """
        content = [{"type": "text", "text": self._description}]

        for label, image_data in self._image_data.items():
            base64_image = image_data.get("image_base64")
            if base64_image and not base64_image.startswith("Error"):
                content.append({"type": "text", "text": f"\n{label} view:"})
                content.append(self._create_image_url_content(base64_image))

        if len(content) > 1:  # More than just the description
            return {"role": "user", "content": content}

        return None

    def _create_multi_image_message(self, base64_images: list[str]) -> dict[str, Any]:
        """
        Create a message with description and multiple image content.

        Args:
            base64_images: List of base64-encoded image strings

        Returns:
            Message dict with description and multiple image_url content
        """
        content = [{"type": "text", "text": self._description}]

        # Add all images to the content array
        for base64_image in base64_images:
            content.append(self._create_image_url_content(base64_image))

        return {"role": "user", "content": content}

    @staticmethod
    def _create_image_url_content(base64_image: str) -> dict[str, Any]:
        """
        Create an image_url content object for OpenAI messages.

        Args:
            base64_image: Base64-encoded image string

        Returns:
            Image URL content dict
        """
        return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}", "detail": "high"}}
