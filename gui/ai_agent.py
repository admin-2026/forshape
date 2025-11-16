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
        model: str,
        max_iterations: int = 10,
        logger: Optional[Logger] = None,
        permission_manager: Optional[PermissionManager] = None,
        image_context = None
    ):
        """
        Initialize the AI agent.

        Args:
            api_key: OpenAI API key
            context_provider: ContextProvider instance for file operations and context
            model: Model identifier to use
            max_iterations: Maximum number of tool calling iterations (default: 10)
            logger: Optional logger for tool call logging
            permission_manager: Optional PermissionManager instance for access control
            image_context: Optional ImageContext instance for screenshot capture
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
            self.permission_manager,
            image_context
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


    def process_request(self, user_input: str, image_data: Optional[Dict] = None) -> str:
        """
        Process the user's request through the AI agent (compatible with AIClient interface).

        This method is designed to be compatible with the existing ForShape GUI code
        that expects an AIClient-like interface.

        Args:
            user_input: The user's input string
            image_data: Optional dict containing captured image data (from capture_screenshot tool)

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
            response = self.run(augmented_input, system_message, image_data)
            return response

        except Exception as e:
            error_msg = f"Error processing AI request: {str(e)}"
            return error_msg

    def run(self, user_message: str, system_message: Optional[str] = None, image_data: Optional[Dict] = None) -> str:
        """
        Run the agent with a user message. The agent will autonomously call tools as needed.

        Args:
            user_message: The user's message/request
            system_message: Optional system message to set context
            image_data: Optional dict or list of dicts containing captured image data (from capture_screenshot tool or dropped images)

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

        # Add user message with optional image(s)
        if image_data:
            # Handle both single image (dict) and multiple images (list)
            images_list = image_data if isinstance(image_data, list) else [image_data]

            # Filter valid images
            valid_images = []
            for img in images_list:
                if img and img.get("success"):
                    base64_image = img.get("image_base64")
                    if base64_image and not base64_image.startswith("Error"):
                        valid_images.append(base64_image)

            # Create message with text and image(s)
            if valid_images:
                messages.append(self._create_multi_image_message(user_message, valid_images))
            else:
                # No valid images, just send text
                messages.append({"role": "user", "content": user_message})
        else:
            # No image, just send text
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

                        # Special handling for screenshot tools - present images to LLM
                        if tool_name == "capture_screenshot":
                            self._add_screenshot_to_conversation(messages, tool_result)

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

    @staticmethod
    def _create_image_url_content(base64_image: str) -> Dict:
        """
        Create an image_url content object for OpenAI messages.

        Args:
            base64_image: Base64-encoded image string

        Returns:
            Image URL content dict
        """
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
                "detail": "high"
            }
        }

    @staticmethod
    def _create_image_message(text: str, base64_image: str) -> Dict:
        """
        Create an OpenAI message with both text and image content.

        Args:
            text: The text content to include with the image
            base64_image: Base64-encoded image string

        Returns:
            Message dict with text and image_url content
        """
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                AIAgent._create_image_url_content(base64_image)
            ]
        }

    @staticmethod
    def _create_multi_image_message(text: str, base64_images: list) -> Dict:
        """
        Create an OpenAI message with text and multiple image content.

        Args:
            text: The text content to include with the images
            base64_images: List of base64-encoded image strings

        Returns:
            Message dict with text and multiple image_url content
        """
        content = [
            {
                "type": "text",
                "text": text
            }
        ]

        # Add all images to the content array
        for base64_image in base64_images:
            content.append(AIAgent._create_image_url_content(base64_image))

        return {
            "role": "user",
            "content": content
        }

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
                    messages.append(self._create_image_message(
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
                        content.append(self._create_image_url_content(base64_image))

                if len(content) > 1:  # More than just the intro text
                    messages.append({
                        "role": "user",
                        "content": content
                    })

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error adding screenshot to conversation: {str(e)}")

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
