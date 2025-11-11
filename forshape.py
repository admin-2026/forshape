"""
Command-line AI interactive interface for shape generation.

This module provides an interactive command-line interface where users can
interact with an AI to generate, manipulate, and export 3D shapes.

Usage from Python REPL:
    >>> script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
    >>> from forshape import ForShapeAI
    >>> ai = ForShapeAI()
    >>> ai.run()
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from openai import OpenAI


class ForShapeAI:
    """Main class for the AI-powered command-line interface."""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the command-line AI interface.

        Args:
            model: Optional AI model identifier to use
        """
        self.model = model or "gpt-4"
        self.history: List[dict] = []
        self.running = True

        # Setup directories and history logging
        self.base_dir = Path.cwd()
        self.forshape_dir = self.base_dir / ".forshape"
        self.history_dir = self.forshape_dir / "history"
        self.history_file = None
        self.api_key_file = self.forshape_dir / "api-key"

        self._setup_directories()
        self._initialize_history_log()
        self.client = self._initialize_openai_client()

    def _setup_directories(self):
        """Setup .forshape and .forshape/history directories if they don't exist."""
        if not self.forshape_dir.exists():
            self.forshape_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {self.forshape_dir}")

        if not self.history_dir.exists():
            self.history_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {self.history_dir}")

    def _initialize_history_log(self):
        """Initialize history log file based on current date."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.history_file = self.history_dir / f"{today}.log"

        # Create file if it doesn't exist
        if not self.history_file.exists():
            self.history_file.touch()

        # Write session start marker
        with open(self.history_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{'='*60}\n")
            f.write(f"Session started: {timestamp}\n")
            f.write(f"{'='*60}\n\n")

    def _initialize_openai_client(self) -> Optional[OpenAI]:
        """
        Initialize OpenAI client by loading API key from .forshape/api-key file.

        Returns:
            OpenAI client instance or None if API key not found
        """
        try:
            if not self.api_key_file.exists():
                print(f"Warning: API key file not found at {self.api_key_file}")
                print("Please create the file and add your OpenAI API key.")
                return None

            with open(self.api_key_file, 'r', encoding='utf-8') as f:
                api_key = f.read().strip()

            if not api_key:
                print("Warning: API key file is empty.")
                return None

            return OpenAI(api_key=api_key)

        except Exception as e:
            print(f"Error loading API key: {e}")
            return None

    def _log_conversation(self, role: str, content: str):
        """
        Log a conversation message to the history file.

        Args:
            role: The role (user, assistant, system, etc.)
            content: The message content
        """
        if self.history_file is None:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {role.upper()}:\n")
            f.write(f"{content}\n\n")

    def run(self):
        """Start the interactive command-line interface."""
        self.display_welcome()

        while self.running:
            try:
                user_input = self.get_user_input()

                if not user_input:
                    continue

                # Log user input
                self._log_conversation("user", user_input)

                if self.handle_special_commands(user_input):
                    continue

                response = self.process_ai_request(user_input)

                # Log AI response
                self._log_conversation("assistant", response)

                self.display_response(response)

            except KeyboardInterrupt:
                self.handle_exit()
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self._log_conversation("error", error_msg)
                self.display_error(error_msg)

    def display_welcome(self):
        """Display welcome message and usage instructions."""
        print("\n" + "="*60)
        print("Welcome to ForShape AI - Interactive 3D Shape Generator")
        print("="*60)
        print(f"Using model: {self.model}")
        print("\nCommands:")
        print("  /exit - Exit the program")
        print("  /help - Show help (coming soon)")
        print("\nStart chatting to generate 3D shapes!")
        print("="*60 + "\n")

    def get_user_input(self) -> str:
        """
        Get input from the user.

        Returns:
            User input string
        """
        try:
            user_input = input("You: ").strip()
            return user_input
        except EOFError:
            return "/exit"

    def handle_special_commands(self, user_input: str) -> bool:
        """
        Handle special commands like /help, /exit, /clear, etc.

        Args:
            user_input: The user's input string

        Returns:
            True if a special command was handled, False otherwise
        """
        command = user_input.strip().lower()

        if command == "/exit":
            self.handle_exit()
            print("Goodbye!")
            return True

        # TODO: Implement other special commands (/help, /clear, etc.)

        return False

    def process_ai_request(self, user_input: str) -> str:
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

    def display_response(self, response: str):
        """
        Display the AI's response to the user.

        Args:
            response: The AI's response string
        """
        print(f"\nAI: {response}\n")

    def display_error(self, error_message: str):
        """
        Display an error message to the user.

        Args:
            error_message: The error message to display
        """
        print(f"\n[ERROR] {error_message}\n")

    def handle_exit(self):
        """Handle graceful exit of the application."""
        # Log session end
        if self.history_file is not None:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{'='*60}\n")
                f.write(f"Session ended: {timestamp}\n")
                f.write(f"{'='*60}\n\n")

        # TODO: Implement additional exit handling
        self.running = False


def start(model: Optional[str] = None):
    """
    Convenience function to start the interactive interface.

    Args:
        model: Optional AI model identifier to use
    """
    ai = ForShapeAI(model=model)
    ai.run()
