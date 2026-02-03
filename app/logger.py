"""
Logging module for ForShape GUI.

This module provides a logger with multiple log levels (debug, info, warn, error)
that can be displayed in the GUI and optionally written to files.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from PySide2.QtCore import QObject, Signal


class LogLevel(Enum):
    """Log level enumeration."""

    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


class Logger(QObject):
    """
    Logger with multiple log levels and GUI integration.

    Emits signals that can be connected to GUI components for real-time display.
    """

    # Signal emitted when a log message is created: (level, message, timestamp)
    log_message = Signal(str, str, str)

    def __init__(self, log_file: Optional[Path] = None, min_level: LogLevel = LogLevel.DEBUG):
        """
        Initialize the logger.

        Args:
            log_file: Optional file path to write logs to
            min_level: Minimum log level to process (default: DEBUG)
        """
        super().__init__()
        self.log_file = log_file
        self.min_level = min_level
        self.enabled = True

    def _log(self, level: LogLevel, message: str):
        """
        Internal logging method.

        Args:
            level: Log level
            message: Log message
        """
        if not self.enabled or level.value < self.min_level.value:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_str = level.name

        # Emit signal for GUI
        self.log_message.emit(level_str, message, timestamp)

        # Write to file if configured
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] [{level_str}] {message}\n")
            except Exception:
                # Avoid infinite recursion if file logging fails
                pass

    def debug(self, message: str):
        """
        Log a debug message.

        Args:
            message: Debug message
        """
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str):
        """
        Log an info message.

        Args:
            message: Info message
        """
        self._log(LogLevel.INFO, message)

    def warn(self, message: str):
        """
        Log a warning message.

        Args:
            message: Warning message
        """
        self._log(LogLevel.WARN, message)

    def error(self, message: str):
        """
        Log an error message.

        Args:
            message: Error message
        """
        self._log(LogLevel.ERROR, message)

    def set_enabled(self, enabled: bool):
        """
        Enable or disable logging.

        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled

    def set_min_level(self, level: LogLevel):
        """
        Set the minimum log level to process.

        Args:
            level: Minimum log level
        """
        self.min_level = level
