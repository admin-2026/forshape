"""
GUI components for ForShape AI.

This package contains the GUI-related classes for the ForShape AI application.
"""

from .dependency_manager import DependencyManager
from .config_manager import ConfigurationManager
from .history_logger import HistoryLogger
from .ai_client import AIClient
from .main_window import ForShapeMainWindow

__all__ = [
    'DependencyManager',
    'ConfigurationManager',
    'HistoryLogger',
    'AIClient',
    'ForShapeMainWindow',
]
