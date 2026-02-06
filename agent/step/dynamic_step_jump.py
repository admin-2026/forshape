"""DynamicStepJump - A StepJump that supports dynamic jump/call requests."""

from typing import TYPE_CHECKING, Optional

from .step_jump import StepJump

if TYPE_CHECKING:
    from ..step_jump_controller import StepJumpController
    from .step_result import StepResult


class DynamicStepJump(StepJump):
    """A StepJump that checks a controller for dynamic jump/call requests."""

    def __init__(
        self,
        controller: "StepJumpController",
        fallback: Optional[StepJump] = None,
    ):
        """
        Initialize the dynamic step jump.

        Args:
            controller: StepJumpController to check for requests
            fallback: Optional StepJump to use if no dynamic request is pending
        """
        self._controller = controller
        self._fallback = fallback

    def get_next_step(self, result: "StepResult") -> Optional[str]:
        """
        Return the next step based on controller state or fallback.

        Priority:
        1. Pending return from a previous call
        2. Jump/call target requested during this step
        3. Fallback step jump logic
        """
        # Check for pending return first (from a previous call_step)
        if self._controller.has_pending_return():
            return self._controller.get_and_clear_return()

        # Check for jump/call request made during this step
        target = self._controller.get_and_clear_target()
        if target:
            return target

        # Fall back to static behavior
        if self._fallback:
            return self._fallback.get_next_step(result)

        return None
