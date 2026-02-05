"""
Conversation view components for ForShape AI GUI.

This package contains widgets for the conversation display area.
"""

from .agent_progress_widget import AgentProgressWidget
from .conversation_view import ConversationView
from .message_widget import MessageWidget
from .welcome_widget import WelcomeWidget
from .widget_base import WidgetBase

__all__ = [
    "AgentProgressWidget",
    "ConversationView",
    "MessageWidget",
    "WelcomeWidget",
    "WidgetBase",
]
