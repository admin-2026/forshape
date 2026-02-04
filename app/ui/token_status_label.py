"""
Token status label widget for displaying token usage information.
"""

from PySide2.QtGui import QFont
from PySide2.QtWidgets import QLabel

from .message_formatter import MessageFormatter


class TokenStatusLabel(QLabel):
    """Label that displays token usage status during and after AI processing."""

    def __init__(self, message_formatter: MessageFormatter, parent=None):
        super().__init__("", parent)
        self.message_formatter = message_formatter
        self.setFont(QFont("Consolas", 9))
        self.setStyleSheet("color: #666; padding: 2px;")
        self.setVisible(False)

    def reset(self):
        """Reset and show the label for a new AI request."""
        self.setVisible(True)
        self.setText("Token Usage: Calculating...")
        self.setStyleSheet("color: #666; padding: 2px;")

    def update_tokens(self, token_data: dict):
        """
        Update with in-progress token usage data.

        Args:
            token_data: Dict with token usage information including iteration number
        """
        if token_data:
            token_str = self.message_formatter.format_token_data(token_data, include_iteration=True)
            self.setText(f"Token Usage ({token_str})")
            self.setStyleSheet("color: #666; padding: 2px;")

    def finalize(self, token_data: dict | None):
        """
        Show final token usage after AI response completes.

        Args:
            token_data: Optional dict with token usage information
        """
        if token_data:
            token_str = self.message_formatter.format_token_data(token_data, include_iteration=False)
            self.setText(f"Token Usage (Final: {token_str})")
            self.setStyleSheet("color: #0066CC; padding: 2px; font-weight: bold;")
        else:
            self.setText("Token Usage: N/A")
            self.setStyleSheet("color: #666; padding: 2px;")
