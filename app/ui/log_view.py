"""
Log view for ForShape AI GUI.

This module provides a widget for displaying formatted log messages.
"""

from PySide2.QtGui import QFont, QTextCursor
from PySide2.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class LogView:
    """Handles log message display and formatting."""

    def __init__(self):
        """Initialize the log view with its own widget."""
        self.log_widget = QWidget()
        log_layout = QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_label = QLabel("System Logs")
        log_label.setFont(QFont("Consolas", 10, QFont.Bold))
        log_layout.addWidget(log_label)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        self.log_display.setMaximumHeight(600)
        log_layout.addWidget(self.log_display)

    def get_widget(self) -> QWidget:
        """Return the log widget for adding to layouts."""
        return self.log_widget

    def on_log_message(self, level: str, message: str, timestamp: str):
        """
        Handle log messages from the logger.

        Args:
            level: Log level (DEBUG, INFO, WARN, ERROR)
            message: Log message
            timestamp: Timestamp of the log
        """
        # Color code based on log level
        color_map = {"DEBUG": "#888888", "INFO": "#0066CC", "WARN": "#FF8800", "ERROR": "#CC0000"}
        color = color_map.get(level, "#000000")

        # Format the log message with color
        formatted_log = f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span><br>'

        # Move cursor to end before inserting
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)

        # Insert HTML
        self.log_display.insertHtml(formatted_log)

        # Scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)
