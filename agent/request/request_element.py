"""
Request element base class.

This module provides the RequestElement abstract base class
for elements that provide content and description.
"""

from abc import ABC, abstractmethod
from typing import Optional


class RequestElement(ABC):
    """Base class for request elements that provide content and description."""

    def __init__(self, description: Optional[str] = None):
        """
        Initialize the request element.

        Args:
            description: Optional description for this element
        """
        self._description = description

    @abstractmethod
    def get_content(self) -> str:
        """
        Get the content of this element.

        Returns:
            The content as a string.
        """
        pass

    def get_description(self) -> Optional[str]:
        """
        Get the description for this element.

        Returns:
            The description string, or None if not set.
        """
        return self._description
