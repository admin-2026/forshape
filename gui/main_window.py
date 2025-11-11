"""
Main window GUI for ForShape AI.

This module provides the interactive GUI interface using PySide2.
"""

from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                                QTextEdit, QLineEdit, QLabel)
from PySide2.QtCore import QCoreApplication, QThread, Signal
from PySide2.QtGui import QFont, QTextCursor

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ai_client import AIClient
    from .history_logger import HistoryLogger


class AIWorker(QThread):
    """Worker thread for handling AI API calls asynchronously."""

    # Signal emitted when AI processing is complete (response or error)
    finished = Signal(str, bool)  # (message, is_error)

    def __init__(self, ai_client: 'AIClient', user_input: str):
        """
        Initialize the AI worker thread.

        Args:
            ai_client: The AIClient instance
            user_input: The user's input to process
        """
        super().__init__()
        self.ai_client = ai_client
        self.user_input = user_input

    def run(self):
        """Run the AI request in a separate thread."""
        try:
            response = self.ai_client.process_request(self.user_input)
            self.finished.emit(response, False)  # False = not an error
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.finished.emit(error_msg, True)  # True = is an error


class ForShapeMainWindow(QMainWindow):
    """Main window for the ForShape AI GUI application."""

    def __init__(self, ai_client: 'AIClient', history_logger: 'HistoryLogger',
                 special_commands_handler, exit_handler):
        """
        Initialize the main window.

        Args:
            ai_client: The AIClient instance for AI interactions
            history_logger: The HistoryLogger instance for logging
            special_commands_handler: Function to handle special commands
            exit_handler: Function to handle exit
        """
        super().__init__()
        self.ai_client = ai_client
        self.history_logger = history_logger
        self.handle_special_commands = special_commands_handler
        self.handle_exit = exit_handler
        self.is_ai_busy = False  # Track if AI is currently processing
        self.pending_input = ""  # Store pending user input when AI is busy
        self.worker = None  # Current worker thread
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
        context_status = "✓ FORSHAPE.md loaded" if self.ai_client.context_provider.has_forshape() else "✗ No FORSHAPE.md"
        welcome_text = f"""
{'='*60}
Welcome to ForShape AI - Interactive 3D Shape Generator
{'='*60}
Using model: {self.ai_client.get_model()}
Context: {context_status}

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

        # Check if AI is currently busy
        if self.is_ai_busy:
            # Show message that AI is busy without clearing the input
            self.append_message("[SYSTEM]", "⚠ AI is currently processing. Please wait...")
            return

        # Display user input
        self.append_message("You", user_input)

        # Clear input field
        self.input_field.clear()

        # Force UI to update immediately
        QCoreApplication.processEvents()

        # Log user input
        self.history_logger.log_conversation("user", user_input)

        # Handle special commands
        if self.handle_special_commands(user_input, self):
            if user_input.strip().lower() == "/exit":
                self.close()
            return

        # Show in-progress indicator
        self.append_message("AI", "⏳ Processing...")

        # Force UI to update to show the processing indicator
        QCoreApplication.processEvents()

        # Set busy state
        self.is_ai_busy = True

        # Create and start worker thread for AI processing
        self.worker = AIWorker(self.ai_client, user_input)
        self.worker.finished.connect(self.on_ai_response)
        self.worker.start()

    def on_ai_response(self, message: str, is_error: bool):
        """
        Handle AI response from worker thread.

        Args:
            message: The response message or error message
            is_error: True if this is an error message, False otherwise
        """
        # Remove the "Processing..." message
        self.remove_last_message()

        # Display the response or error
        if is_error:
            self.history_logger.log_conversation("error", message)
            self.display_error(message)
        else:
            self.history_logger.log_conversation("assistant", message)
            self.append_message("AI", message)

        # Reset busy state
        self.is_ai_busy = False

        # Clean up worker thread
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

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

    def remove_last_message(self):
        """Remove the last message from the conversation display."""
        # Get current text
        text = self.conversation_display.toPlainText()

        # Find the last occurrence of a message (starting with \n)
        lines = text.split('\n')

        # Remove trailing empty lines and the last message block
        while lines and not lines[-1].strip():
            lines.pop()

        # Remove the last message line (e.g., "AI: Processing...")
        if lines:
            lines.pop()

        # Remove the empty line before the message if present
        while lines and not lines[-1].strip():
            lines.pop()

        # Set the modified text back
        self.conversation_display.setPlainText('\n'.join(lines) + '\n')

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
        self.handle_exit()
        event.accept()
