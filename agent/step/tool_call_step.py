"""
Tool Call Step for pure tool execution without AI.

This module provides a ToolCallStep that directly calls tools (no AI)
and puts responses in history for other steps to process.
"""

from typing import Callable, Optional

from ..api_debugger import APIDebugger
from ..api_provider import APIProvider
from ..chat_history_manager import HistoryMessage
from ..logger_protocol import LoggerProtocol
from ..request import MessageElement
from ..request.tool_call_message import ToolCall, ToolCallMessage
from ..step_config import StepConfig
from .step_jump import StepJump
from .step_result import StepResult
from .tool_executor import ToolExecutor


class ToolCallStep:
    """
    A step that directly calls tools without AI involvement.

    This step takes ToolCallMessages and executes the tool calls,
    returning the messages (tool call + results) for the conversation history.
    Messages provided at construction time are concatenated with any
    initial_messages from step_run, and all are executed one by one.
    """

    def __init__(
        self,
        name: str,
        tool_executor: ToolExecutor,
        messages: Optional[list[MessageElement]] = None,
        logger: Optional[LoggerProtocol] = None,
        step_jump: Optional[StepJump] = None,
    ):
        """
        Initialize a ToolCallStep.

        Args:
            name: Name of this step for logging/identification
            tool_executor: ToolExecutor instance for executing tools
            messages: Optional list of MessageElement to execute (concatenated with step_run initial_messages)
            logger: Optional LoggerProtocol instance for logging
            step_jump: Optional StepJump to determine the next step after completion
        """
        self.name = name
        self.tool_executor = tool_executor
        self.messages = messages or []
        self.logger = logger
        self.step_jump = step_jump

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
        model: str,  # Ignored - no AI calls
        history: list[dict],
        step_config: Optional[StepConfig] = None,  # Ignored - no user input processing
        initial_messages: Optional[list[MessageElement]] = None,
        api_debugger: Optional[APIDebugger] = None,
        token_callback: Optional[Callable[[dict], None]] = None,  # Ignored - no tokens
        cancellation_check: Optional[Callable[[], bool]] = None,
        response_content_callback: Optional[Callable[[str, str], None]] = None,  # Ignored - no user facing response
    ) -> StepResult:
        """
        Run the step by executing tool calls from initial_messages.

        Args:
            provider: API provider (ignored - no AI calls made)
            model: Model identifier (ignored - no AI calls made)
            history: Conversation history (not modified, for reference only)
            step_config: Optional StepConfig (ignored - no user input processing)
            initial_messages: List of MessageElement objects; must contain a ToolCallMessage
            api_debugger: Optional APIDebugger instance for dumping tool execution data
            token_callback: Optional callback (ignored - no tokens used)
            cancellation_check: Optional function that returns True if cancellation requested
            response_content_callback: Optional callback function to receive response content (step_name, content)

        Returns:
            StepResult containing history_messages (one per tool result), api_messages, and status
        """
        # Concatenate constructor messages with step_run initial_messages
        all_messages: list[MessageElement] = list(self.messages)
        if initial_messages:
            all_messages.extend(initial_messages)

        api_messages = []

        if not all_messages:
            self._log_error("No messages provided")
            return StepResult(
                history_messages=[], api_messages=[], token_usage={}, status="error", step_jump=self.step_jump
            )

        # Check all messages are ToolCallMessage
        for msg_element in all_messages:
            if not isinstance(msg_element, ToolCallMessage):
                self._log_error(f"messages must contain only ToolCallMessage, got {type(msg_element).__name__}")
                return StepResult(
                    history_messages=[], api_messages=[], token_usage={}, status="error", step_jump=self.step_jump
                )

        # Check for cancellation before starting
        if cancellation_check and cancellation_check():
            return StepResult(
                history_messages=[], api_messages=[], token_usage={}, status="cancelled", step_jump=self.step_jump
            )

        history_messages: list[HistoryMessage] = []

        try:
            # Process each ToolCallMessage one by one
            for tool_call_message in all_messages:
                # Check for cancellation before each message
                if cancellation_check and cancellation_check():
                    return StepResult(
                        history_messages=history_messages,
                        api_messages=api_messages,
                        token_usage={},
                        status="cancelled",
                        step_jump=self.step_jump,
                    )

                # Add the assistant message with tool_calls to output
                assistant_message = tool_call_message.get_message()
                if assistant_message:
                    api_messages.append(assistant_message)

                # Get the tool calls
                tool_calls = tool_call_message.get_tool_calls()

                self._log_info(f"Executing {len(tool_calls)} tool call(s)")

                # Build a map of tool call IDs to descriptions and tools
                tool_info = {tc.id: tc for tc in tool_calls if isinstance(tc, ToolCall)}

                # Execute tools using shared executor
                result_messages, was_cancelled = self.tool_executor.execute_tool_calls(
                    tool_calls=tool_calls, api_debugger=api_debugger, cancellation_check=cancellation_check
                )

                if was_cancelled:
                    return StepResult(
                        history_messages=history_messages,
                        api_messages=api_messages,
                        token_usage={},
                        status="cancelled",
                        step_jump=self.step_jump,
                    )

                # Build history messages - one per tool result
                for i, msg in enumerate(result_messages):
                    tool_call_id = msg.get("tool_call_id")
                    content = msg.get("content", "")

                    # Add description prefix if available
                    if tool_call_id and tool_call_id in tool_info:
                        tc = tool_info[tool_call_id]
                        if tc.description:
                            content = f"{tc.description}\n\n{content}"
                        # Update the api_message content with description
                        msg["content"] = content

                        # Check if this tool result should be added to history
                        if tc.copy_result_to_response:
                            # Use key from ToolCall if provided, otherwise generate one
                            key = tc.key if tc.key else f"{self.name}_tool_{i}_{tool_call_id}"
                            history_messages.append(
                                HistoryMessage(
                                    role="assistant",
                                    content=content,
                                    key=key,
                                    policy=tc.policy,
                                )
                            )

                api_messages.extend(result_messages)

            return StepResult(
                history_messages=history_messages,
                api_messages=api_messages,
                token_usage={},
                status="completed",
                step_jump=self.step_jump,
            )

        except Exception as e:
            self._log_error(f"Error during tool execution: {str(e)}")
            return StepResult(
                history_messages=[], api_messages=api_messages, token_usage={}, status="error", step_jump=self.step_jump
            )
