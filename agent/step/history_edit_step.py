"""
History Edit Step for modifying conversation history.

This module provides a HistoryEditStep that edits the chat history manager
(e.g., dropping messages from a given step) without generating additional history.
"""

from typing import TYPE_CHECKING, Callable, Optional

from ..api_debugger import APIDebugger
from ..api_provider import APIProvider
from ..chat_history_manager import ChatHistoryManager
from ..logger_protocol import LoggerProtocol
from ..request import MessageElement
from ..step_config import StepConfig
from .step_jump import StepJump
from .step_result import StepResult

if TYPE_CHECKING:
    from ..step_jump_controller import StepJumpController


class HistoryEditStep:
    """
    A step that edits the chat history without AI involvement.

    This step drops history from one or more step names from the history manager.
    It does not generate any additional history messages.
    """

    def __init__(
        self,
        name: str,
        history_manager: ChatHistoryManager,
        step_names_to_drop: list[str],
        logger: Optional[LoggerProtocol] = None,
        step_jump: Optional[StepJump] = None,
    ):
        """
        Initialize a HistoryEditStep.

        Args:
            name: Name of this step for logging/identification
            history_manager: ChatHistoryManager instance to edit
            step_names_to_drop: Step names whose history messages to drop
            logger: Optional LoggerProtocol instance for logging
            step_jump: Optional StepJump to determine the next step after completion
        """
        self.name = name
        self.history_manager = history_manager
        self.step_names_to_drop = step_names_to_drop
        self.logger = logger
        self.step_jump = step_jump

    def _log_info(self, message: str):
        """Log info message if logger is available."""
        if self.logger:
            self.logger.info(f"[{self.name}] {message}")

    def step_run(
        self,
        provider: APIProvider,  # Ignored - no AI calls
        model: str,  # Ignored - no AI calls
        history: list[dict],  # Ignored - edits history manager directly
        step_config: Optional[StepConfig] = None,  # Ignored
        initial_messages: Optional[list[MessageElement]] = None,  # Ignored
        api_debugger: Optional[APIDebugger] = None,  # Ignored
        token_callback: Optional[Callable[[dict], None]] = None,  # Ignored
        cancellation_check: Optional[Callable[[], bool]] = None,
        response_content_callback: Optional[Callable[[str, str], None]] = None,  # Ignored
        step_jump_controller: Optional["StepJumpController"] = None,  # Ignored
    ) -> StepResult:
        """
        Run the step by dropping history from the configured step name.

        Args:
            provider: API provider (ignored - no AI calls made)
            model: Model identifier (ignored - no AI calls made)
            history: Conversation history (ignored - edits history manager directly)
            step_config: Optional StepConfig (ignored)
            initial_messages: Optional list of MessageElement (ignored)
            api_debugger: Optional APIDebugger (ignored)
            token_callback: Optional callback (ignored)
            cancellation_check: Optional function that returns True if cancellation requested
            response_content_callback: Optional callback (ignored)
            step_jump_controller: Optional StepJumpController (ignored)

        Returns:
            StepResult with empty history_messages and api_messages
        """
        if cancellation_check and cancellation_check():
            return StepResult(
                history_messages=[], api_messages=[], token_usage={}, status="cancelled", step_jump=self.step_jump
            )

        for step_name in self.step_names_to_drop:
            dropped = self.history_manager.drop_history_by_step(step_name)
            self._log_info(f"Dropped {dropped} message(s) from step '{step_name}'")

        return StepResult(
            history_messages=[],
            api_messages=[],
            token_usage={},
            status="completed",
            step_jump=self.step_jump,
        )
