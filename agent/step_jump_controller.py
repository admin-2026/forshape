"""Controller for managing dynamic step jump/call requests."""

from typing import Optional


class StepJumpController:
    """Manages dynamic step jump and call requests from tools."""

    def __init__(self, valid_destinations: dict[str, list[str]]):
        """
        Initialize the controller.

        Args:
            valid_destinations: Dict mapping step names to their allowed destination steps.
                               Example: {"main": ["lint", "lint_err_fix"], "lint": ["main"]}
        """
        self._valid_destinations = valid_destinations
        self._target_step: Optional[str] = None
        self._return_step: Optional[str] = None

    def clear(self) -> None:
        """Clear any pending jump/call requests."""
        self._target_step = None
        self._return_step = None

    def request_jump(self, from_step: str, to_step: str) -> tuple[bool, str]:
        """
        Request a one-way jump to the specified step.

        Args:
            from_step: The step making the request
            to_step: The destination step

        Returns:
            Tuple of (success, message)
        """
        valid, error = self._validate_destination(from_step, to_step)
        if not valid:
            return False, error
        self._target_step = to_step
        self._return_step = None
        return True, f"Jump to '{to_step}' requested"

    def request_call(self, from_step: str, to_step: str) -> tuple[bool, str]:
        """
        Request a call to the specified step with return.

        Args:
            from_step: The step making the request (will be returned to)
            to_step: The destination step to call

        Returns:
            Tuple of (success, message)
        """
        valid, error = self._validate_destination(from_step, to_step)
        if not valid:
            return False, error
        self._target_step = to_step
        self._return_step = from_step
        return True, f"Call to '{to_step}' requested (will return to '{from_step}')"

    def get_and_clear_target(self) -> Optional[str]:
        """Get the requested target step and clear it."""
        target = self._target_step
        self._target_step = None
        return target

    def get_and_clear_return(self) -> Optional[str]:
        """Get the pending return step and clear it."""
        return_step = self._return_step
        self._return_step = None
        return return_step

    def has_pending_return(self) -> bool:
        """Check if there's a pending return step."""
        return self._return_step is not None

    def get_valid_destinations(self, from_step: str) -> list[str]:
        """Get list of valid destination steps from the given step."""
        return self._valid_destinations.get(from_step, [])

    def _validate_destination(self, from_step: str, to_step: str) -> tuple[bool, str]:
        """Validate that the jump/call is allowed."""
        if from_step not in self._valid_destinations:
            return False, f"Step '{from_step}' cannot jump to other steps"
        valid_targets = self._valid_destinations[from_step]
        if to_step not in valid_targets:
            return False, f"Cannot go from '{from_step}' to '{to_step}'. Valid: {valid_targets}"
        return True, ""
