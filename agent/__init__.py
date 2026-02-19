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
from .chat_history_manager import ChatHistoryManager, HistoryMessage, HistoryPolicy
from .edit_history import EditHistory
from .history_logger import HistoryLogger
from .logger_protocol import LoggerProtocol
from .permission_manager import PermissionManager, PermissionResponse
from .provider_config_loader import ModelConfig, ProviderConfig, ProviderConfigLoader
from .request import RequestBuilder
from .step import DynamicStepJump, HistoryEditStep, NextStepJump, Step, StepJump, StepResult, ToolCallStep, ToolExecutor
from .step_config import StepConfig, StepConfigRegistry
from .step_jump_controller import StepJumpController
from .tools.step_jump_tools import StepJumpTools
from .tools.tool_manager import ToolManager

__all__ = [
    "AIAgent",
    "Step",
    "StepJump",
    "NextStepJump",
    "DynamicStepJump",
    "HistoryEditStep",
    "StepJumpController",
    "StepJumpTools",
    "StepResult",
    "HistoryMessage",
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
    "HistoryPolicy",
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
    "WaitManager",
    "UserInputBase",
    "UserInputRequest",
    "UserInputResponse",
    "ClarificationInput",
    "PermissionInput",
]
