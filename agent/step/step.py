"""
Step class for AI agent execution.

A Step represents a single execution unit that runs a tool-calling loop
until completion or max iterations.
"""

from typing import TYPE_CHECKING, Callable, Optional

from ..api_debugger import APIDebugger
from ..api_provider import APIProvider
from ..chat_history_manager import HistoryMessage
from ..logger_protocol import LoggerProtocol
from ..request import Instruction, MessageElement, RequestBuilder, TextMessage
from ..step_config import StepConfig
from .step_jump import StepJump
from .step_result import StepResult
from .tool_executor import ToolExecutor

if TYPE_CHECKING:
    from ..step_jump_controller import StepJumpController


class Step:
    """
    A Step represents a single execution unit in an AI agent pipeline.

    Each step has its own request builder, tool manager, and configuration.
    The step runs a tool-calling loop until the AI provides a final response
    or max iterations is reached.
    """

    def __init__(
        self,
        name: str,
        request_builder: RequestBuilder,
        tool_executor: ToolExecutor,
        max_iterations: int = 50,
        logger: Optional[LoggerProtocol] = None,
        step_jump: Optional[StepJump] = None,
    ):
        """
        Initialize a Step.

        Args:
            name: Name of this step for logging/identification
            request_builder: RequestBuilder instance for building request context
            tool_executor: ToolExecutor instance for executing tools
            max_iterations: Maximum number of tool calling iterations (default: 50)
            logger: Optional LoggerProtocol instance for logging
            step_jump: Optional StepJump to determine the next step after completion
        """
        self.name = name
        self.request_builder = request_builder
        self.tool_executor = tool_executor
        self.max_iterations = max_iterations
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
        provider: APIProvider,
        model: str,
        history: list[dict],
        step_config: Optional[StepConfig] = None,
        initial_messages: Optional[list[MessageElement]] = None,
        api_debugger: Optional[APIDebugger] = None,
        token_callback: Optional[Callable[[dict], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
        response_content_callback: Optional[Callable[[str, str], None]] = None,
        step_jump_controller: Optional["StepJumpController"] = None,
    ) -> StepResult:
        """
        Run the step with a user message. Executes the tool-calling loop.

        Args:
            provider: API provider to use for completions
            model: Model identifier to use
            history: Conversation history from previous steps/interactions
            step_config: Optional StepConfig containing the initial message and pending messages
            initial_messages: Optional list of MessageElement objects for additional content
            api_debugger: Optional APIDebugger instance for dumping API data
            token_callback: Optional callback function to receive token usage updates
            cancellation_check: Optional function that returns True if cancellation requested
            response_content_callback: Optional callback function to receive response content (step_name, content)
            step_jump_controller: Optional StepJumpController for dynamic step flow control

        Returns:
            StepResult containing history_messages, api_messages, token usage, and status
        """
        # Check if we're resuming from a call_step (has saved context)
        if step_jump_controller and step_jump_controller.has_saved_context():
            messages = step_jump_controller.get_and_clear_saved_messages()
            self._log_info("Resuming from call_step with saved messages")

            # Add a message to inform LLM about the called step's completion
            # The called step's result should be in the history
            if history:
                # Find the last assistant message from history (from the called step)
                last_result = None
                for msg in reversed(history):
                    if msg.get("role") == "assistant":
                        last_result = msg.get("content", "")
                        break
                if last_result:
                    messages.append(
                        {
                            "role": "user",
                            "content": f"[Called step completed with result: {last_result}]",
                        }
                    )
        else:
            # Build messages fresh (normal flow)
            user_messages = []
            if step_config:
                user_message = step_config.get_initial_message()
                if user_message:
                    user_messages.append(Instruction(user_message, description="User Request"))

            messages = self.request_builder.build_messages(history, user_messages, initial_messages)

        # Initialize token usage tracking
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0

        def _make_token_usage() -> dict:
            return {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens,
            }

        # Agent loop: keep calling tools until the agent gives a final response
        for iteration in range(self.max_iterations):
            # Check for cancellation before each iteration
            if cancellation_check and cancellation_check():
                return StepResult(
                    history_messages=[
                        HistoryMessage(
                            role="assistant",
                            content="Operation cancelled by user.",
                            key=f"{self.name}_cancelled",
                        )
                    ],
                    api_messages=messages,
                    token_usage=_make_token_usage(),
                    status="cancelled",
                    step_jump=self.step_jump,
                )

            # Check for new user input from the step_config
            pending_input = step_config.get_next_message() if step_config else None
            if pending_input:
                # Append the new user message to the conversation
                messages.append(TextMessage("user", pending_input).get_message())
                self._log_info(f"New user input received during iteration {iteration + 1}: {pending_input}")

            try:
                # Dump request data if debugger is enabled
                if api_debugger:
                    api_debugger.dump_request(
                        model=model,
                        messages=messages,
                        tools=self.tool_executor.tool_manager.get_tools(),
                        tool_choice="auto",
                        additional_data={"iteration": iteration + 1, "step": self.name},
                    )

                # Call API provider with tools
                response = provider.create_completion(
                    model=model,
                    messages=messages,
                    tools=self.tool_executor.tool_manager.get_tools(),
                    tool_choice="auto",
                )

                # Track token usage from this API call
                if hasattr(response, "usage") and response.usage:
                    total_prompt_tokens += response.usage.prompt_tokens
                    total_completion_tokens += response.usage.completion_tokens
                    total_tokens += response.usage.total_tokens

                    # Send token usage update via callback if provided
                    if token_callback:
                        token_data = {
                            "prompt_tokens": total_prompt_tokens,
                            "completion_tokens": total_completion_tokens,
                            "total_tokens": total_tokens,
                            "iteration": iteration + 1,
                            "step": self.name,
                        }
                        token_callback(token_data)

                # Dump response data if debugger is enabled
                if api_debugger:
                    api_debugger.dump_response(
                        response=response,
                        token_usage=_make_token_usage(),
                        additional_data={"iteration": iteration + 1, "step": self.name},
                    )

                response_message = response.choices[0].message

                # Invoke response content callback if provided
                if response_content_callback and response_message.content:
                    response_content_callback(self.name, response_message.content)

                # Check if the agent wants to call tools
                if response_message.tool_calls:
                    # Add the assistant's message (with tool_calls) to messages first
                    # Use exclude_none=True to avoid sending extra fields like 'refusal',
                    # 'annotations', 'audio', 'function_call' that some APIs reject
                    messages.append(response_message.model_dump(exclude_none=True))

                    # Execute tools using shared executor
                    result_messages, was_cancelled = self.tool_executor.execute_tool_calls(
                        tool_calls=response_message.tool_calls,
                        api_debugger=api_debugger,
                        cancellation_check=cancellation_check,
                    )

                    if was_cancelled:
                        return StepResult(
                            history_messages=[
                                HistoryMessage(
                                    role="assistant",
                                    content="Operation cancelled by user.",
                                    key=f"{self.name}_cancelled",
                                )
                            ],
                            api_messages=messages,
                            token_usage=_make_token_usage(),
                            status="cancelled",
                            step_jump=self.step_jump,
                        )

                    messages.extend(result_messages)

                    # Check if a call_step was requested - save context and return early
                    if step_jump_controller and step_jump_controller.is_call_pending():
                        step_jump_controller.save_call_context(messages)
                        self._log_info("call_step detected, saving context and yielding to called step")
                        return StepResult(
                            history_messages=[],  # No history yet, will continue after call returns
                            api_messages=messages,
                            token_usage=_make_token_usage(),
                            status="call_pending",
                            step_jump=self.step_jump,
                        )

                    # Continue the loop to get the next response
                    continue

                # No tool calls, we have a final response
                final_response = response_message.content

                return StepResult(
                    history_messages=[
                        HistoryMessage(
                            role="assistant",
                            content=final_response,
                            key=f"{self.name}_response",
                        )
                    ],
                    api_messages=messages,
                    token_usage=_make_token_usage(),
                    status="completed",
                    step_jump=self.step_jump,
                )

            except Exception as e:
                return StepResult(
                    history_messages=[
                        HistoryMessage(
                            role="assistant",
                            content=f"Error during step execution: {str(e)}",
                            key=f"{self.name}_error",
                        )
                    ],
                    api_messages=messages,
                    token_usage=_make_token_usage(),
                    status="error",
                    step_jump=self.step_jump,
                )

        # If we hit max iterations
        return StepResult(
            history_messages=[
                HistoryMessage(
                    role="assistant",
                    content="Step reached maximum iterations without completing the task.",
                    key=f"{self.name}_max_iterations",
                )
            ],
            api_messages=messages,
            token_usage=_make_token_usage(),
            status="max_iterations",
            step_jump=self.step_jump,
        )
