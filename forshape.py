"""
GUI AI interactive interface for shape generation.

This module provides an interactive GUI interface using PySide2 where users can
interact with an AI to generate, manipulate, and export 3D shapes.

Usage from Python REPL:
    >>> script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
    >>> from forshape import ForShapeAI
    >>> ai = ForShapeAI()
    >>> ai.run()
"""

# from importlib import reload
# reload(forshape); from forshape import ForShapeAI; ai = ForShapeAI(); ai.run()

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                QTextEdit, QLineEdit, QLabel, QSplitter, QMessageBox)
from PySide2.QtCore import Qt, Signal, QObject
from PySide2.QtGui import QFont, QTextCursor

# Module-level flag to track if OpenAI is available
_OPENAI_AVAILABLE = False
_OPENAI_ERROR_MESSAGE = ""

# Setup local library directory - subdirectory where forshape.py lives
_LOCAL_LIB_DIR = Path(__file__).parent / "libs"

# Check if openai is installed
def check_and_install_openai():
    """
    Check if openai library is installed. If not, prompt user to install it locally.

    Returns:
        tuple: (success: bool, error_message: str)
    """
    # Add local library directory to sys.path if it exists
    if _LOCAL_LIB_DIR.exists() and str(_LOCAL_LIB_DIR) not in sys.path:
        sys.path.insert(0, str(_LOCAL_LIB_DIR))

    try:
        import openai
        return True, ""
    except ImportError:
        # Create a minimal QApplication if it doesn't exist (needed for dialog)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Ask user if they want to install
        reply = QMessageBox.question(
            None,
            'OpenAI Library Not Found',
            'The OpenAI library is required but not installed.\n\n'
            'Would you like to install it now using pip?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.No:
            QMessageBox.information(
                None,
                'Installation Cancelled',
                'OpenAI library is required to run ForShape AI.\n\n'
                'Module will load but cannot be used.'
            )
            return False, "OpenAI library not installed. User declined installation."

        # Try to install openai
        try:
            QMessageBox.information(
                None,
                'Installing',
                f'Installing OpenAI library to:\n{_LOCAL_LIB_DIR}\n\n'
                'This may take a moment. Click OK to continue.',
                QMessageBox.Ok
            )

            # Create the libs subdirectory if it doesn't exist
            _LOCAL_LIB_DIR.mkdir(parents=True, exist_ok=True)

            # Install openai to the libs subdirectory using pip with --target flag
            subprocess.check_call(['pip', 'install', '--target', str(_LOCAL_LIB_DIR), 'openai'])

            # Add the local library directory to sys.path
            if str(_LOCAL_LIB_DIR) not in sys.path:
                sys.path.insert(0, str(_LOCAL_LIB_DIR))

            QMessageBox.information(
                None,
                'Installation Complete',
                f'OpenAI library has been successfully installed!\n\n'
                f'Location: {_LOCAL_LIB_DIR}\n\n'
                'The application will now start.',
                QMessageBox.Ok
            )
            return True, ""

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install OpenAI library: {str(e)}"
            QMessageBox.critical(
                None,
                'Installation Failed',
                f'{error_msg}\n\n'
                f'Please install manually using:\npip install --target {_LOCAL_LIB_DIR} openai',
                QMessageBox.Ok
            )
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during installation: {str(e)}"
            QMessageBox.critical(
                None,
                'Installation Error',
                f'{error_msg}\n\n'
                f'Please install manually using:\npip install --target {_LOCAL_LIB_DIR} openai',
                QMessageBox.Ok
            )
            return False, error_msg

# Check for openai before importing
_OPENAI_AVAILABLE, _OPENAI_ERROR_MESSAGE = check_and_install_openai()

if _OPENAI_AVAILABLE:
    from openai import OpenAI
else:
    OpenAI = None  # Placeholder when OpenAI is not available


class ForShapeMainWindow(QMainWindow):
    """Main window for the ForShape AI GUI application."""

    def __init__(self, ai_instance):
        """
        Initialize the main window.

        Args:
            ai_instance: The ForShapeAI instance to connect with
        """
        super().__init__()
        self.ai = ai_instance
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface components."""
        self.setWindowTitle("ForShape AI - Interactive 3D Shape Generator")
        self.setMinimumSize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create conversation display area (read-only)
        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setFont(QFont("Consolas", 10))

        # Create input field
        input_label = QLabel("You:")
        self.input_field = QLineEdit()
        self.input_field.setFont(QFont("Consolas", 10))
        self.input_field.setPlaceholderText("Type your message here... (/exit to quit, /help for commands)")
        self.input_field.returnPressed.connect(self.on_user_input)

        # Add widgets to layout
        layout.addWidget(self.conversation_display, stretch=1)
        layout.addWidget(input_label)
        layout.addWidget(self.input_field)

        # Display welcome message
        self.display_welcome()

    def display_welcome(self):
        """Display welcome message in the conversation area."""
        welcome_text = f"""
{'='*60}
Welcome to ForShape AI - Interactive 3D Shape Generator
{'='*60}
Using model: {self.ai.model}

Commands:
  /exit - Exit the program
  /help - Show help (coming soon)

Start chatting to generate 3D shapes!
{'='*60}

"""
        self.conversation_display.append(welcome_text)

    def on_user_input(self):
        """Handle user input when Enter is pressed."""
        user_input = self.input_field.text().strip()

        if not user_input:
            return

        # Display user input
        self.append_message("You", user_input)

        # Clear input field
        self.input_field.clear()

        # Log user input
        self.ai._log_conversation("user", user_input)

        # Handle special commands
        if self.ai.handle_special_commands(user_input):
            if user_input.strip().lower() == "/exit":
                self.close()
            return

        # Process AI request
        try:
            response = self.ai.process_ai_request(user_input)
            self.ai._log_conversation("assistant", response)
            self.append_message("AI", response)
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.ai._log_conversation("error", error_msg)
            self.display_error(error_msg)

    def append_message(self, role: str, message: str):
        """
        Append a message to the conversation display.

        Args:
            role: The role (You, AI, Error, etc.)
            message: The message content
        """
        formatted_message = f"\n{role}: {message}\n"
        self.conversation_display.append(formatted_message)

        # Scroll to bottom
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conversation_display.setTextCursor(cursor)

    def display_error(self, error_message: str):
        """
        Display an error message.

        Args:
            error_message: The error message to display
        """
        self.append_message("[ERROR]", error_message)

    def closeEvent(self, event):
        """Handle window close event."""
        self.ai.handle_exit()
        event.accept()


class ForShapeAI:
    """Main class for the AI-powered GUI interface."""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the GUI AI interface.

        Args:
            model: Optional AI model identifier to use
        """
        # Check if OpenAI is available
        if not _OPENAI_AVAILABLE:
            print(f"\nError: Cannot initialize ForShapeAI - {_OPENAI_ERROR_MESSAGE}")
            print("Please install the OpenAI library to use ForShape AI.\n")
            raise RuntimeError(f"ForShapeAI requires OpenAI library: {_OPENAI_ERROR_MESSAGE}")

        self.model = model or "gpt-4"
        self.history: List[dict] = []
        self.running = True
        self.main_window = None

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

    def _initialize_openai_client(self):
        """
        Initialize the OpenAI client using API key from file or environment.

        Returns:
            OpenAI client instance or None if initialization fails
        """
        api_key = None

        # Try to read API key from file
        if self.api_key_file.exists():
            try:
                with open(self.api_key_file, 'r', encoding='utf-8') as f:
                    api_key = f.read().strip()
            except Exception as e:
                print(f"Error reading API key file: {e}")

        # Fall back to environment variable
        if not api_key:
            api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            print("\nWarning: No OpenAI API key found!")
            print(f"Please either:")
            print(f"  1. Save your API key to: {self.api_key_file}")
            print(f"  2. Set the OPENAI_API_KEY environment variable")
            print("\nThe application will run but AI features will not work.\n")
            return None

        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
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
        """Start the interactive GUI interface."""
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Create and show main window
        self.main_window = ForShapeMainWindow(self)
        self.main_window.show()

        # Start Qt event loop
        return app.exec_()

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
            return True

        if command == "/help":
            if self.main_window:
                help_text = """Available commands:
  /exit - Exit the program
  /help - Show this help message
  /clear - Clear conversation history (coming soon)

Simply type your questions or requests to interact with the AI."""
                self.main_window.append_message("System", help_text)
            return True

        # TODO: Implement other special commands (/clear, etc.)

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
