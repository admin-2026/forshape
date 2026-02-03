"""
Step configuration for AI agent execution.

This module provides runtime configuration for step-specific data injection,
allowing AIWorker to specify messages and user input handling for specific steps.
"""

from dataclasses import dataclass, field
from typing import Optional

from .request import MessageElement


@dataclass
class StepConfig:
    """Runtime configuration for a specific step execution.

    This class manages both additional messages and user input for a step.
    It encapsulates the initial user message and allows pending messages to be
    queued and retrieved during AI agent iterations.
    """

    messages: Optional[list[MessageElement]] = None
    initial_message: Optional[str] = None
    pending_messages: list[str] = field(default_factory=list)

    def add_pending_message(self, message: str) -> None:
        """Add a new message to the pending queue.

        This is called when the user types additional input while the AI is processing.

        Args:
            message: The new message to add to the queue
        """
        if message:  # Only add non-empty messages
            self.pending_messages.append(message)

    def get_initial_message(self) -> Optional[str]:
        """Get the initial message that started this conversation.

        Returns:
            The initial user message, or None if not set
        """
        return self.initial_message

    def get_next_message(self) -> Optional[str]:
        """Get and remove the next pending message from the queue.

        This is called by the AI agent during iterations to check for new user input.

        Returns:
            The next pending message, or None if the queue is empty
        """
        if self.pending_messages:
            return self.pending_messages.pop(0)
        return None


class StepConfigRegistry:
    """Registry for step-specific runtime configurations."""

    def __init__(self):
        """Initialize an empty registry."""
        self._configs: dict[str, StepConfig] = {}

    def set_config(self, step_name: str, config: StepConfig) -> None:
        """Set configuration for a specific step by name."""
        self._configs[step_name] = config

    def get_config(self, step_name: str) -> StepConfig:
        """Get configuration for a step, creating a default if not configured."""
        return self._configs.get(step_name) or StepConfig()

    def get_messages(self, step_name: str) -> Optional[list[MessageElement]]:
        """Get messages for a step, or None if not configured."""
        config = self._configs.get(step_name)
        return config.messages if config else None

    def append_messages(self, step_name: str, messages: list[MessageElement]) -> None:
        """Append messages to a step. Can be called multiple times."""
        config = self._configs.get(step_name) or StepConfig()
        if config.messages is None:
            config.messages = []
        config.messages.extend(messages)
        self._configs[step_name] = config
