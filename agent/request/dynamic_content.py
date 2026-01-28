"""
Dynamic content element.

This module provides a DynamicContent class for holding
content that is generated dynamically via a callable.
"""

from typing import Callable, Optional

from .request_element import RequestElement


class DynamicContent(RequestElement):
    """Holds dynamically generated content via a callable."""

    def __init__(self, content_provider: Callable[[], str], description: Optional[str] = None):
        """
        Initialize the dynamic content element.

        Args:
            content_provider: A callable that returns the content string when invoked
            description: Optional description for this element
        """
        super().__init__(description)
        self._content_provider = content_provider

    def get_content(self) -> str:
        """
        Get the dynamic content by invoking the content provider.

        Returns:
            The content as a string.
        """
        return self._content_provider()
