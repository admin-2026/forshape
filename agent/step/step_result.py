"""
Step result dataclass for AI agent execution.

This module provides the StepResult class used by all step types.
"""

from dataclasses import dataclass

from ..chat_history_manager import HistoryMessage


@dataclass
class StepResult:
    """Result of a Step execution."""

    history_messages: list[HistoryMessage]  # Messages to save to chat history
    api_messages: list[dict]  # Raw API messages from step execution
    token_usage: dict
    status: str  # "completed", "cancelled", "max_iterations", "error"
