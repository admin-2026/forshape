"""
AI Agent with tool calling capabilities for multiple API providers.

This module provides an AI agent that can call tools to interact with the file system,
including listing files, reading files, and editing files.

Supports multiple API providers: OpenAI, Fireworks, and more.
"""

import json
from typing import List, Dict, Optional

from .request import RequestBuilder, Instruction, MessageElement, TextMessage
from .tools.tool_manager import ToolManager
from .api_debugger import APIDebugger
from .chat_history_manager import ChatHistoryManager
from .api_provider import APIProvider, create_api_provider

from .logger_protocol import LoggerProtocol
from .user_input_queue import UserInputQueue


class AIAgent:
    """
    AI Agent with tool-calling capabilities for multiple API providers.

    This agent can use tools to interact with the file system and perform
    tasks autonomously through function calling APIs (OpenAI, Fireworks, etc.).
    """

    def __init__(
        self,
        api_key: Optional[str],
        request_builder: RequestBuilder,
        model: str,
        logger: LoggerProtocol,
        tool_manager: ToolManager,
        max_iterations: int = 50,
        api_debugger: Optional[APIDebugger] = None,
        provider: str = "openai",
        provider_config = None
    ):
        """
        Initialize the AI agent.

        Args:
            api_key: API key for the selected provider
            request_builder: RequestBuilder instance for building request context
            model: Model identifier to use
            logger: LoggerProtocol instance for tool call logging
            tool_manager: ToolManager instance with registered tools
            max_iterations: Maximum number of tool calling iterations (default: 50)
            api_debugger: Optional APIDebugger instance for dumping API data
            provider: API provider to use ("openai", "fireworks", etc.)
            provider_config: Optional ProviderConfig instance for provider configuration
        """
        # Set logger first so it's available in _initialize_provider
        self.logger = logger

        self.model = model
        self.max_iterations = max_iterations
        self.history_manager = ChatHistoryManager(max_messages=None)
        self.provider = self._initialize_provider(provider, api_key, provider_config)
        self.provider_name = provider
        self.request_builder = request_builder

        # Use injected tool manager (tools already registered by caller)
        self.tool_manager = tool_manager

        self.last_token_usage = None  # Store the most recent token usage data
        self._cancellation_requested = False  # Flag to track cancellation requests
        self.api_debugger = api_debugger
        self._conversation_counter = 0  # Counter for generating unique conversation IDs

    def _initialize_provider(self, provider_name: str, api_key: Optional[str], provider_config=None) -> Optional[APIProvider]:
        """
        Initialize the API provider.

        Args:
            provider_name: Name of the provider ("openai", "fireworks", etc.)
            api_key: API key for authentication
            provider_config: Optional ProviderConfig instance for provider configuration

        Returns:
            APIProvider instance or None if initialization fails
        """
        if not api_key:
            return None

        try:
            from .api_provider import create_api_provider_from_config
            if provider_config:
                provider = create_api_provider_from_config(provider_config, api_key)
            else:
                provider = create_api_provider(provider_name, api_key)

            if not provider.is_available():
                print(f"Error: {provider_name} provider not available")
                return None

            return provider
        except ValueError as e:
            print(f"Error: {e}")
            return None
        except Exception as e:
            print(f"Error initializing {provider_name} provider: {e}")
            return None

    def _generate_conversation_id(self) -> str:
        """
        Generate a unique conversation ID.

        Each conversation represents a user request and all subsequent AI agent work
        until a final response is given.

        Returns:
            Unique conversation ID string
        """
        from datetime import datetime
        self._conversation_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"conv_{timestamp}_{self._conversation_counter:03d}"


    def process_request(self, input_queue: 'UserInputQueue', initial_messages: Optional[List[MessageElement]] = None, token_callback=None) -> str:
        """
        Process the user's request through the AI agent (compatible with AIClient interface).

        This method is designed to be compatible with the existing ForShape GUI code
        that expects an AIClient-like interface.

        Args:
            input_queue: The user input queue containing the initial message and any follow-up messages
            initial_messages: Optional list of MessageElement objects for additional content
                              (e.g., images with descriptions)
            token_callback: Optional callback function to receive token usage updates after each iteration

        Returns:
            AI response string
        """
        if self.provider is None:
            return f"Error: {self.provider_name} provider not initialized. Please check your API key."

        try:
            # Get the initial message from the queue
            initial_message = input_queue.get_initial_message()

            # Generate a new conversation ID for this user request
            # Each user request begins a new conversation in the edit history
            conversation_id = self._generate_conversation_id()
            self.tool_manager.start_conversation(conversation_id, user_request=initial_message)
            self.history_manager.set_conversation_id(conversation_id)
            self.logger.info(f"Started new conversation: {conversation_id}")

            # Use the run method with the context and input queue
            response = self.run(initial_message, initial_messages, token_callback, input_queue)
            return response

        except Exception as e:
            error_msg = f"Error processing AI request: {str(e)}"
            return error_msg

    def request_cancellation(self):
        """Request cancellation of the current AI processing."""
        self._cancellation_requested = True

    def reset_cancellation(self):
        """Reset the cancellation flag for new requests."""
        self._cancellation_requested = False

    def run(self, user_message: str, initial_messages: Optional[List[MessageElement]] = None, token_callback=None, input_queue: Optional[UserInputQueue] = None) -> str:
        """
        Run the agent with a user message. The agent will autonomously call tools as needed.

        Args:
            user_message: The user's message/request
            initial_messages: Optional list of MessageElement objects for additional content
                              (e.g., images with descriptions)
            token_callback: Optional callback function to receive token usage updates after each iteration
            input_queue: Optional UserInputQueue to check for new user input during iterations

        Returns:
            Final response from the agent
        """
        if self.provider is None:
            return f"Error: {self.provider_name} provider not initialized. Please check your API key."

        # Reset cancellation flag at the start of each run
        self.reset_cancellation()

        # Build messages for API call (system message + history + user message)
        init_user_message = Instruction(user_message, description="User Request")

        messages = self.request_builder.build_messages(
            self.history_manager.get_history(),
            [init_user_message],
            initial_messages
        )

        self.history_manager.add_user_message(user_message)

        # Initialize token usage tracking
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0

        # Agent loop: keep calling tools until the agent gives a final response
        for iteration in range(self.max_iterations):
            # Check for cancellation before each iteration
            if self._cancellation_requested:
                return "Operation cancelled by user."

            # Check for new user input from the queue
            if input_queue:
                pending_input = input_queue.get_next_message()
                if pending_input:
                    self.history_manager.add_user_message(pending_input)
                    # Append the new user message to the conversation
                    messages.append(TextMessage("user", pending_input).get_message())
                    self.logger.info(f"New user input received during iteration {iteration + 1}: {pending_input}")

            try:
                # Dump request data if debugger is enabled
                if self.api_debugger:
                    self.api_debugger.dump_request(
                        model=self.model,
                        messages=messages,
                        tools=self.tool_manager.get_tools(),
                        tool_choice="auto",
                        additional_data={"iteration": iteration + 1}
                    )

                # Call API provider with tools
                response = self.provider.create_completion(
                    model=self.model,
                    messages=messages,
                    tools=self.tool_manager.get_tools(),
                    tool_choice="auto"
                )

                # Track token usage from this API call
                if hasattr(response, 'usage') and response.usage:
                    total_prompt_tokens += response.usage.prompt_tokens
                    total_completion_tokens += response.usage.completion_tokens
                    total_tokens += response.usage.total_tokens

                    # Send token usage update via callback if provided
                    if token_callback:
                        token_data = {
                            "prompt_tokens": total_prompt_tokens,
                            "completion_tokens": total_completion_tokens,
                            "total_tokens": total_tokens,
                            "iteration": iteration + 1
                        }
                        token_callback(token_data)

                # Dump response data if debugger is enabled
                if self.api_debugger:
                    self.api_debugger.dump_response(
                        response=response,
                        token_usage={
                            "prompt_tokens": total_prompt_tokens,
                            "completion_tokens": total_completion_tokens,
                            "total_tokens": total_tokens
                        },
                        additional_data={"iteration": iteration + 1}
                    )

                response_message = response.choices[0].message

                # Check if the agent wants to call tools
                if response_message.tool_calls:
                    # Add the assistant's message (with tool_calls) to messages first
                    # This is required before adding tool result messages
                    messages.append(response_message.model_dump())

                    # Process each tool call
                    for tool_call in response_message.tool_calls:
                        # Check for cancellation during tool execution
                        if self._cancellation_requested:
                            return "Operation cancelled by user."

                        tool_name = tool_call.function.name
                        raw_arguments = tool_call.function.arguments
                        try:
                            tool_args = json.loads(raw_arguments)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"JSON parsing failed for tool '{tool_name}'")
                            self.logger.error(f"Error: {e}")
                            self.logger.error(f"Raw arguments (len={len(raw_arguments)}): {raw_arguments[:500]}...")
                            if len(raw_arguments) > 500:
                                self.logger.error(f"...end of raw arguments: ...{raw_arguments[-200:]}")
                            raise

                        # Execute the tool
                        tool_result = self.tool_manager.execute_tool(tool_name, tool_args)

                        # Dump tool execution data if debugger is enabled
                        if self.api_debugger:
                            self.api_debugger.dump_tool_execution(
                                tool_name=tool_name,
                                tool_arguments=tool_call.function.arguments,
                                tool_result=tool_result,
                                tool_call_id=tool_call.id
                            )

                        # Get the provider and let it process the result
                        provider = self.tool_manager.get_provider(tool_name)
                        if provider:
                            result_messages = provider.process_result(
                                tool_call.id, tool_name, tool_result
                            )
                            for result_message in result_messages:
                                message_dict = result_message.get_message()
                                if message_dict:
                                    messages.append(message_dict)

                    # Continue the loop to get the next response
                    continue

                # No tool calls, we have a final response
                final_response = response_message.content

                # Store token usage data
                self.last_token_usage = {
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "total_tokens": total_tokens
                }

                # Update history through history manager
                self.history_manager.add_assistant_message(final_response)

                return final_response

            except Exception as e:
                return f"Error during agent execution: {str(e)}"

        # If we hit max iterations
        return "Agent reached maximum iterations without completing the task."

    def clear_history(self):
        """Clear the conversation history."""
        self.history_manager.clear_history()

    def get_history_manager(self) -> ChatHistoryManager:
        """
        Get the ChatHistoryManager instance for advanced history operations.

        Returns:
            ChatHistoryManager instance
        """
        return self.history_manager

    def get_model(self) -> str:
        """
        Get the model identifier being used.

        Returns:
            Model identifier string
        """
        return self.model

    def set_model(self, model: str):
        """
        Set the model identifier to use for future requests.

        Args:
            model: Model identifier string
        """
        self.model = model
        self.logger.info(f"Model changed to: {model}")

    def get_last_token_usage(self) -> Optional[Dict]:
        """
        Get the token usage data from the most recent request.

        Returns:
            Dict with 'prompt_tokens', 'completion_tokens', and 'total_tokens' keys,
            or None if no request has been made yet
        """
        return self.last_token_usage
