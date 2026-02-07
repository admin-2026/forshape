"""
Base widget utilities for ForShape AI GUI.

This module provides shared widget creation and sizing utilities
used by MessageWidget and WelcomeWidget.
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QTextBrowser


class WidgetBase:
    """Base class providing widget creation utilities."""

    DEFAULT_STYLESHEET = """
        p {
            margin: 0;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 3px;
            font-family: Consolas, monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        code {
            background-color: #f0f0f0;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: Consolas, monospace;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        div {
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        strong { font-weight: bold; }
        em { font-style: italic; }
    """

    @staticmethod
    def create_widget(html_content: str, viewport_width: int) -> QTextBrowser:
        """
        Create a QTextBrowser widget for displaying a single message.

        Args:
            html_content: HTML content to display
            viewport_width: Width of the parent viewport in pixels

        Returns:
            Configured QTextBrowser widget
        """
        widget = QTextBrowser()
        widget.setFont(QFont("Consolas", 10))
        widget.setReadOnly(True)
        widget.setOpenExternalLinks(True)
        widget.setFrameShape(QTextBrowser.NoFrame)

        # Disable border line. Comment them out to help debug GUI issue
        widget.setLineWidth(0)
        widget.setStyleSheet("QTextBrowser { border: none; }")

        # Disable scrollbars - the parent QListWidget handles scrolling
        widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Enable text selection
        widget.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )
        # Remove internal margins/padding
        widget.setContentsMargins(0, 0, 0, 0)
        widget.document().setDocumentMargin(0)
        # Set stylesheet for markdown rendering
        widget.document().setDefaultStyleSheet(WidgetBase.DEFAULT_STYLESHEET)
        # Set the HTML content
        widget.setHtml(html_content)
        # Calculate appropriate height based on content
        widget.document().setTextWidth(viewport_width - 20)
        doc_height = int(widget.document().size().height()) + 5  # Add buffer for full visibility
        widget.setFixedHeight(doc_height)
        return widget

    @staticmethod
    def update_widget_size(widget: QTextBrowser, viewport_width: int):
        """Update widget size based on current viewport width."""
        widget.document().setDocumentMargin(0)
        widget.document().setTextWidth(viewport_width - 20)
        doc_height = int(widget.document().size().height()) + 5  # Add buffer for full visibility
        widget.setFixedHeight(doc_height)
