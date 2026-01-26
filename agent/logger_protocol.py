"""
Logger Protocol for AI Agent.

This module defines the logger interface used by agent components.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LoggerProtocol(Protocol):
    """Protocol defining the logger interface needed by agent components."""

    def info(self, message: str) -> None:
        """Log an info message."""
        ...

    def error(self, message: str) -> None:
        """Log an error message."""
        ...

    def warn(self, message: str) -> None:
        """Log a warning message."""
        ...
