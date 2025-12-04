"""
Main window GUI for ForShape AI.

This module provides the interactive GUI interface using PySide2.
"""

from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                                QTextEdit, QLineEdit, QLabel, QPushButton,
                                QAction, QDialog, QComboBox, QWidgetAction)
from PySide2.QtCore import QCoreApplication, Qt, QUrl
from PySide2.QtGui import QFont, QTextCursor, QDragEnterEvent, QDropEvent

import os
import sys
import glob
import io
import traceback
from typing import TYPE_CHECKING

from .dialogs import PythonFileSelector, ImagePreviewDialog
from .workers import AIWorker
from .formatters import MessageFormatter
from .logger import LogLevel
from .script_executor import ScriptExecutor, ExecutionMode

if TYPE_CHECKING:
    from .ai_agent import AIAgent
    from .history_logger import HistoryLogger
    from .logger import Logger


class MultiLineInputField(QTextEdit):
    """Custom QTextEdit for multi-line user input with Enter to submit."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.submit_callback = None

    def keyPressEvent(self, event):
        """Handle key press events. Enter submits, Shift+Enter adds new line."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ShiftModifier:
                # Shift+Enter: insert new line
                super().keyPressEvent(event)
            else:
                # Plain Enter: submit
                if self.submit_callback:
                    self.submit_callback()
                event.accept()
        else:
            super().keyPressEvent(event)


