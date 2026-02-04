"""
Conversation view components for ForShape AI GUI.

This package contains widgets for the conversation display area.
"""

from .message_handler import MessageHandler
from .message_widget import MessageWidget
from .welcome_widget import WelcomeWidget
from .widget_base import WidgetBase

__all__ = [
    "MessageHandler",
    "MessageWidget",
    "WelcomeWidget",
    "WidgetBase",
]
