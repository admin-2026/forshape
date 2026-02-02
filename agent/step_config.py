"""
Step configuration for AI agent execution.

This module provides runtime configuration for step-specific data injection,
allowing AIWorker to specify initial_messages and input_queue for specific steps.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict

from .request import MessageElement
from .user_input_queue import UserInputQueue


@dataclass
class StepConfig:
    """Runtime configuration for a specific step execution."""
    initial_messages: Optional[List[MessageElement]] = None
    input_queue: Optional[UserInputQueue] = None


class StepConfigRegistry:
    """Registry for step-specific runtime configurations."""

    def __init__(self, default_input_queue: UserInputQueue):
        """
        Initialize registry with a default input queue.

        Args:
            default_input_queue: Fallback queue for steps without specific config
        """
        self.default_input_queue = default_input_queue
        self._configs: Dict[str, StepConfig] = {}

    def set_config(self, step_name: str, config: StepConfig) -> None:
        """Set configuration for a specific step by name."""
        self._configs[step_name] = config

    def get_initial_messages(self, step_name: str) -> Optional[List[MessageElement]]:
        """Get initial_messages for a step, or None if not configured."""
        config = self._configs.get(step_name)
        return config.initial_messages if config else None

    def get_input_queue(self, step_name: str) -> UserInputQueue:
        """Get input_queue for a step, or default if not configured."""
        config = self._configs.get(step_name)
        if config and config.input_queue is not None:
            return config.input_queue
        return self.default_input_queue

    def set_initial_messages(self, step_name: str, messages: List[MessageElement]) -> None:
        """Convenience method to set initial_messages for a step."""
        config = self._configs.get(step_name) or StepConfig()
        config.initial_messages = messages
        self._configs[step_name] = config

    def set_input_queue(self, step_name: str, queue: UserInputQueue) -> None:
        """Convenience method to set input_queue for a step."""
        config = self._configs.get(step_name) or StepConfig()
        config.input_queue = queue
        self._configs[step_name] = config
