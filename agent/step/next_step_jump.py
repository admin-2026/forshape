"""
NextStepJump - A StepJump that always jumps to a fixed next step.
"""

from typing import TYPE_CHECKING

from .step_jump import StepJump

if TYPE_CHECKING:
    from .step_result import StepResult


class NextStepJump(StepJump):
    """A StepJump that always jumps to a fixed next step."""

    def __init__(self, next_step: str):
        self._next_step = next_step

    def get_next_step(self, result: "StepResult") -> str:
        return self._next_step
