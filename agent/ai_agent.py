"""
AI Agent with tool calling capabilities for multiple API providers.

This module provides an AI agent that can call tools to interact with the file system,
including listing files, reading files, and editing files.

Supports multiple API providers: OpenAI, Fireworks, and more.
"""

import json
from typing import List, Dict, Optional

from .context_provider import ContextProvider
from .request import RequestBuilder
from .tools.tool_manager import ToolManager
from .api_debugger import APIDebugger
from .chat_history_manager import ChatHistoryManager
from .api_provider import APIProvider, create_api_provider

from .logger_protocol import LoggerProtocol
from .user_input_queue import UserInputQueue
from .async_ops import WaitManager, PermissionInput


class AIAgent:
    """
    AI Agent with tool-calling capabilities for multiple API providers.

    This agent can use tools to interact with the file system and perform
    tasks autonomously through function calling APIs (OpenAI, Fireworks, etc.).
    """

    def __init__(
        self,
        api_key: Optional[str],
        context_provider: ContextProvider,
        request_builder: RequestBuilder,
        model: str,
        logger: LoggerProtocol,
        tool_manager: ToolManager,
        wait_manager: WaitManager,
        permission_input: PermissionInput,
        max_iterations: int = 50,
        api_debugger: Optional[APIDebugger] = None,
        provider: str = "openai",
        provider_config = None
    ):
        """
        Initialize the AI agent.

        Args:
            api_key: API key for the selected provider
            context_provider: ContextProvider instance for file operations and context
            request_builder: RequestBuilder instance for building request context
            model: Model identifier to use
            logger: LoggerProtocol instance for tool call logging
            tool_manager: ToolManager instance with registered tools
            wait_manager: WaitManager instance for user interactions
            permission_input: PermissionInput instance for permission requests
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
        self.context_provider = context_provider
        self.request_builder = request_builder

        # Use injected managers for user interactions and permissions
        self.wait_manager = wait_manager
        self.permission_input = permission_input

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


    def process_request(self, image_data: Optional[Dict] = None, token_callback=None) -> str:
        """
        Process the user's request through the AI agent (compatible with AIClient interface).

        This method is designed to be compatible with the existing ForShape GUI code
        that expects an AIClient-like interface.

        Note: input_queue must be set on request_builder before calling this method.

        Args:
            image_data: Optional dict containing captured image data (from capture_screenshot tool)
            token_callback: Optional callback function to receive token usage updates after each iteration

        Returns:
            AI response string
        """
        if self.provider is None:
            return f"Error: {self.provider_name} provider not initialized. Please check your API key."

        try:
            # Build system message and augmented input (gets initial_message from input_queue)
            system_message, augmented_input, initial_message = self.request_builder.build_request(
                self.tool_manager
            )

            # Generate a new conversation ID for this user request
            # Each user request begins a new conversation in the edit history
            conversation_id = self._generate_conversation_id()
            self.tool_manager.start_conversation(conversation_id, user_request=initial_message)
            self.history_manager.set_conversation_id(conversation_id)
            self.logger.info(f"Started new conversation: {conversation_id}")

            # Use the run method with the context and input queue
            response = self.run(augmented_input, system_message, image_data, token_callback, self.request_builder.input_queue)
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

    def run(self, user_message: str, system_message: Optional[str] = None, image_data: Optional[Dict] = None, token_callback=None, input_queue: Optional[UserInputQueue] = None) -> str:
        """
        Run the agent with a user message. The agent will autonomously call tools as needed.

        Args:
            user_message: The user's message/request
            system_message: Optional system message to set context
            image_data: Optional dict or list of dicts containing captured image data (from capture_screenshot tool or dropped images)
            token_callback: Optional callback function to receive token usage updates after each iteration
            input_queue: Optional UserInputQueue to check for new user input during iterations

        Returns:
            Final response from the agent
        """
        if self.provider is None:
            return f"Error: {self.provider_name} provider not initialized. Please check your API key."

        # Reset cancellation flag at the start of each run
        self.reset_cancellation()

        # Get messages for API call (system message + history)
        # System message is NOT stored in history, just prepended for the API call
        messages = self.history_manager.get_context_for_api(system_message=system_message)

        # Add user message with optional image(s) using RequestBuilder
        messages.append(self.request_builder.build_user_message(user_message, image_data))

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
                    # Append the new user message to the conversation
                    messages.append({"role": "user", "content": pending_input})
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
                    # Add the assistant's response to messages
                    messages.append(response_message)

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

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_result
                        })

                        # Special handling for screenshot tools - present images to LLM
                        if tool_name == "capture_screenshot":
                            self._add_screenshot_to_conversation(messages, tool_result)

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
                self.history_manager.add_user_message(user_message)
                self.history_manager.add_assistant_message(final_response)

                return final_response

            except Exception as e:
                return f"Error during agent execution: {str(e)}"

        # If we hit max iterations
        return "Agent reached maximum iterations without completing the task."

    def _add_screenshot_to_conversation(self, messages: List[Dict], tool_result: str):
        """
        Parse screenshot tool result and add images to conversation for LLM to see.

        Args:
            messages: The conversation messages list
            tool_result: The JSON string returned from capture_screenshot tool
        """
        try:
            result_data = json.loads(tool_result)

            if not result_data.get("success"):
                return

            # Check if we have single or multiple images
            if "image_base64" in result_data:
                # Single image
                base64_image = result_data["image_base64"]
                if base64_image and not base64_image.startswith("Error"):
                    messages.append(RequestBuilder.create_image_message(
                        "Here is the screenshot that was just captured:",
                        base64_image
                    ))

            elif "images" in result_data:
                # Multiple images
                content = [{"type": "text", "text": "Here are the screenshots that were just captured:"}]

                for perspective, image_data in result_data["images"].items():
                    base64_image = image_data.get("image_base64")
                    if base64_image and not base64_image.startswith("Error"):
                        content.append({"type": "text", "text": f"\n{perspective} view:"})
                        content.append(RequestBuilder.create_image_url_content(base64_image))

                if len(content) > 1:  # More than just the intro text
                    messages.append({
                        "role": "user",
                        "content": content
                    })

        except Exception as e:
            self.logger.error(f"Error adding screenshot to conversation: {str(e)}")

    def get_history(self) -> List[Dict]:
        """
        Get the conversation history.

        Returns:
            List of message dictionaries
        """
        return self.history_manager.get_history()

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
