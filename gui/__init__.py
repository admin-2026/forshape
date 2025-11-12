"""
GUI components for ForShape AI.

This package contains the GUI-related classes for the ForShape AI application.
"""

from .dependency_manager import DependencyManager
from .config_manager import ConfigurationManager
from .history_logger import HistoryLogger
from .ai_agent import AIAgent
from .main_window import ForShapeMainWindow
from .context_provider import ContextProvider
from .logger import Logger, LogLevel
from .permission_manager import PermissionManager

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
]
