"""
Welcome widget for ForShape AI GUI.

This module provides the welcome message widget displayed at the start of conversations.
"""

from PySide2.QtCore import QSize
from PySide2.QtWidgets import QListWidgetItem

from .widget_base import WidgetBase


class WelcomeWidget(WidgetBase):
    """Handles welcome message display and updates."""

    def __init__(self, get_ai_client, config):
        """
        Initialize the welcome widget.

        Args:
            get_ai_client: Callable that returns the current AIAgent instance (or None)
            config: The ConfigurationManager instance
        """
        self.get_ai_client = get_ai_client
        self.config = config
        self.msg_id = None

    def generate_html(self) -> str:
        """
        Generate the welcome message HTML.

        Returns:
            HTML string for the welcome message
        """
        ai_client = self.get_ai_client()
        ai_client_ready = ai_client is not None
        has_forshape = self.config.has_forshape()
        model_name = ai_client.get_model() if ai_client else None

        if has_forshape:
            context_info = "<strong>Context:</strong> ✓ FORSHAPE.md loaded"
        else:
            context_info = (
                "<strong>Context:</strong> ✗ No FORSHAPE.md<br>"
                "<strong>Hint:</strong> Place a FORSHAPE.md file in your working directory "
                "to provide custom instructions and context to the AI."
            )

        if ai_client_ready:
            model_info = f"<strong>Using model:</strong> {model_name}<br>"
            start_message = "Start chatting to generate 3D shapes!"
        else:
            model_info = ""
            start_message = "Please complete the setup steps below to begin."

        return f"""
<div style="font-family: Consolas, monospace; margin: 0;">
<pre style="margin: 0;">{"=" * 60}
Welcome to ForShape AI - Interactive 3D Shape Generator
{"=" * 60}</pre>
<p style="margin: 0;">{model_info}{context_info}</p>
<p style="margin: 0;"><strong>Tip:</strong> Drag & drop images or .py files to attach them to your messages</p>
<p style="margin: 0;">{start_message}</p>
<pre style="margin: 0;">{"=" * 60}</pre>
</div>
"""

    def create(self, conversation_display):
        """
        Create the welcome message widget and list item.

        Args:
            conversation_display: The QListWidget for conversation display

        Returns:
            Tuple of (QTextBrowser widget, QListWidgetItem)
        """
        self._conversation_display = conversation_display
        welcome_html = self.generate_html()
        viewport_width = conversation_display.viewport().width()
        self._widget = self.create_widget(welcome_html, viewport_width)
        self._item = QListWidgetItem()
        self._item.setSizeHint(QSize(viewport_width, self._widget.height()))
        return self._widget, self._item

    def refresh(self):
        """Regenerate the welcome HTML and update the displayed widget."""
        if not hasattr(self, "_widget") or self._widget is None:
            return
        welcome_html = self.generate_html()
        self._widget.setHtml(welcome_html)
        viewport_width = self._conversation_display.viewport().width()
        self.update_widget_size(self._widget, viewport_width)
        self._item.setSizeHint(QSize(viewport_width, self._widget.height()))
