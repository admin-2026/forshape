"""
Custom widgets for ForShape AI GUI.

This module provides custom widget classes used in the main window.
"""

from PySide2.QtWidgets import QTextEdit
from PySide2.QtCore import Qt


class MultiLineInputField(QTextEdit):
    """Custom QTextEdit for multi-line user input with Enter to submit."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.submit_callback = None

    def keyPressEvent(self, event):
        """Handle key press events. Enter submits, Shift+Enter adds new line."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ShiftModifier:
                # Shift+Enter: insert new line
                super().keyPressEvent(event)
            else:
                # Plain Enter: submit
                if self.submit_callback:
                    self.submit_callback()
                event.accept()
        else:
            super().keyPressEvent(event)
