"""
Agent progress widget for ForShape AI GUI.

This module provides the AgentProgressWidget class for displaying
a processing indicator during AI agent operations.
"""

from PySide2.QtCore import QSize
from PySide2.QtWidgets import QListWidgetItem

from .widget_base import WidgetBase


class AgentProgressWidget(WidgetBase):
    """Displays a processing indicator while the AI agent is working."""

    def __init__(self, message_formatter, conversation_display):
        self.message_formatter = message_formatter
        self.conversation_display = conversation_display
        self._widget = None
        self._item = None

    def create(self):
        """Create the progress widget showing "AI: Processing...".

        Returns:
            Tuple of (QTextBrowser widget, QListWidgetItem)
        """
        html = self.message_formatter.format_message("AI", "\u23f3 Processing...")
        viewport_width = self.conversation_display.viewport().width()
        self._widget = self.create_widget(html, viewport_width)
        self._item = QListWidgetItem()
        self._item.setSizeHint(QSize(viewport_width, self._widget.height()))
        return self._widget, self._item
