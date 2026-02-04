"""
Message widget for ForShape AI GUI.

This module provides the MessageWidget class for creating
formatted message displays in the conversation area.
"""


from PySide2.QtCore import QSize
from PySide2.QtWidgets import QListWidgetItem

from .widget_base import WidgetBase


class MessageWidget(WidgetBase):
    """Handles creation of individual message widgets."""

    def __init__(self, message_formatter, conversation_display):
        """
        Initialize the message widget.

        Args:
            message_formatter: MessageFormatter instance for formatting messages
            conversation_display: The QListWidget for conversation display
        """
        self.message_formatter = message_formatter
        self.conversation_display = conversation_display

    def create(self, role: str, message: str, token_data: dict = None):
        """
        Create a formatted message widget and list item.

        Args:
            role: The role (You, AI, Error, etc.)
            message: The message content (supports markdown)
            token_data: Optional dict with token usage information

        Returns:
            Tuple of (QTextBrowser widget, QListWidgetItem)
        """
        formatted_message = self.message_formatter.format_message(role, message, token_data)
        viewport_width = self.conversation_display.viewport().width()
        widget = self.create_widget(formatted_message, viewport_width)
        item = QListWidgetItem()
        item.setSizeHint(QSize(widget.width(), widget.height()))
        return widget, item
