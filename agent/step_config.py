"""
Step configuration for AI agent execution.

This module provides runtime configuration for step-specific data injection,
allowing AIWorker to specify messages and input_queue for specific steps.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict

from .request import MessageElement
from .user_input_queue import UserInputQueue


@dataclass
class StepConfig:
    """Runtime configuration for a specific step execution."""
    messages: Optional[List[MessageElement]] = None
    input_queue: Optional[UserInputQueue] = None


class StepConfigRegistry:
    """Registry for step-specific runtime configurations."""

    def __init__(self):
        """Initialize an empty registry."""
        self._configs: Dict[str, StepConfig] = {}

    def set_config(self, step_name: str, config: StepConfig) -> None:
        """Set configuration for a specific step by name."""
        self._configs[step_name] = config

    def get_messages(self, step_name: str) -> Optional[List[MessageElement]]:
        """Get messages for a step, or None if not configured."""
        config = self._configs.get(step_name)
        return config.messages if config else None

    def get_input_queue(self, step_name: str) -> Optional[UserInputQueue]:
        """Get input_queue for a step, or None if not configured."""
        config = self._configs.get(step_name)
        if config and config.input_queue is not None:
            return config.input_queue
        return None

    def append_messages(self, step_name: str, messages: List[MessageElement]) -> None:
        """Append messages to a step. Can be called multiple times."""
        config = self._configs.get(step_name) or StepConfig()
        if config.messages is None:
            config.messages = []
        config.messages.extend(messages)
        self._configs[step_name] = config

    def set_input_queue(self, step_name: str, queue: UserInputQueue) -> None:
        """Convenience method to set input_queue for a step."""
        config = self._configs.get(step_name) or StepConfig()
        config.input_queue = queue
        self._configs[step_name] = config
