"""
Agent module for AI agent logic.

This module contains the AI agent orchestration, API provider abstraction,
tool management, and related components that are independent of the GUI.
"""

from .ai_agent import AIAgent
from .api_debugger import APIDebugger
from .api_key_manager import ApiKeyManager
from .api_provider import APIProvider, OpenAICompatibleProvider, create_api_provider, create_api_provider_from_config
from .async_ops import (
    ClarificationInput,
    PermissionInput,
    UserInputBase,
    UserInputRequest,
    UserInputResponse,
    WaitManager,
)
from .chat_history_manager import ChatHistoryManager
from .edit_history import EditHistory
from .history_logger import HistoryLogger
from .logger_protocol import LoggerProtocol
from .permission_manager import PermissionManager, PermissionResponse
from .provider_config_loader import ModelConfig, ProviderConfig, ProviderConfigLoader
from .request import RequestBuilder
from .step import Step, StepResult, ToolCallStep, ToolExecutor
from .step_config import StepConfig, StepConfigRegistry
from .tools.tool_manager import ToolManager
from .user_input_queue import UserInputQueue

__all__ = [
    "AIAgent",
    "Step",
    "StepResult",
    "ToolCallStep",
    "ToolExecutor",
    "StepConfig",
    "StepConfigRegistry",
    "APIProvider",
    "OpenAICompatibleProvider",
    "create_api_provider",
    "create_api_provider_from_config",
    "ToolManager",
    "ChatHistoryManager",
    "RequestBuilder",
    "APIDebugger",
    "ProviderConfigLoader",
    "ProviderConfig",
    "ModelConfig",
    "PermissionManager",
    "PermissionResponse",
    "ApiKeyManager",
    "HistoryLogger",
    "EditHistory",
    "LoggerProtocol",
    "UserInputQueue",
    "WaitManager",
    "UserInputBase",
    "UserInputRequest",
    "UserInputResponse",
    "ClarificationInput",
    "PermissionInput",
]
