"""
Tool Call Step for pure tool execution without AI.

This module provides a ToolCallStep that directly calls tools (no AI)
and puts responses in history for other steps to process.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Callable

from .tool_executor import ToolExecutor
from ..request import MessageElement
from ..request.tool_call_message import ToolCallMessage
from ..api_debugger import APIDebugger
from ..api_provider import APIProvider
from ..logger_protocol import LoggerProtocol
from ..user_input_queue import UserInputQueue


@dataclass
class ToolCallStepResult:
    """Result of a ToolCallStep execution."""
    messages: List[Dict]  # Tool call message + tool result messages
    status: str  # "completed", "cancelled", "error"


class ToolCallStep:
    """
    A step that directly calls tools without AI involvement.

    This step takes a ToolCallMessage from initial_messages, executes the
    tool calls, and returns the messages (tool call + results) for the
    conversation history.
    """

    def __init__(
        self,
        name: str,
        tool_executor: ToolExecutor,
        logger: Optional[LoggerProtocol] = None
    ):
        """
        Initialize a ToolCallStep.

        Args:
            name: Name of this step for logging/identification
            tool_executor: ToolExecutor instance for executing tools
            logger: Optional LoggerProtocol instance for logging
        """
        self.name = name
        self.tool_executor = tool_executor
        self.logger = logger

    def _log_info(self, message: str):
        """Log info message if logger is available."""
        if self.logger:
            self.logger.info(f"[{self.name}] {message}")

    def _log_error(self, message: str):
        """Log error message if logger is available."""
        if self.logger:
            self.logger.error(f"[{self.name}] {message}")

    def step_run(
        self,
        provider: APIProvider,  # Ignored - no AI calls
        model: str,             # Ignored - no AI calls
        history: List[Dict],
        input_queue: UserInputQueue,  # Ignored - no user input processing
        initial_messages: Optional[List[MessageElement]] = None,
        api_debugger: Optional[APIDebugger] = None,
        token_callback: Optional[Callable[[Dict], None]] = None,  # Ignored - no tokens
        cancellation_check: Optional[Callable[[], bool]] = None
    ) -> ToolCallStepResult:
        """
        Run the step by executing tool calls from initial_messages.

        Args:
            provider: API provider (ignored - no AI calls made)
            model: Model identifier (ignored - no AI calls made)
            history: Conversation history (not modified, for reference only)
            input_queue: UserInputQueue (ignored - no user input processing)
            initial_messages: List of MessageElement objects; must contain a ToolCallMessage
            api_debugger: Optional APIDebugger instance for dumping tool execution data
            token_callback: Optional callback (ignored - no tokens used)
            cancellation_check: Optional function that returns True if cancellation requested

        Returns:
            ToolCallStepResult containing messages (tool call + results) and status
        """
        messages = []

        # Validate initial_messages contains only ToolCallMessage
        if not initial_messages:
            self._log_error("No initial_messages provided")
            return ToolCallStepResult(
                messages=[],
                status="error"
            )

        # Check all messages are ToolCallMessage
        for msg_element in initial_messages:
            if not isinstance(msg_element, ToolCallMessage):
                self._log_error(
                    f"initial_messages must contain only ToolCallMessage, "
                    f"got {type(msg_element).__name__}"
                )
                return ToolCallStepResult(
                    messages=[],
                    status="error"
                )

        # Use the first ToolCallMessage
        tool_call_message = initial_messages[0]

        # Check for cancellation before starting
        if cancellation_check and cancellation_check():
            return ToolCallStepResult(
                messages=[],
                status="cancelled"
            )

        # Add the assistant message with tool_calls to output
        assistant_message = tool_call_message.get_message()
        if assistant_message:
            messages.append(assistant_message)

        # Get the tool calls
        tool_calls = tool_call_message.get_tool_calls()

        self._log_info(f"Executing {len(tool_calls)} tool call(s)")

        try:
            # Execute tools using shared executor
            result_messages, was_cancelled = self.tool_executor.execute_tool_calls(
                tool_calls=tool_calls,
                api_debugger=api_debugger,
                cancellation_check=cancellation_check
            )

            if was_cancelled:
                return ToolCallStepResult(
                    messages=messages,
                    status="cancelled"
                )

            messages.extend(result_messages)

            return ToolCallStepResult(
                messages=messages,
                status="completed"
            )

        except Exception as e:
            self._log_error(f"Error during tool execution: {str(e)}")
            return ToolCallStepResult(
                messages=messages,
                status="error"
            )
