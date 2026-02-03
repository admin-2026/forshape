"""
Step class for AI agent execution.

A Step represents a single execution unit that runs a tool-calling loop
until completion or max iterations.
"""

from typing import Callable, Dict, List, Optional

from ..api_debugger import APIDebugger
from ..api_provider import APIProvider
from ..logger_protocol import LoggerProtocol
from ..request import Instruction, MessageElement, RequestBuilder, TextMessage
from ..user_input_queue import UserInputQueue
from .step_result import StepResult
from .tool_executor import ToolExecutor


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
    ):
        """
        Initialize a Step.

        Args:
            name: Name of this step for logging/identification
            request_builder: RequestBuilder instance for building request context
            tool_executor: ToolExecutor instance for executing tools
            max_iterations: Maximum number of tool calling iterations (default: 50)
            logger: Optional LoggerProtocol instance for logging
        """
        self.name = name
        self.request_builder = request_builder
        self.tool_executor = tool_executor
        self.max_iterations = max_iterations
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
        provider: APIProvider,
        model: str,
        history: List[Dict],
        input_queue: Optional[UserInputQueue] = None,
        initial_messages: Optional[List[MessageElement]] = None,
        api_debugger: Optional[APIDebugger] = None,
        token_callback: Optional[Callable[[Dict], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> StepResult:
        """
        Run the step with a user message. Executes the tool-calling loop.

        Args:
            provider: API provider to use for completions
            model: Model identifier to use
            history: Conversation history from previous steps/interactions
            input_queue: Optional UserInputQueue containing the initial message and any follow-up messages
            initial_messages: Optional list of MessageElement objects for additional content
            api_debugger: Optional APIDebugger instance for dumping API data
            token_callback: Optional callback function to receive token usage updates
            cancellation_check: Optional function that returns True if cancellation requested

        Returns:
            StepResult containing response, updated messages, token usage, and status
        """
        # Get the initial message from the queue if available
        user_messages = []
        if input_queue:
            user_message = input_queue.get_initial_message()
            if user_message:
                user_messages.append(Instruction(user_message, description="User Request"))

        messages = self.request_builder.build_messages(history, user_messages, initial_messages)

        # Initialize token usage tracking
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0

        # Agent loop: keep calling tools until the agent gives a final response
        for iteration in range(self.max_iterations):
            # Check for cancellation before each iteration
            if cancellation_check and cancellation_check():
                return StepResult(
                    response="Operation cancelled by user.",
                    messages=messages,
                    token_usage={
                        "prompt_tokens": total_prompt_tokens,
                        "completion_tokens": total_completion_tokens,
                        "total_tokens": total_tokens,
                    },
                    status="cancelled",
                )

            # Check for new user input from the queue
            pending_input = input_queue.get_next_message() if input_queue else None
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
                        token_usage={
                            "prompt_tokens": total_prompt_tokens,
                            "completion_tokens": total_completion_tokens,
                            "total_tokens": total_tokens,
                        },
                        additional_data={"iteration": iteration + 1, "step": self.name},
                    )

                response_message = response.choices[0].message

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
                            response="Operation cancelled by user.",
                            messages=messages,
                            token_usage={
                                "prompt_tokens": total_prompt_tokens,
                                "completion_tokens": total_completion_tokens,
                                "total_tokens": total_tokens,
                            },
                            status="cancelled",
                        )

                    messages.extend(result_messages)

                    # Continue the loop to get the next response
                    continue

                # No tool calls, we have a final response
                final_response = response_message.content

                return StepResult(
                    response=final_response,
                    messages=messages,
                    token_usage={
                        "prompt_tokens": total_prompt_tokens,
                        "completion_tokens": total_completion_tokens,
                        "total_tokens": total_tokens,
                    },
                    status="completed",
                )

            except Exception as e:
                return StepResult(
                    response=f"Error during step execution: {str(e)}",
                    messages=messages,
                    token_usage={
                        "prompt_tokens": total_prompt_tokens,
                        "completion_tokens": total_completion_tokens,
                        "total_tokens": total_tokens,
                    },
                    status="error",
                )

        # If we hit max iterations
        return StepResult(
            response="Step reached maximum iterations without completing the task.",
            messages=messages,
            token_usage={
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens,
            },
            status="max_iterations",
        )
