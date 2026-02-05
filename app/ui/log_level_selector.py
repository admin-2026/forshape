"""
Log level selector UI component.

This module provides a combo box widget for selecting log levels.
"""

from PySide2.QtGui import QFont
from PySide2.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget, QWidgetAction

from ..logger import LogLevel


class LogLevelSelector(QWidget):
    """A widget containing a label and combo box for selecting log levels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        log_level_label = QLabel("  Log Level: ")
        log_level_label.setFont(QFont("Consolas", 9))

        self.combo = QComboBox()
        self.combo.setFont(QFont("Consolas", 9))
        self.combo.addItem("DEBUG", LogLevel.DEBUG)
        self.combo.addItem("INFO", LogLevel.INFO)
        self.combo.addItem("WARN", LogLevel.WARN)
        self.combo.addItem("ERROR", LogLevel.ERROR)

        layout.addWidget(log_level_label)
        layout.addWidget(self.combo)
        layout.addStretch()

    def set_level(self, level_name: str):
        """
        Set the current log level by name.

        Args:
            level_name: The name of the log level (DEBUG, INFO, WARN, ERROR)
        """
        index = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}.get(level_name, 1)
        self.combo.setCurrentIndex(index)

    def current_level(self) -> LogLevel:
        """
        Get the currently selected log level.

        Returns:
            The selected LogLevel enum value
        """
        return self.combo.currentData()

    def create_menu_action(self, parent) -> QWidgetAction:
        """
        Create a QWidgetAction for adding this widget to a menu.

        Args:
            parent: The parent for the QWidgetAction

        Returns:
            A QWidgetAction containing this widget
        """
        action = QWidgetAction(parent)
        action.setDefaultWidget(self)
        return action
