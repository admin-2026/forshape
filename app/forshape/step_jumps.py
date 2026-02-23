from typing import Optional

from agent import StepJump


class ChangedFilesStepJump(StepJump):
    """A StepJump that jumps to next step only if files were changed (edited or created)."""

    def __init__(self, next_step: str, edit_history):
        self._next_step = next_step
        self._edit_history = edit_history

    def get_next_step(self, result) -> Optional[str]:
        """Return next step only if files were changed, otherwise None to stop."""
        changed_files = self._edit_history.get_changed_files()
        if changed_files:
            return self._next_step
        return None


class LintStepJump(StepJump):
    """A StepJump that jumps to lint_err_fix only if there are lint issues."""

    def __init__(self, next_step: str):
        self._next_step = next_step

    def get_next_step(self, result) -> Optional[str]:
        """Return next step only if lint found issues, otherwise None to stop."""
        import json

        # Look through api_messages for the lint results
        for msg in result.api_messages:
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                try:
                    tool_result = json.loads(content)
                    # Check if this is a lint result with issues
                    if tool_result.get("success") and tool_result.get("issue_count", 0) > 0:
                        return self._next_step
                except (json.JSONDecodeError, TypeError):
                    continue

        # No issues found, stop here
        return None
