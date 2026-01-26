"""
GUI components for ForShape AI.

This package contains the GUI-related classes for the ForShape AI application.
"""

from .dependency_manager import DependencyManager
from .config_manager import ConfigurationManager
from .main_window import ForShapeMainWindow
from .logger import Logger, LogLevel
from .prestart_checker import PrestartChecker

# Re-export agent components for backwards compatibility
from agent import (
    AIAgent,
    ContextProvider,
    APIDebugger,
    PermissionManager,
    PermissionResponse,
    ApiKeyManager,
    HistoryLogger,
    EditHistory,
    UserInputQueue,
)

__all__ = [
    'DependencyManager',
    'ConfigurationManager',
    'HistoryLogger',
    'AIAgent',
    'ForShapeMainWindow',
    'ContextProvider',
    'Logger',
    'LogLevel',
    'PermissionManager',
    'PermissionResponse',
    'PrestartChecker',
    'APIDebugger',
    'ApiKeyManager',
    'EditHistory',
    'UserInputQueue',
]
