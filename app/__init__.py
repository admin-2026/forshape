"""
GUI components for ForShape AI.

This package contains the GUI-related classes for the ForShape AI application.
"""

# Re-export agent components for backwards compatibility
from agent import (
    AIAgent,
    APIDebugger,
    ApiKeyManager,
    EditHistory,
    HistoryLogger,
    PermissionManager,
    PermissionResponse,
    Step,
    StepResult,
)

from .config_manager import ConfigurationManager
from .dependency_manager import DependencyManager
from .document_observer import ActiveDocumentObserver
from .logger import Logger, LogLevel
from .main_window import ForShapeMainWindow
from .prestart_checker import PrestartChecker

__all__ = [
    "DependencyManager",
    "ConfigurationManager",
    "HistoryLogger",
    "AIAgent",
    "Step",
    "StepResult",
    "ForShapeMainWindow",
    "Logger",
    "LogLevel",
    "PermissionManager",
    "PermissionResponse",
    "PrestartChecker",
    "APIDebugger",
    "ApiKeyManager",
    "EditHistory",
    "ActiveDocumentObserver",
]
