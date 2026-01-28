"""
Agent module for AI agent logic.

This module contains the AI agent orchestration, API provider abstraction,
tool management, and related components that are independent of the GUI.
"""

from .ai_agent import AIAgent
from .api_provider import APIProvider, OpenAICompatibleProvider, create_api_provider, create_api_provider_from_config
from .tools.tool_manager import ToolManager
from .chat_history_manager import ChatHistoryManager
from .context_provider import ContextProvider
from .request import RequestBuilder
from .api_debugger import APIDebugger
from .provider_config_loader import ProviderConfigLoader, ProviderConfig, ModelConfig
from .permission_manager import PermissionManager, PermissionResponse
from .api_key_manager import ApiKeyManager
from .history_logger import HistoryLogger
from .edit_history import EditHistory
from .logger_protocol import LoggerProtocol
from .user_input_queue import UserInputQueue
from .async_ops import WaitManager
from .async_ops import (
    UserInputBase,
    UserInputRequest,
    UserInputResponse,
    ClarificationInput,
    PermissionInput,
)

__all__ = [
    'AIAgent',
    'APIProvider',
    'OpenAICompatibleProvider',
    'create_api_provider',
    'create_api_provider_from_config',
    'ToolManager',
    'ChatHistoryManager',
    'ContextProvider',
    'RequestBuilder',
    'APIDebugger',
    'ProviderConfigLoader',
    'ProviderConfig',
    'ModelConfig',
    'PermissionManager',
    'PermissionResponse',
    'ApiKeyManager',
    'HistoryLogger',
    'EditHistory',
    'LoggerProtocol',
    'UserInputQueue',
    'WaitManager',
    'UserInputBase',
    'UserInputRequest',
    'UserInputResponse',
    'ClarificationInput',
    'PermissionInput',
]
