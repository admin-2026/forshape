"""
Main window GUI for ForShape AI.

This module provides the interactive GUI interface using PySide2.
"""

from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                                QTextEdit, QLineEdit, QLabel, QGroupBox, QPushButton,
                                QMenuBar, QAction, QDialog, QListWidget, QListWidgetItem,
                                QDialogButtonBox)
from PySide2.QtCore import QCoreApplication, QThread, Signal, Qt, QProcess, QProcessEnvironment
from PySide2.QtGui import QFont, QTextCursor, QColor

import os
import sys
import glob
import io
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ai_agent import AIAgent
    from .history_logger import HistoryLogger
    from .logger import Logger


class PythonFileSelector(QDialog):
    """Dialog for selecting a Python file to run."""

    def __init__(self, python_files, parent=None):
        """
        Initialize the file selector dialog.

        Args:
            python_files: List of Python file paths
            parent: Parent widget
        """
        super().__init__(parent)
        self.selected_file = None
        self.setup_ui(python_files)

    def setup_ui(self, python_files):
        """Setup the dialog UI."""
        self.setWindowTitle("Select Python File to Run")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        # Add label
        label = QLabel("Select a Python file to run:")
        label.setFont(QFont("Consolas", 10))
        layout.addWidget(label)

        # Add list widget
        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Consolas", 9))

        for file_path in python_files:
            item = QListWidgetItem(file_path)
            self.file_list.addItem(item)

        self.file_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.file_list)

        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_item_double_clicked(self, item):
        """Handle double-click on a list item."""
        self.selected_file = item.text()
        self.accept()

    def on_ok_clicked(self):
        """Handle OK button click."""
        current_item = self.file_list.currentItem()
        if current_item:
            self.selected_file = current_item.text()
            self.accept()

    def get_selected_file(self):
        """Return the selected file path."""
        return self.selected_file


