"""
AI client for ForShape AI.

This module handles interaction with the OpenAI API for generating responses.
"""

from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AIClient:
    """Handles interaction with OpenAI API."""

    def __init__(self, api_key: Optional[str], model: str = "gpt-4"):
        """
        Initialize the AI client.

        Args:
            api_key: OpenAI API key
            model: Model identifier to use (default: gpt-4)
        """
        self.model = model
        self.history: List[dict] = []
        self.client = self._initialize_client(api_key)

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

        if OpenAI is None:
            print("Error: OpenAI library not available")
            return None

        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            return None

    def process_request(self, user_input: str) -> str:
        """
        Process the user's request through the AI.

        Args:
            user_input: The user's input string

        Returns:
            AI response string
        """
        if self.client is None:
            return "Error: OpenAI client not initialized. Please check your API key."

        try:
            # Add user message to history
            self.history.append({
                "role": "user",
                "content": user_input
            })

            # Create system message for shape generation context
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant helping users create and manipulate 3D shapes using Python code. You can help generate shapes, apply transformations, and export models."
                }
            ] + self.history

            # Make API call to ChatGPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            # Extract response content
            assistant_message = response.choices[0].message.content

            # Add assistant response to history
            self.history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            error_msg = f"Error processing AI request: {str(e)}"
            return error_msg

    def get_history(self) -> List[dict]:
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
        Check if the AI client is available and ready.

        Returns:
            True if client is initialized, False otherwise
        """
        return self.client is not None

    def get_model(self) -> str:
        """
        Get the model identifier being used.

        Returns:
            Model identifier string
        """
        return self.model