class ForShapeMainWindow(QMainWindow):
    """Main window for the ForShape AI GUI application."""

    def __init__(self, ai_client: 'AIAgent', history_logger: 'HistoryLogger',
                 logger: 'Logger', context_provider, exit_handler,
                 image_context=None, prestart_checker=None, completion_callback=None, window_close_callback=None):
        """
        Initialize the main window.

        Args:
            ai_client: The AIAgent instance for AI interactions (can be None initially)
            history_logger: The HistoryLogger instance for logging (can be None initially)
            logger: The Logger instance for tool call logging
            context_provider: The ContextProvider instance for accessing working directory and project info
            exit_handler: Function to handle exit
            image_context: Optional ImageContext instance for capturing screenshots
            prestart_checker: Optional PrestartChecker instance for prestart validation
            completion_callback: Optional callback to complete initialization after checks pass
            window_close_callback: Optional callback to call when window is closed
        """
        super().__init__()
        self.ai_client = ai_client
        self.history_logger = history_logger
        self.logger = logger
        self.context_provider = context_provider
        self.image_context = image_context
        self.handle_exit = exit_handler
        self.is_ai_busy = False  # Track if AI is currently processing
        self.pending_input = ""  # Store pending user input when AI is busy
        self.worker = None  # Current worker thread
        self.captured_images = []  # Store captured images to attach to next message
        self.attached_files = []  # Store attached Python files to include in next message
        self.api_debugger = None  # API debugger instance (will be set later)

        # Prestart check mode
        self.prestart_checker = prestart_checker
        self.prestart_check_mode = True if prestart_checker else False  # Start in prestart check mode if checker provided
        self.completion_callback = completion_callback
        self.window_close_callback = window_close_callback

        # Connect logger signal to display handler
        if self.logger:
            self.logger.log_message.connect(self.on_log_message)


        # Initialize message formatter
        self.message_formatter = MessageFormatter(self.logger)

        # Enable drag and drop
        self.setAcceptDrops(True)

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

        # Add toggle API dump action
        self.toggle_api_dump_action = QAction("Dump API Data", self)
        self.toggle_api_dump_action.setCheckable(True)
        self.toggle_api_dump_action.triggered.connect(self.toggle_api_dump)
        view_menu.addAction(self.toggle_api_dump_action)

        # Add dump history action
        self.dump_history_action = QAction("Dump History", self)
        self.dump_history_action.triggered.connect(self.dump_history)
        view_menu.addAction(self.dump_history_action)

        # Add log level dropdown
        view_menu.addSeparator()
        log_level_label = QLabel("  Log Level: ")
        log_level_label.setFont(QFont("Consolas", 9))

        self.log_level_combo = QComboBox()
        self.log_level_combo.setFont(QFont("Consolas", 9))
        self.log_level_combo.addItem("DEBUG", LogLevel.DEBUG)
        self.log_level_combo.addItem("INFO", LogLevel.INFO)
        self.log_level_combo.addItem("WARN", LogLevel.WARN)
        self.log_level_combo.addItem("ERROR", LogLevel.ERROR)
        self.log_level_combo.setCurrentIndex(1)  # Default to INFO
        self.log_level_combo.currentIndexChanged.connect(self.on_log_level_changed)

        # Create a widget container for label and combo
        log_level_widget = QWidget()
        log_level_layout = QHBoxLayout(log_level_widget)
        log_level_layout.setContentsMargins(5, 2, 5, 2)
        log_level_layout.addWidget(log_level_label)
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()

        # Add the widget to the menu using QWidgetAction
        log_level_action = QWidgetAction(self)
        log_level_action.setDefaultWidget(log_level_widget)
        view_menu.addAction(log_level_action)

        # Create Model menu
        model_menu = menubar.addMenu("Model")

        # OpenAI section
        openai_label = QLabel("  OpenAI: ")
        openai_label.setFont(QFont("Consolas", 9, QFont.Bold))

        self.openai_model_combo = QComboBox()
        self.openai_model_combo.setFont(QFont("Consolas", 9))
        # Add placeholder as first option
        self.openai_model_combo.addItem("-- Select --", None)
        # Add common OpenAI models
        self.openai_model_combo.addItem("GPT-5.1", "gpt-5.1")
        self.openai_model_combo.addItem("GPT-5", "gpt-5")
        self.openai_model_combo.addItem("GPT-4o", "gpt-4o")
        self.openai_model_combo.addItem("GPT-4o Mini", "gpt-4o-mini")
        self.openai_model_combo.addItem("GPT-4 Turbo", "gpt-4-turbo")
        self.openai_model_combo.addItem("GPT-4", "gpt-4")
        self.openai_model_combo.addItem("GPT-3.5 Turbo", "gpt-3.5-turbo")
        self.openai_model_combo.setCurrentIndex(1)  # Default to GPT-5.1
        self.openai_model_combo.currentIndexChanged.connect(lambda idx: self.on_model_changed(idx, "openai"))

        # Create a widget container for OpenAI label and combo
        openai_widget = QWidget()
        openai_layout = QHBoxLayout(openai_widget)
        openai_layout.setContentsMargins(5, 2, 5, 2)
        openai_layout.addWidget(openai_label)
        openai_layout.addWidget(self.openai_model_combo)
        openai_layout.addStretch()

        # Add the OpenAI widget to the menu using QWidgetAction
        openai_action = QWidgetAction(self)
        openai_action.setDefaultWidget(openai_widget)
        model_menu.addAction(openai_action)

        # Fireworks section
        fireworks_label = QLabel("  Fireworks: ")
        fireworks_label.setFont(QFont("Consolas", 9, QFont.Bold))

        self.fireworks_model_combo = QComboBox()
        self.fireworks_model_combo.setFont(QFont("Consolas", 9))
        # Add placeholder as first option
        self.fireworks_model_combo.addItem("-- Select --", None)
        # Add Fireworks models
        self.fireworks_model_combo.addItem("DeepSeek v3.1", "accounts/fireworks/models/deepseek-v3p1-terminus")
        self.fireworks_model_combo.addItem("Kimi K2", "accounts/fireworks/models/kimi-k2-instruct-0905")
        self.fireworks_model_combo.addItem("Qwen3 Coder", "accounts/fireworks/models/qwen3-coder-480b-a35b-instruct")
        self.fireworks_model_combo.setCurrentIndex(0)  # Default to placeholder
        self.fireworks_model_combo.currentIndexChanged.connect(lambda idx: self.on_model_changed(idx, "fireworks"))

        # Create a widget container for Fireworks label and combo
        fireworks_widget = QWidget()
        fireworks_layout = QHBoxLayout(fireworks_widget)
        fireworks_layout.setContentsMargins(5, 2, 5, 2)
        fireworks_layout.addWidget(fireworks_label)
        fireworks_layout.addWidget(self.fireworks_model_combo)
        fireworks_layout.addStretch()

        # Add the Fireworks widget to the menu using QWidgetAction
        fireworks_action = QWidgetAction(self)
        fireworks_action.setDefaultWidget(fireworks_widget)
        model_menu.addAction(fireworks_action)

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
        # Enable rich text (HTML) rendering for markdown support
        self.conversation_display.setAcceptRichText(True)
        # Enable word wrapping at widget width
        self.conversation_display.setLineWrapMode(QTextEdit.WidgetWidth)
        # Enable text selection and copying
        self.conversation_display.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )

        # Set default stylesheet for better markdown rendering
        self.conversation_display.document().setDefaultStyleSheet("""
            p {
                margin: 0 0 5px 0;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }
            p:first-of-type {
                margin-top: 0;
            }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 3px;
                font-family: Consolas, monospace;
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }
            code {
                background-color: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: Consolas, monospace;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }
            div {
                word-wrap: break-word;
                overflow-wrap: break-word;
            }
            strong { font-weight: bold; }
            em { font-style: italic; }
        """)

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

        # Create input area with buttons
        input_container = QWidget()
        input_container_layout = QVBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        input_container_layout.setSpacing(5)

        # First row: Capture and New Chat buttons (new row above input)
        first_row = QWidget()
        first_row_layout = QHBoxLayout(first_row)
        first_row_layout.setContentsMargins(0, 0, 0, 0)

        # Add Capture button
        self.capture_button = QPushButton("Capture")
        self.capture_button.setFont(QFont("Consolas", 10))
        self.capture_button.setToolTip("Capture - take a screenshot of the current 3D scene to attach to next message\n(Click again to cancel if already captured)\n\nTip: You can also drag & drop image files onto the window!")
        self.capture_button.clicked.connect(self.on_capture_screenshot)

        # Add New Chat button
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.setFont(QFont("Consolas", 10))
        self.new_chat_button.setToolTip("New Chat - clear the chatbox and conversation history")
        self.new_chat_button.clicked.connect(self.clear_conversation)

        first_row_layout.addWidget(self.capture_button)
        first_row_layout.addWidget(self.new_chat_button)
        first_row_layout.addStretch()  # Push buttons to the left

        # Second row: input field and cancel button
        second_row = QWidget()
        second_row_layout = QHBoxLayout(second_row)
        second_row_layout.setContentsMargins(0, 0, 0, 0)

        input_label = QLabel("You:")
        self.input_field = MultiLineInputField()
        self.input_field.setFont(QFont("Consolas", 10))
        self.input_field.setPlaceholderText("Type your message here... - Drag & drop images or .py files to attach\nPress Enter to send, Shift+Enter for new line")
        self.input_field.submit_callback = self.on_user_input

        # Configure for 5 lines high with word wrap and scrolling
        self.input_field.setLineWrapMode(QTextEdit.WidgetWidth)
        self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set height to approximately 5 lines
        font_metrics = self.input_field.fontMetrics()
        line_height = font_metrics.lineSpacing()
        self.input_field.setFixedHeight(line_height * 5 + 10)  # 5 lines + padding

        # Add Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(QFont("Consolas", 10))
        self.cancel_button.setToolTip("Cancel - stop the current AI processing")
        self.cancel_button.clicked.connect(self.on_cancel_ai)
        self.cancel_button.setVisible(False)  # Initially hidden
        self.cancel_button.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")

        second_row_layout.addWidget(input_label)
        second_row_layout.addWidget(self.input_field, stretch=1)
        second_row_layout.addWidget(self.cancel_button)

        # Third row: Build and Teardown buttons
        third_row = QWidget()
        third_row_layout = QHBoxLayout(third_row)
        third_row_layout.setContentsMargins(0, 0, 0, 0)

        # Add Quick Rebuild button
        self.quick_rebuild_button = QPushButton("Quick Rebuild")
        self.quick_rebuild_button.setFont(QFont("Consolas", 10))
        self.quick_rebuild_button.setToolTip("Quick Rebuild - run a script in quick rebuild mode (skips construction if objects exist)")
        self.quick_rebuild_button.clicked.connect(self.on_quick_rebuild_script)

        # Add Build button
        self.run_button = QPushButton("Build")
        self.run_button.setFont(QFont("Consolas", 10))
        self.run_button.setToolTip("Build - run a Python script from the working directory")
        self.run_button.clicked.connect(self.on_run_script)

        # Add Teardown button
        self.redo_button = QPushButton("Teardown")
        self.redo_button.setFont(QFont("Consolas", 10))
        self.redo_button.setToolTip("Teardown - run a script in teardown mode to remove objects")
        self.redo_button.clicked.connect(self.on_redo_script)

        third_row_layout.addWidget(self.quick_rebuild_button)
        third_row_layout.addWidget(self.run_button)
        third_row_layout.addWidget(self.redo_button)
        third_row_layout.addStretch()  # Push buttons to the left

        # Add all rows to the input container
        input_container_layout.addWidget(first_row)
        input_container_layout.addWidget(second_row)
        input_container_layout.addWidget(third_row)

        # Fourth row: Token usage status label
        self.token_status_label = QLabel("")
        self.token_status_label.setFont(QFont("Consolas", 9))
        self.token_status_label.setStyleSheet("color: #666; padding: 2px;")
        self.token_status_label.setVisible(False)  # Initially hidden
        input_container_layout.addWidget(self.token_status_label)

        # Add input container to main layout
        main_layout.addWidget(input_container)

        # Display welcome message
        self.display_welcome()

    def display_welcome(self):
        """Display welcome message in the conversation area."""
        # Check if AI client is initialized
        if self.ai_client:
            context_status = "✓ FORSHAPE.md loaded" if self.ai_client.context_provider.has_forshape() else "✗ No FORSHAPE.md"
            model_info = f"<strong>Using model:</strong> {self.ai_client.get_model()}<br>"
            context_info = f"<strong>Context:</strong> {context_status}"
            start_message = "Start chatting to generate 3D shapes!"
        else:
            # During prestart checks
            model_info = ""
            context_info = "<strong>Status:</strong> Setting up..."
            start_message = "Please complete the setup steps below to begin."

        welcome_html = f"""
<div style="font-family: Consolas, monospace; margin: 10px 0;">
<pre style="margin: 0;">{'='*60}
Welcome to ForShape AI - Interactive 3D Shape Generator
{'='*60}</pre>
<p style="margin: 5px 0;">{model_info}{context_info}</p>

<p style="margin: 5px 0;"><strong>Tip:</strong> Drag & drop images or .py files to attach them to your messages</p>

<p style="margin: 5px 0;">{start_message}</p>
<pre style="margin: 0;">{'='*60}</pre>
</div>
"""
        self.conversation_display.insertHtml(welcome_html)
        # Add line breaks after welcome message to separate from first user message
        self.conversation_display.insertHtml('<br><br>')

    def clear_conversation(self):
        """Clear the conversation display and AI history."""
        # Clear the AI agent's conversation history
        if self.ai_client:
            self.ai_client.clear_history()

            # Also explicitly clear the chat history manager
            history_manager = self.ai_client.get_history_manager()
            if history_manager:
                history_manager.clear_history()

        # Clear the conversation display
        self.conversation_display.clear()

        # Redisplay the welcome message
        self.display_welcome()

        # Show confirmation message
        self.append_message("System", "Conversation history cleared.")

    def set_components(self, ai_client: 'AIAgent', history_logger: 'HistoryLogger', logger: 'Logger' = None, image_context=None, api_debugger=None):
        """
        Set the AI client and history logger after initialization completes.

        Args:
            ai_client: The AIAgent instance
            history_logger: The HistoryLogger instance
            logger: Optional Logger instance to update (if logger was recreated)
            image_context: Optional ImageContext instance for capturing screenshots
            api_debugger: Optional APIDebugger instance for API data dumping
        """
        self.ai_client = ai_client
        self.history_logger = history_logger

        # Update image_context if provided
        if image_context is not None:
            self.image_context = image_context

        # Update api_debugger if provided
        if api_debugger is not None:
            self.api_debugger = api_debugger

        # Update logger if provided
        if logger is not None:
            # Disconnect old logger
            if self.logger and hasattr(self.logger, 'log_message'):
                try:
                    self.logger.log_message.disconnect(self.on_log_message)
                except:
                    pass

            # Update to new logger
            self.logger = logger

            # Connect new logger
            if self.logger and hasattr(self.logger, 'log_message'):
                self.logger.log_message.connect(self.on_log_message)

        # Sync model dropdown with AI client's current model
        if self.ai_client:
            self._sync_model_dropdown()

    def handle_prestart_input(self, user_input: str):
        """
        Handle user input during prestart check mode.

        Args:
            user_input: The user's input
        """
        if not self.prestart_checker:
            return

        current_status = self.prestart_checker.get_status()

        if current_status == "dir_mismatch":
            # Handle directory mismatch response (yes/no/cancel)
            should_continue = self.prestart_checker.handle_directory_mismatch(self, user_input)
            if should_continue:
                # Re-run prestart checks
                status = self.prestart_checker.check(self)
                if status == "ready":
                    # Complete initialization if callback provided
                    if self.completion_callback:
                        self.completion_callback()
                    self.enable_ai_mode()
            else:
                # User cancelled or error
                self.prestart_check_mode = False
        else:
            # For "waiting", "need_api_key", or other status, re-run checks when user provides input
            status = self.prestart_checker.check(self)
            if status == "ready":
                # Complete initialization if callback provided
                if self.completion_callback:
                    self.completion_callback()
                self.enable_ai_mode()
            elif status == "error":
                self.prestart_check_mode = False

    def enable_ai_mode(self):
        """Enable normal AI interaction mode after prestart checks pass."""
        self.prestart_check_mode = False
        # Update welcome message to show full AI details now that ai_client is initialized
        if self.ai_client:
            context_status = "✓ FORSHAPE.md loaded" if self.ai_client.context_provider.has_forshape() else "✗ No FORSHAPE.md"
            self.append_message("System",
                f"🎉 **Initialization Complete!**\n\n"
                f"**Using model:** {self.ai_client.get_model()}\n"
                f"**Context:** {context_status}\n\n"
                f"You can now chat with the AI to generate 3D shapes!")

    def on_user_input(self):
        """Handle user input when Enter is pressed."""
        user_input = self.input_field.toPlainText().strip()

        if not user_input:
            return

        # Display user input
        self.append_message("You", user_input)

        # Clear input field
        self.input_field.clear()

        # Force UI to update immediately
        QCoreApplication.processEvents()

        # Handle prestart check mode
        if self.prestart_check_mode:
            self.handle_prestart_input(user_input)
            return

        # Check if AI client is available
        if not self.ai_client:
            self.append_message("[SYSTEM]", "⚠ AI is not yet initialized. Please wait for setup to complete.")
            return

        # Check if AI is currently busy
        if self.is_ai_busy:
            # Show message that AI is busy without clearing the input
            self.append_message("[SYSTEM]", "⚠ AI is currently processing. Please wait...")
            return

        # Log user input
        if self.history_logger:
            self.history_logger.log_conversation("user", user_input)

        # Check if there are attached Python files to include in message
        has_files = len(self.attached_files) > 0
        augmented_input = user_input

        if has_files:
            # Prepend Python file content to the message
            file_parts = []
            for file_info in self.attached_files:
                file_parts.append(
                    f"[Attached Python file: {file_info['name']}]\n"
                    f"```python\n{file_info['content']}\n```\n"
                )

            # Combine file content with user input
            augmented_input = "\n".join(file_parts) + f"\n[User message]\n{user_input}"

            file_count = len(self.attached_files)
            file_word = "file" if file_count == 1 else "files"
            self.append_message("System", f"📎 Attaching {file_count} Python {file_word} to message...")

        # Check if there are captured images to attach
        has_images = len(self.captured_images) > 0
        if has_images:
            image_count = len(self.captured_images)
            image_word = "image" if image_count == 1 else "images"
            self.append_message("System", f"📷 Attaching {image_count} {image_word} to message...")

        # Show in-progress indicator
        self.append_message("AI", "⏳ Processing...")

        # Force UI to update to show the processing indicator
        QCoreApplication.processEvents()

        # Set busy state
        self.is_ai_busy = True

        # Show cancel button when AI starts processing
        self.cancel_button.setVisible(True)

        # Create and start worker thread for AI processing with augmented input and optional images
        self.worker = AIWorker(self.ai_client, augmented_input, self.captured_images if has_images else None)
        self.worker.finished.connect(self.on_ai_response)
        self.worker.token_update.connect(self.on_token_update)
        self.worker.start()

        # Reset and show token status label for new request
        self.token_status_label.setVisible(True)
        self.token_status_label.setText("Token Usage: Calculating...")
        self.token_status_label.setStyleSheet("color: #666; padding: 2px;")  # Reset to default style

        # Clear captured images and reset button after sending
        if has_images:
            self.captured_images = []
            self.update_capture_button_state()

        # Clear attached files and reset placeholder after sending
        if has_files:
            self.attached_files = []
            self.update_input_placeholder()

    def on_cancel_ai(self):
        """Handle cancel button click - cancel the current AI processing."""
        if not self.is_ai_busy or not self.worker:
            return

        # Request cancellation from the worker
        self.worker.cancel()

        # Show cancellation message
        self.append_message("System", "Cancellation requested. Waiting for AI to stop...")

        # Force UI to update
        QCoreApplication.processEvents()

    def play_notification_sound(self):
        """Play a notification sound when AI finishes processing."""
        try:
            # Play system beep sound
            # On Windows, this will play the system default beep
            # On other platforms, it will attempt to play a system sound
            import platform
            if platform.system() == 'Windows':
                # Use winsound for a simple beep on Windows
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:
                # On other platforms, try to use system bell
                print('\a')  # ASCII bell character
        except Exception as e:
            # If sound fails, just log it and continue
            if self.logger:
                self.logger.debug(f"Could not play notification sound: {e}")

    def on_token_update(self, token_data: dict):
        """
        Handle token usage updates during AI processing.

        Args:
            token_data: Dict with token usage information including iteration number
        """
        if token_data:
            # Use MessageFormatter to format token data consistently
            token_str = self.message_formatter.format_token_data(token_data, include_iteration=True)

            # Update the status label with current token usage (in-progress style)
            self.token_status_label.setText(f"Token Usage ({token_str})")
            self.token_status_label.setStyleSheet("color: #666; padding: 2px;")

            # Force UI update
            QCoreApplication.processEvents()

    def on_ai_response(self, message: str, is_error: bool, token_data: dict = None):
        """
        Handle AI response from worker thread.

        Args:
            message: The response message or error message
            is_error: True if this is an error message, False otherwise
            token_data: Optional dict with token usage information
        """
        # Remove the "Processing..." message
        self.remove_last_message()

        # Update the token status label to show final count instead of hiding it
        if token_data:
            token_str = self.message_formatter.format_token_data(token_data, include_iteration=False)
            self.token_status_label.setText(f"Token Usage (Final: {token_str})")
            self.token_status_label.setStyleSheet("color: #0066CC; padding: 2px; font-weight: bold;")
        else:
            # If no token data, keep the label visible with a default message
            self.token_status_label.setText("Token Usage: N/A")
            self.token_status_label.setStyleSheet("color: #666; padding: 2px;")

        # Display the response or error
        if is_error:
            if self.history_logger:
                self.history_logger.log_conversation("error", message)
            self.display_error(message)
        else:
            if self.history_logger:
                self.history_logger.log_conversation("assistant", message)
            self.append_message("AI", message, token_data)

        # Play notification sound when AI finishes
        self.play_notification_sound()

        # Bring main window to front when AI finishes
        self.raise_()
        self.activateWindow()
        # Restore window if minimized
        if self.isMinimized():
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)

        # Reset busy state
        self.is_ai_busy = False

        # Hide cancel button when AI finishes
        self.cancel_button.setVisible(False)

        # Clean up worker thread
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def markdown_to_html(self, text: str) -> str:
        """
        Convert markdown text to HTML using MessageFormatter.

        Args:
            text: Markdown text to convert

        Returns:
            HTML string
        """
        return self.message_formatter.markdown_to_html(text)

    def append_message(self, role: str, message: str, token_data: dict = None):
        """
        Append a message to the conversation display with markdown support.

        Args:
            role: The role (You, AI, Error, etc.)
            message: The message content (supports markdown)
            token_data: Optional dict with token usage information
        """
        # Move cursor to end before inserting
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conversation_display.setTextCursor(cursor)

        # Use MessageFormatter to format the message
        formatted_message = self.message_formatter.format_message(role, message, token_data)

        # Use insertHtml instead of append for proper HTML rendering
        self.conversation_display.insertHtml(formatted_message)

        # Add a line break after each message to separate consecutive messages
        self.conversation_display.insertHtml('<br>')

        # Scroll to bottom
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conversation_display.setTextCursor(cursor)

    def remove_last_message(self):
        """Remove the last message from the conversation display."""
        # Get the document
        document = self.conversation_display.document()

        # Start from the end and work backwards to find and remove the last div block
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Move to the start of the document and select all
        cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)

        # Get HTML content
        html_content = cursor.selection().toHtml()

        # Find and remove the last message div (work from the end)
        # Look for the last occurrence of a div with our message styling
        last_div_start = html_content.rfind('<div style="margin: 15px 0; padding: 8px')

        if last_div_start != -1:
            # Find the closing </div> after this opening tag
            search_from = last_div_start + 10
            div_end = html_content.find('</div>', search_from)

            if div_end != -1:
                # Also remove the <br> that follows
                br_end = html_content.find('<br>', div_end)
                if br_end != -1 and br_end - div_end < 20:  # Make sure it's the immediate <br>
                    end_pos = br_end + 4  # Include the <br>
                else:
                    end_pos = div_end + 6  # Just </div>

                # Remove the last message div and br
                html_content = html_content[:last_div_start] + html_content[end_pos:]

                # Set the modified HTML back
                cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
                cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                cursor.insertHtml(html_content)

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
        formatted_log = f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span><br>'

        # Move cursor to end before inserting
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)

        # Insert HTML
        self.log_display.insertHtml(formatted_log)

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

    def toggle_api_dump(self):
        """Toggle API data dumping."""
        if self.api_debugger is None:
            self.append_message("System", "API debugger not initialized yet.")
            self.toggle_api_dump_action.setChecked(False)
            return

        # Toggle the enabled state
        new_state = not self.api_debugger.enabled
        self.api_debugger.set_enabled(new_state)

        if new_state:
            dump_dir = self.api_debugger.output_dir
            self.append_message("System", f"API data dumping enabled. Data will be saved to: {dump_dir}")
            if self.logger:
                self.logger.info(f"API data dumping enabled - output: {dump_dir}")
        else:
            self.append_message("System", "API data dumping disabled.")
            if self.logger:
                self.logger.info("API data dumping disabled")

    def dump_history(self):
        """Dump the conversation history to a file."""
        if not self.ai_client:
            self.append_message("System", "AI client not initialized yet.")
            return

        try:
            # Get the history manager from AI client
            history_manager = self.ai_client.get_history_manager()

            # Use working directory's .forshape folder for history dumps
            history_dir = os.path.join(self.context_provider.working_dir, '.forshape', 'history_dumps')

            # Get model name
            model_name = self.ai_client.get_model()

            # Dump history using chat_history_manager
            dump_path = history_manager.dump_history(history_dir, model_name)

            self.append_message("System", f"Conversation history dumped successfully!\nSaved to: {dump_path}")
            if self.logger:
                self.logger.info(f"History dumped to: {dump_path}")

        except Exception as e:
            import traceback
            error_msg = f"Error dumping history: {str(e)}\n{traceback.format_exc()}"
            self.append_message("[ERROR]", error_msg)
            if self.logger:
                self.logger.error(f"Failed to dump history: {str(e)}")

    def on_log_level_changed(self, index: int):
        """
        Handle log level dropdown selection change.

        Args:
            index: The index of the selected item in the combo box
        """
        if not self.logger:
            return

        # Get the LogLevel enum value from the combo box data
        log_level = self.log_level_combo.itemData(index)

        # Update the logger's minimum level
        self.logger.set_min_level(log_level)

        # Show a brief message in the log display
        level_name = log_level.name
        self.logger.info(f"Log level changed to {level_name}")

    def on_model_changed(self, index: int, provider: str):
        """
        Handle model dropdown selection change.

        Args:
            index: The index of the selected item in the combo box
            provider: The provider name ("openai" or "fireworks")
        """
        if not self.ai_client:
            return

        # Get the appropriate combo box based on provider
        if provider == "openai":
            combo_box = self.openai_model_combo
            other_combo_box = self.fireworks_model_combo
        elif provider == "fireworks":
            combo_box = self.fireworks_model_combo
            other_combo_box = self.openai_model_combo
        else:
            return

        # Get the model identifier from the combo box data
        model = combo_box.itemData(index)
        model_name = combo_box.itemText(index)

        # If placeholder is selected (model is None), do nothing
        if model is None:
            return

        # Clear the other provider's selection
        try:
            other_combo_box.currentIndexChanged.disconnect()
        except:
            pass
        other_combo_box.setCurrentIndex(0)  # Reset to placeholder
        if provider == "openai":
            other_combo_box.currentIndexChanged.connect(lambda idx: self.on_model_changed(idx, "fireworks"))
        else:
            other_combo_box.currentIndexChanged.connect(lambda idx: self.on_model_changed(idx, "openai"))

        # Get provider-specific API key from keyring
        from .api_key_manager import ApiKeyManager
        api_key_manager = ApiKeyManager()
        api_key = api_key_manager.get_api_key(provider)

        # Check if API key exists for this provider
        if not api_key:
            self.append_message("System", f"No API key configured for {provider.capitalize()}. Please add the API key to the system keyring using ApiKeyManager.")
            return

        # Reinitialize the AI agent with the new provider
        from .api_provider import create_api_provider
        new_provider = create_api_provider(provider, api_key)

        if new_provider and new_provider.is_available():
            self.ai_client.provider = new_provider
            self.ai_client.provider_name = provider
            self.ai_client.set_model(model)

            # Show a confirmation message
            self.append_message("System", f"Provider changed to: {provider.capitalize()}\nModel changed to: {model_name} ({model})")
        else:
            self.append_message("System", f"Failed to initialize {provider} provider. Please check your API key configuration.")

    def _sync_model_dropdown(self):
        """Sync the model dropdown selection with the AI client's current model and provider."""
        if not self.ai_client:
            return

        current_model = self.ai_client.get_model()
        current_provider = self.ai_client.provider_name

        # Determine which combo box to sync based on the provider
        if current_provider == "openai":
            combo_box = self.openai_model_combo
            other_combo_box = self.fireworks_model_combo
            signal_lambda = lambda idx: self.on_model_changed(idx, "openai")
            other_signal_lambda = lambda idx: self.on_model_changed(idx, "fireworks")
        elif current_provider == "fireworks":
            combo_box = self.fireworks_model_combo
            other_combo_box = self.openai_model_combo
            signal_lambda = lambda idx: self.on_model_changed(idx, "fireworks")
            other_signal_lambda = lambda idx: self.on_model_changed(idx, "openai")
        else:
            # Unknown provider, keep current dropdown selection
            return

        # Reset the other provider's dropdown to placeholder
        try:
            other_combo_box.currentIndexChanged.disconnect()
        except:
            pass
        other_combo_box.setCurrentIndex(0)  # Reset to placeholder
        other_combo_box.currentIndexChanged.connect(other_signal_lambda)

        # Find and select the matching model in the appropriate dropdown
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == current_model:
                # Temporarily disconnect signal to avoid triggering on_model_changed
                try:
                    combo_box.currentIndexChanged.disconnect()
                except:
                    pass
                combo_box.setCurrentIndex(i)
                combo_box.currentIndexChanged.connect(signal_lambda)
                return

        # If model not found in dropdown, it might be a custom model
        # Keep current dropdown selection as is

    def scan_python_files(self):
        """
        Scan the working directory for Python files.

        Returns:
            List of Python file paths relative to the working directory
        """
        python_files = []

        # Get working directory from context provider
        working_dir = self.context_provider.working_dir

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
        """Handle Build button click."""
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

    def on_redo_script(self):
        """Handle Teardown button click."""
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
                self.redo_python_file(selected_file)

    def on_quick_rebuild_script(self):
        """Handle Quick Rebuild button click."""
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
                self.quick_rebuild_python_file(selected_file)

    def update_capture_button_state(self):
        """Update the capture button text and styling based on number of captured images."""
        image_count = len(self.captured_images)
        if image_count == 0:
            self.capture_button.setText("Capture")
            self.capture_button.setStyleSheet("")
            self.capture_button.setToolTip("Capture - take a screenshot of the current 3D scene to attach to next message\n(Click again to clear all if already captured)\n\nTip: You can also drag & drop image files onto the window!")
        elif image_count == 1:
            self.capture_button.setText("Capture ✓ (1)")
            self.capture_button.setStyleSheet("background-color: #90EE90;")
            self.capture_button.setToolTip("1 image ready to send. Click to clear all images.")
        else:
            self.capture_button.setText(f"Capture ✓ ({image_count})")
            self.capture_button.setStyleSheet("background-color: #90EE90;")
            self.capture_button.setToolTip(f"{image_count} images ready to send. Click to clear all images.")

    def update_input_placeholder(self):
        """Update the input field placeholder text based on attached files."""
        file_count = len(self.attached_files)
        if file_count == 0:
            self.input_field.setPlaceholderText("Type your message here... - Drag & drop images or .py files to attach\nPress Enter to send, Shift+Enter for new line")
        elif file_count == 1:
            file_name = self.attached_files[0]['name']
            self.input_field.setPlaceholderText(f"1 Python file attached ({file_name}) - Type your message...\nPress Enter to send, Shift+Enter for new line")
        else:
            self.input_field.setPlaceholderText(f"{file_count} Python files attached - Type your message...\nPress Enter to send, Shift+Enter for new line")

    def on_capture_screenshot(self):
        """Handle Capture button click - captures scene screenshot or clears all if already captured."""
        # If images are already captured, clicking again clears all of them
        if len(self.captured_images) > 0:
            image_count = len(self.captured_images)
            self.captured_images = []
            self.update_capture_button_state()
            image_word = "image" if image_count == 1 else "images"
            self.append_message("System", f"All {image_count} captured {image_word} discarded. No images will be attached.")
            return

        if not self.image_context:
            self.append_message("[SYSTEM]", "ImageContext not configured")
            return

        if self.is_ai_busy:
            self.append_message("[SYSTEM]", "AI is currently processing. Please wait...")
            return

        # Show capturing message
        self.append_message("System", "Capturing screenshot...")

        # Force UI to update
        QCoreApplication.processEvents()

        try:
            # Fit all objects in view before capturing (so user can see what will be captured)
            self.image_context.fit()

            # Capture screenshot with base64 encoding using image_context
            result = self.image_context.capture_encoded(perspective="isometric")

            if result is None or not result.get("success"):
                self.append_message("[SYSTEM]", "Screenshot capture failed")
                return

            file_path = result.get("file", "unknown")

            # Show preview dialog for user to confirm or cancel (and potentially annotate)
            preview_dialog = ImagePreviewDialog(file_path, self)
            if preview_dialog.exec_() == QDialog.Accepted and preview_dialog.is_confirmed():
                # User confirmed - the annotated image has been saved to file_path
                # Re-encode the potentially modified image
                import base64
                try:
                    with open(file_path, 'rb') as image_file:
                        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

                    # Update the result with the new base64 encoding
                    result["image_base64"] = image_base64

                    # Add the captured (and potentially annotated) image data to the list
                    self.captured_images.append(result)

                    # Visual feedback - update button to show images are ready
                    self.update_capture_button_state()

                    # Show success message
                    image_count = len(self.captured_images)
                    image_word = "image" if image_count == 1 else "images"
                    self.append_message("System",
                        f"Screenshot confirmed!\n"
                        f"Saved to: {file_path}\n"
                        f"{image_count} {image_word} ready to attach to your next message.")
                except Exception as e:
                    self.append_message("[SYSTEM]", f"Error encoding annotated image: {str(e)}")
            else:
                # User cancelled - discard the image
                self.append_message("System", "Screenshot cancelled. Image will not be attached.")

        except Exception as e:
            import traceback
            error_msg = f"Error capturing screenshot:\n{traceback.format_exc()}"
            self.append_message("[SYSTEM]", error_msg)

    def _execute_python_file_with_mode(self, file_path, mode, action_name):
        """
        Generic helper to execute a Python file with a specific execution mode.

        Args:
            file_path: Path to the Python file to run
            mode: ExecutionMode enum value or 'with_teardown' for execute_with_teardown
            action_name: Action name for messages (e.g., "Teardown", "Quick rebuild", "Build")

        Returns:
            None
        """
        self.append_message("[SYSTEM]", f"{action_name}: {file_path}")

        # Get absolute path
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            self.display_error(f"File not found: {file_path}")
            return

        # Add project directory to sys.path if not already there
        project_dir = self.context_provider.get_project_dir()
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)

        try:
            # Read the script content
            with open(abs_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            from pathlib import Path
            path_obj = Path(abs_path)

            # Execute based on mode
            if mode == 'with_teardown':
                # Execute with teardown first, then normal
                teardown_result, normal_result = ScriptExecutor.execute_with_teardown(
                    script_content, path_obj, import_freecad=False
                )

                # Display teardown output if any
                if teardown_result.output.strip():
                    self.append_message("[TEARDOWN OUTPUT]", teardown_result.output.strip())

                # Display normal execution output if any
                if normal_result.output.strip():
                    self.append_message("[OUTPUT]", normal_result.output.strip())

                # Check results
                if teardown_result.success and normal_result.success:
                    self.append_message("[SYSTEM]", f"{action_name} completed successfully: {file_path}")
                elif not teardown_result.success:
                    error_msg = f"Error during teardown of {file_path}:\n{teardown_result.error}"
                    self.display_error(error_msg)
                else:
                    error_msg = f"Error running {file_path}:\n{normal_result.error}"
                    self.display_error(error_msg)
            else:
                # Execute with specific mode
                result = ScriptExecutor.execute(
                    script_content, path_obj, mode=mode, import_freecad=False
                )

                # Display output if any
                if result.output.strip():
                    self.append_message("[OUTPUT]", result.output.strip())

                if result.success:
                    self.append_message("[SYSTEM]", f"{action_name} completed successfully: {file_path}")
                else:
                    error_msg = f"Error during {action_name.lower()} of {file_path}:\n{result.error}"
                    self.display_error(error_msg)

        except Exception as e:
            # Format and display the error
            error_msg = f"Error executing {file_path}:\n{traceback.format_exc()}"
            self.display_error(error_msg)

    def redo_python_file(self, file_path):
        """
        Teardown a Python file - run the script in teardown mode to remove objects.

        Args:
            file_path: Path to the Python file to teardown
        """
        self._execute_python_file_with_mode(file_path, ExecutionMode.TEARDOWN, "Tearing down")

    def quick_rebuild_python_file(self, file_path):
        """
        Quick rebuild a Python file - run the script in quick rebuild mode.

        Args:
            file_path: Path to the Python file to run
        """
        self._execute_python_file_with_mode(file_path, ExecutionMode.QUICK_REBUILD, "Quick rebuilding")

    def run_python_file(self, file_path):
        """
        Run a Python file with teardown first, then normal execution.

        Args:
            file_path: Path to the Python file to run
        """
        self._execute_python_file_with_mode(file_path, 'with_teardown', "Building (with teardown)")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event to accept file drops."""
        if event.mimeData().hasUrls():
            # Check if any of the URLs are files
            urls = event.mimeData().urls()
            has_files = any(url.isLocalFile() for url in urls)
            if has_files:
                event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move event for visual feedback."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Handle file drop event for images and Python files."""
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        # Get the list of dropped files
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls if url.isLocalFile()]

        if not files:
            event.ignore()
            return

        # Categorize files by type
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        image_files = []
        python_files = []
        unsupported_files = []

        for file_path in files:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in image_extensions:
                image_files.append(file_path)
            elif file_ext == '.py':
                python_files.append(file_path)
            else:
                unsupported_files.append(file_path)

        # Process image files
        for file_path in image_files:
            self.handle_dropped_image(file_path)

        # Process Python files
        for file_path in python_files:
            self.handle_dropped_python_file(file_path)

        # Show message for unsupported files
        if unsupported_files:
            file_names = ", ".join([os.path.basename(f) for f in unsupported_files])
            self.append_message("System", f"Skipped unsupported file(s): {file_names}\n(Supported: images and .py files)")

        event.acceptProposedAction()

    def handle_dropped_image(self, file_path: str):
        """
        Handle a dropped image file by converting it to base64 and adding it to the list.

        Args:
            file_path: Path to the dropped image file
        """
        if self.is_ai_busy:
            self.append_message("[SYSTEM]", "AI is currently processing. Please wait...")
            return

        try:
            import base64

            # Read and encode the image
            with open(file_path, 'rb') as image_file:
                image_bytes = image_file.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            # Determine the file extension for saving
            file_ext = os.path.splitext(file_path)[1].lower()

            # Copy the image to the history folder (same as capture does)
            if self.image_context:
                history_dir = self.image_context.images_dir
                os.makedirs(history_dir, exist_ok=True)

                # Generate timestamped filename
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"dropped_{timestamp}{file_ext}"
                new_file_path = os.path.join(history_dir, new_filename)

                # Copy the file
                import shutil
                shutil.copy2(file_path, new_file_path)
                stored_path = new_file_path
            else:
                stored_path = file_path

            # Add the image data to the list (same format as captured images)
            self.captured_images.append({
                "success": True,
                "file": stored_path,
                "image_base64": image_base64  # Just the base64 string, not the data URL
            })

            # Visual feedback - update button to show images are ready
            self.update_capture_button_state()

            # Show success message
            image_count = len(self.captured_images)
            image_word = "image" if image_count == 1 else "images"
            self.append_message("System",
                f"Image added!\n"
                f"File: {os.path.basename(file_path)}\n"
                f"Saved to: {stored_path}\n"
                f"{image_count} {image_word} ready to attach to your next message.")

        except Exception as e:
            import traceback
            error_msg = f"Error processing dropped image:\n{traceback.format_exc()}"
            self.append_message("[SYSTEM]", error_msg)

    def handle_dropped_python_file(self, file_path: str):
        """
        Handle a dropped Python file by reading its content and adding it to the attached files list.

        Args:
            file_path: Path to the dropped Python file
        """
        if self.is_ai_busy:
            self.append_message("[SYSTEM]", "AI is currently processing. Please wait...")
            return

        try:
            # Read the Python file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Store the file info
            file_info = {
                "path": file_path,
                "name": os.path.basename(file_path),
                "content": file_content
            }
            self.attached_files.append(file_info)

            # Update UI
            self.update_input_placeholder()

            # Show success message
            file_count = len(self.attached_files)
            file_word = "file" if file_count == 1 else "files"
            self.append_message("System",
                f"Python file attached!\n"
                f"File: {os.path.basename(file_path)}\n"
                f"{file_count} Python {file_word} ready to attach to your next message.")

        except Exception as e:
            import traceback
            error_msg = f"Error processing dropped Python file:\n{traceback.format_exc()}"
            self.append_message("[SYSTEM]", error_msg)

    def closeEvent(self, event):
        """Handle window close event."""
        self.handle_exit()

        # Call the window close callback to clear the active window reference
        if self.window_close_callback:
            self.window_close_callback()

        event.accept()