class AIWorker(QThread):
    """Worker thread for handling AI API calls asynchronously."""

    # Signal emitted when AI processing is complete (response or error)
    finished = Signal(str, bool)  # (message, is_error)

    def __init__(self, ai_client: 'AIAgent', user_input: str):
        """
        Initialize the AI worker thread.

        Args:
            ai_client: The AIAgent instance
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

    def __init__(self, ai_client: 'AIAgent', history_logger: 'HistoryLogger',
                 logger: 'Logger', special_commands_handler, exit_handler):
        """
        Initialize the main window.

        Args:
            ai_client: The AIAgent instance for AI interactions
            history_logger: The HistoryLogger instance for logging
            logger: The Logger instance for tool call logging
            special_commands_handler: Function to handle special commands
            exit_handler: Function to handle exit
        """
        super().__init__()
        self.ai_client = ai_client
        self.history_logger = history_logger
        self.logger = logger
        self.handle_special_commands = special_commands_handler
        self.handle_exit = exit_handler
        self.is_ai_busy = False  # Track if AI is currently processing
        self.pending_input = ""  # Store pending user input when AI is busy
        self.worker = None  # Current worker thread

        # Connect logger signal to display handler
        if self.logger:
            self.logger.log_message.connect(self.on_log_message)

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface components."""
        self.setWindowTitle("ForShape AI - Interactive 3D Shape Generator")
        self.setMinimumSize(1000, 600)

        # Create menu bar
        menubar = self.menuBar()
        view_menu = menubar.addMenu("View")

        # Add toggle logs action
        self.toggle_logs_action = QAction("Show Logs", self)
        self.toggle_logs_action.setCheckable(True)
        self.toggle_logs_action.triggered.connect(self.toggle_log_panel)
        view_menu.addAction(self.toggle_logs_action)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create horizontal splitter for conversation and log
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Conversation area
        conversation_widget = QWidget()
        conversation_layout = QVBoxLayout(conversation_widget)
        conversation_layout.setContentsMargins(0, 0, 0, 0)

        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setFont(QFont("Consolas", 10))
        conversation_layout.addWidget(self.conversation_display)

        # Right side: Log area
        self.log_widget = QWidget()
        log_layout = QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_label = QLabel("System Logs")
        log_label.setFont(QFont("Consolas", 10, QFont.Bold))
        log_layout.addWidget(log_label)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        self.log_display.setMaximumHeight(600)
        log_layout.addWidget(self.log_display)

        # Add both sides to splitter
        splitter.addWidget(conversation_widget)
        splitter.addWidget(self.log_widget)

        # Set initial splitter sizes (70% conversation, 30% logs)
        splitter.setSizes([700, 300])

        # Hide log panel by default
        self.log_widget.hide()

        main_layout.addWidget(splitter, stretch=1)

        # Create input area with button
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)

        input_label = QLabel("You:")
        self.input_field = QLineEdit()
        self.input_field.setFont(QFont("Consolas", 10))
        self.input_field.setPlaceholderText("Type your message here... (/exit to quit, /help for commands)")
        self.input_field.returnPressed.connect(self.on_user_input)

        # Add Run button
        self.run_button = QPushButton("Run Script")
        self.run_button.setFont(QFont("Consolas", 10))
        self.run_button.setToolTip("Run a Python script from the working directory")
        self.run_button.clicked.connect(self.on_run_script)

        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_field, stretch=1)
        input_layout.addWidget(self.run_button)

        # Add input container to main layout
        main_layout.addWidget(input_container)

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

    def on_log_message(self, level: str, message: str, timestamp: str):
        """
        Handle log messages from the logger.

        Args:
            level: Log level (DEBUG, INFO, WARN, ERROR)
            message: Log message
            timestamp: Timestamp of the log
        """
        # Color code based on log level
        color_map = {
            "DEBUG": "#888888",
            "INFO": "#0066CC",
            "WARN": "#FF8800",
            "ERROR": "#CC0000"
        }
        color = color_map.get(level, "#000000")

        # Format the log message with color
        formatted_log = f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span>'

        # Append to log display
        self.log_display.append(formatted_log)

        # Scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)

    def toggle_log_panel(self):
        """Toggle the visibility of the log panel."""
        if self.log_widget.isVisible():
            self.log_widget.hide()
            self.toggle_logs_action.setText("Show Logs")
            self.toggle_logs_action.setChecked(False)
        else:
            self.log_widget.show()
            self.toggle_logs_action.setText("Hide Logs")
            self.toggle_logs_action.setChecked(True)

    def scan_python_files(self):
        """
        Scan the working directory for Python files.

        Returns:
            List of Python file paths relative to the working directory
        """
        python_files = []

        # Get working directory from context provider
        working_dir = self.ai_client.context_provider.working_dir

        # Find all .py files in the working directory (non-recursive)
        pattern = os.path.join(working_dir, "*.py")
        files = glob.glob(pattern)

        # Convert to relative paths
        for file_path in files:
            rel_path = os.path.relpath(file_path, working_dir)
            python_files.append(rel_path)

        # Sort alphabetically
        python_files.sort()

        return python_files

    def on_run_script(self):
        """Handle Run Script button click."""
        # Scan for Python files
        python_files = self.scan_python_files()

        if not python_files:
            self.append_message("[SYSTEM]", "No Python files found in the working directory.")
            return

        # Show file selector dialog
        dialog = PythonFileSelector(python_files, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_file = dialog.get_selected_file()
            if selected_file:
                self.run_python_file(selected_file)

    def run_python_file(self, file_path):
        """
        Run a Python file in the current Python context (FreeCAD's interpreter).

        Args:
            file_path: Path to the Python file to run
        """
        self.append_message("[SYSTEM]", f"Running: {file_path}")

        # Get absolute path
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            self.display_error(f"File not found: {file_path}")
            return

        # Add project directory to sys.path if not already there
        project_dir = self.ai_client.context_provider.get_project_dir()
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)

        try:
            # Read the script content
            with open(abs_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

            try:
                # Execute the script in the current context
                # This allows it to access FreeCAD's App.activeDocument()
                exec(script_content, {'__name__': '__main__', '__file__': abs_path})

                # Get captured output
                stdout_output = sys.stdout.getvalue()
                stderr_output = sys.stderr.getvalue()

                # Display output if any
                if stdout_output.strip():
                    self.append_message("[OUTPUT]", stdout_output.strip())
                if stderr_output.strip():
                    self.append_message("[STDERR]", stderr_output.strip())

                # Success message
                self.append_message("[SYSTEM]", f"Finished running: {file_path}")

            finally:
                # Restore stdout and stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        except Exception as e:
            # Restore stdout and stderr in case of error
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Format and display the error
            error_msg = f"Error executing {file_path}:\n{traceback.format_exc()}"
            self.display_error(error_msg)

    def closeEvent(self, event):
        """Handle window close event."""
        self.handle_exit()
        event.accept()
