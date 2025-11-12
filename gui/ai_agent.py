"""
AI Agent with tool calling capabilities for ChatGPT/OpenAI API.

This module provides an AI agent that can call tools to interact with the file system,
including listing files, reading files, and editing files.
"""

import json
from typing import List, Dict, Optional

from .context_provider import ContextProvider
from .logger import Logger
from .tool_manager import ToolManager
from .permission_manager import PermissionManager


class AIAgent:
    """
    AI Agent with tool-calling capabilities adapted for ChatGPT/OpenAI API.

    This agent can use tools to interact with the file system and perform
    tasks autonomously through the OpenAI function calling API.
    """

    def __init__(
        self,
        api_key: Optional[str],
        context_provider: ContextProvider,
        model: str = "gpt-4o",
        max_iterations: int = 10,
        logger: Optional[Logger] = None,
        permission_manager: Optional[PermissionManager] = None
    ):
        """
        Initialize the AI agent.

        Args:
            api_key: OpenAI API key
            context_provider: ContextProvider instance for file operations and context
            model: Model identifier to use (default: gpt-4o for tool calling)
            max_iterations: Maximum number of tool calling iterations (default: 10)
            logger: Optional logger for tool call logging
            permission_manager: Optional PermissionManager instance for access control
        """
        self.model = model
        self.max_iterations = max_iterations
        self.history: List[Dict] = []
        self.client = self._initialize_client(api_key)
        self.context_provider = context_provider
        self.permission_manager = permission_manager
        self.tool_manager = ToolManager(
            context_provider.working_dir,
            logger,
            self.permission_manager
        )
        self._system_message_cache = None
        self.logger = logger

    def _initialize_client(self, api_key: Optional[str]):
        """
        Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key

        Returns:
            OpenAI client instance or None if initialization fails
        """
        if not api_key:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            print("Error: OpenAI library not available")
            return None

        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            return None


    def process_request(self, user_input: str) -> str:
        """
        Process the user's request through the AI agent (compatible with AIClient interface).

        This method is designed to be compatible with the existing ForShape GUI code
        that expects an AIClient-like interface.

        Args:
            user_input: The user's input string

        Returns:
            AI response string
        """
        if self.client is None:
            return "Error: OpenAI client not initialized. Please check your API key."

        try:
            # Get system message from context provider (only once, then cache it)
            if self._system_message_cache is None:
                system_message, forshape_context = self.context_provider.get_context(include_agent_tools=True)
                self._system_message_cache = system_message
            else:
                system_message = self._system_message_cache
                forshape_context = self.context_provider.load_forshape_context()

            # Augment user input with FORSHAPE.md context if available
            augmented_input = user_input
            if forshape_context:
                augmented_input = f"[User Context from FORSHAPE.md]\n{forshape_context}\n\n[User Request]\n{user_input}"

            # Use the run method with the context
            response = self.run(augmented_input, system_message)
            return response

        except Exception as e:
            error_msg = f"Error processing AI request: {str(e)}"
            return error_msg

    def run(self, user_message: str, system_message: Optional[str] = None) -> str:
        """
        Run the agent with a user message. The agent will autonomously call tools as needed.

        Args:
            user_message: The user's message/request
            system_message: Optional system message to set context

        Returns:
            Final response from the agent
        """
        if self.client is None:
            return "Error: OpenAI client not initialized. Please check your API key."

        # Initialize messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add conversation history
        messages.extend(self.history)

        # Add user message
        messages.append({"role": "user", "content": user_message})

        # Agent loop: keep calling tools until the agent gives a final response
        for iteration in range(self.max_iterations):
            try:
                # Call OpenAI API with tools
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tool_manager.get_tools(),
                    tool_choice="auto"
                )

                response_message = response.choices[0].message

                # Check if the agent wants to call tools
                if response_message.tool_calls:
                    # Add the assistant's response to messages
                    messages.append(response_message)

                    # Process each tool call
                    for tool_call in response_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        # Execute the tool
                        tool_result = self.tool_manager.execute_tool(tool_name, tool_args)

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_result
                        })

                    # Continue the loop to get the next response
                    continue

                # No tool calls, we have a final response
                final_response = response_message.content

                # Update history
                self.history.append({"role": "user", "content": user_message})
                self.history.append({"role": "assistant", "content": final_response})

                return final_response

            except Exception as e:
                return f"Error during agent execution: {str(e)}"

        # If we hit max iterations
        return "Agent reached maximum iterations without completing the task."

    def get_history(self) -> List[Dict]:
        """
        Get the conversation history.

        Returns:
            List of message dictionaries
        """
        return self.history

    def clear_history(self):
        """Clear the conversation history."""
        self.history = []

    def is_available(self) -> bool:
        """
        Check if the AI agent is available and ready.

        Returns:
            True if client is initialized, False otherwise
        """
        return self.client is not None

    def get_working_dir(self) -> str:
        """
        Get the current working directory for file operations.

        Returns:
            Working directory path as string
        """
        return self.context_provider.working_dir

    def get_model(self) -> str:
        """
        Get the model identifier being used.

        Returns:
            Model identifier string
        """
        return self.model
