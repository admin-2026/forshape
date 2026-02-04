"""
StepJump base class for controlling step flow in AI agent execution.

A StepJump determines which step to run next after a step completes.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .step_result import StepResult


class StepJump(ABC):
    """Determines the next step to run after a step completes."""

    @abstractmethod
    def get_next_step(self, result: "StepResult") -> Optional[str]:
        """Return the name of the next step, or None to stop."""
