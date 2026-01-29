"""
Message element base class.

This module provides the MessageElement abstract base class
for elements that can produce API message dicts.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class MessageElement(ABC):
    """Base class for elements that produce API message dicts."""

    @abstractmethod
    def get_message(self) -> Optional[Dict[str, Any]]:
        """
        Get the message dict for this element.

        Returns:
            Message dict ready for API call with 'role' and 'content' keys,
            or None if the data is invalid or empty.
        """
        pass
