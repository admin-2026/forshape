"""
Main window GUI for ForShape AI.

This module provides the interactive GUI interface using PySide2.
"""

from typing import TYPE_CHECKING

from PySide2.QtCore import QCoreApplication, Qt
from PySide2.QtGui import QDragEnterEvent, QDropEvent, QFont
from PySide2.QtWidgets import (
    QAction,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from agent.chat_history_manager import HistoryPolicy
from agent.provider_config_loader import ProviderConfigLoader
from agent.request import ImageMessage, TextMessage, ToolCall, ToolCallMessage
from agent.step_config import StepConfig, StepConfigRegistry

from .dialogs import CheckpointSelector, ImagePreviewDialog
from .logger import LogLevel
from .ui import (
    DragDropHandler,
    FileExecutor,
    LogView,
    MessageFormatter,
    MessageHandler,
    ModelMenuManager,
    MultiLineInputField,
    TokenStatusLabel,
    WelcomeWidget,
)
from .ui_config_manager import UIConfigManager
from .variables import VariablesView
from .workers import AIWorker

if TYPE_CHECKING:
    from agent.ai_agent import AIAgent
    from agent.history_logger import HistoryLogger

    from .logger import Logger


class ForShapeMainWindow(QMainWindow):
    """Main window for the ForShape AI GUI application."""

    def __init__(
        self,
        ai_client: "AIAgent",
        history_logger: "HistoryLogger",
        logger: "Logger",
        config,
        exit_handler,
        image_context=None,
        prestart_checker=None,
        completion_callback=None,
        window_close_callback=None,
    ):
        """
        Initialize the main window.

        Args:
            ai_client: The AIAgent instance for AI interactions (can be None initially)
            history_logger: The HistoryLogger instance for logging (can be None initially)
            logger: The Logger instance for tool call logging
            config: The ConfigurationManager instance for accessing working directory and project info
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
        self.config = config
        self.image_context = image_context
        self.handle_exit = exit_handler
        self.is_ai_busy = False  # Track if AI is currently processing
        self.current_step_config = None  # Store the current StepConfig when AI is busy
        self.worker = None  # Current worker thread
        self.captured_images = []  # Store captured images to attach to next message
        self.attached_files = []  # Store attached Python files to include in next message
        self.api_debugger = None  # API debugger instance (will be set later)

        # Prestart check mode
        self.prestart_checker = prestart_checker
        self.prestart_check_mode = (
            True if prestart_checker else False
        )  # Start in prestart check mode if checker provided
        self.completion_callback = completion_callback
        self.window_close_callback = window_close_callback

        # Initialize message formatter
        self.message_formatter = MessageFormatter(self.logger)

        # Load provider configuration
        self.provider_config_loader = ProviderConfigLoader()

        # Initialize UI config manager for persisting menu selections
        self.ui_config_manager = UIConfigManager(self.config.get_forshape_dir())
        self.ui_config_manager.load()

        # Initialize handler instances (will be fully configured after UI setup)
        self.file_executor = None
        self.drag_drop_handler = None
        self.model_menu_manager = None

        # Enable drag and drop
        self.setAcceptDrops(True)

        self.setup_ui()

    def _pluralize(self, word: str, count: int) -> str:
        """
        Return singular or plural form of a word based on count.

        Args:
            word: The singular form of the word
            count: The count to determine singular/plural

        Returns:
            The word with 's' appended if count != 1, otherwise the original word
        """
        return word if count == 1 else f"{word}s"

    def _set_log_panel_visibility(self, visible: bool):
        """
        Set the visibility of the log panel and update the action text.

        Args:
            visible: True to show the log panel, False to hide it
        """
        if visible:
            self.log_widget.show()
        else:
            self.log_widget.hide()

        # Always set text to "Show Logs" as requested
        self.toggle_logs_action.setText("Show Logs")
        self.toggle_logs_action.setChecked(visible)

        # Save to config
        self.ui_config_manager.set("show_logs", visible)

    def _set_variables_panel_visibility(self, visible: bool):
        """
        Set the visibility of the variables panel and update the action text.

        Args:
            visible: True to show the variables panel, False to hide it
        """
        if visible:
            self.variables_widget.show()
        else:
            self.variables_widget.hide()

        # Always set text to "Show Variables" as requested
        self.toggle_variables_action.setText("Show Variables")
        self.toggle_variables_action.setChecked(visible)

        # Save to config
        self.ui_config_manager.set("show_variables", visible)

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

        # Add toggle variables action
        self.toggle_variables_action = QAction("Show Variables", self)
        self.toggle_variables_action.setCheckable(True)
        self.toggle_variables_action.triggered.connect(self.toggle_variables_panel)
        view_menu.addAction(self.toggle_variables_action)

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

        # Restore log level from config, default to INFO if not set
        saved_log_level = self.ui_config_manager.get("log_level", "INFO")
        log_level_index = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}.get(saved_log_level, 1)
        self.log_level_combo.setCurrentIndex(log_level_index)

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

        # Create Model menu dynamically from provider config
        model_menu = menubar.addMenu("Model")
        self._create_model_menu_items(model_menu)

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

        # Right side: Log area
        self.log_view = LogView()
        self.log_widget = self.log_view.get_widget()
        self.welcome_widget = WelcomeWidget(lambda: self.ai_client, self.config)
        self.message_handler = MessageHandler(self.message_formatter, self.logger, self.welcome_widget)

        conversation_layout.addWidget(self.message_handler.get_widget())

        # Variables area
        self.variables_widget = VariablesView(working_dir=self.config.working_dir)

        # Add all panels to splitter
        splitter.addWidget(conversation_widget)
        splitter.addWidget(self.log_widget)
        splitter.addWidget(self.variables_widget)

        # Set initial splitter sizes (60% conversation, 20% logs, 20% variables)
        splitter.setSizes([600, 200, 200])

        # Restore show_logs state from config, default to hidden
        show_logs = self.ui_config_manager.get("show_logs", False)
        self._set_log_panel_visibility(show_logs)

        # Restore show_variables state from config, default to visible
        show_variables = self.ui_config_manager.get("show_variables", True)
        self._set_variables_panel_visibility(show_variables)

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
        self.capture_button.setToolTip(
            "Capture - take a screenshot of the current 3D scene to attach to next message\n(Click again to cancel if already captured)\n\nTip: You can also drag & drop image files onto the window!"
        )
        self.capture_button.clicked.connect(self.on_capture_screenshot)

        # Add New Chat button
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.setFont(QFont("Consolas", 10))
        self.new_chat_button.setToolTip("New Chat - clear the chatbox and conversation history")
        self.new_chat_button.clicked.connect(self.clear_conversation)

        # Add Rewind button
        self.rewind_button = QPushButton("Rewind")
        self.rewind_button.setFont(QFont("Consolas", 10))
        self.rewind_button.setToolTip("Rewind - restore files from a previous checkpoint")
        self.rewind_button.clicked.connect(self.on_rewind_clicked)

        first_row_layout.addWidget(self.capture_button)
        first_row_layout.addWidget(self.new_chat_button)
        first_row_layout.addWidget(self.rewind_button)
        first_row_layout.addStretch()  # Push buttons to the left

        # Second row: input field and cancel button
        second_row = QWidget()
        second_row_layout = QHBoxLayout(second_row)
        second_row_layout.setContentsMargins(0, 0, 0, 0)

        input_label = QLabel("You:")
        self.input_field = MultiLineInputField()
        self.input_field.setFont(QFont("Consolas", 10))
        self.input_field.setPlaceholderText(
            "Type your message here... - Drag & drop images or .py files to attach\nPress Enter to send, Shift+Enter for new line"
        )
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

        # Add Incremental Build button
        self.incremental_build_button = QPushButton("Incremental Build")
        self.incremental_build_button.setFont(QFont("Consolas", 10))
        self.incremental_build_button.setToolTip(
            "Incremental Build - run a script in incremental build mode (skips construction if objects exist)"
        )
        self.incremental_build_button.clicked.connect(self.on_incremental_build_script)

        # Add Rebuild button
        self.run_button = QPushButton("Rebuild")
        self.run_button.setFont(QFont("Consolas", 10))
        self.run_button.setToolTip("Rebuild - run a Python script from the working directory")
        self.run_button.clicked.connect(self.on_run_script)

        # Add Teardown button
        self.teardown_button = QPushButton("Teardown")
        self.teardown_button.setFont(QFont("Consolas", 10))
        self.teardown_button.setToolTip("Teardown - run a script in teardown mode to remove objects")
        self.teardown_button.clicked.connect(self.on_redo_script)

        # Add Export button
        self.export_button = QPushButton("Export")
        self.export_button.setFont(QFont("Consolas", 10))
        self.export_button.setToolTip("Export - run export.py from the working directory")
        self.export_button.clicked.connect(self.on_export_clicked)

        # Add Import button
        self.import_button = QPushButton("Import")
        self.import_button.setFont(QFont("Consolas", 10))
        self.import_button.setToolTip("Import - run import.py from the working directory")
        self.import_button.clicked.connect(self.on_import_clicked)

        third_row_layout.addWidget(self.incremental_build_button)
        third_row_layout.addWidget(self.run_button)
        third_row_layout.addWidget(self.teardown_button)
        third_row_layout.addWidget(self.export_button)
        third_row_layout.addWidget(self.import_button)
        third_row_layout.addStretch()  # Push buttons to the left

        # Add all rows to the input container
        input_container_layout.addWidget(first_row)
        input_container_layout.addWidget(second_row)
        input_container_layout.addWidget(third_row)

        # Fourth row: Token usage status label
        self.token_status_label = TokenStatusLabel(self.message_formatter)
        input_container_layout.addWidget(self.token_status_label)

        # Add input container to main layout
        main_layout.addWidget(input_container)

        # Connect logger signal to log view
        self.logger.log_message.connect(self.log_view.on_log_message)

        self.file_executor = FileExecutor(self.config, self.message_handler, self.logger)

        self.drag_drop_handler = DragDropHandler(self.message_handler, self.logger, self.image_context)
        # Set state references for drag drop handler
        self.drag_drop_handler.set_state_references(
            self.captured_images, self.attached_files, lambda: self.is_ai_busy, self.capture_button, self.input_field
        )

        self.model_menu_manager = ModelMenuManager(
            self.provider_config_loader, self.message_handler, self.logger, self.ui_config_manager
        )
        self.model_menu_manager.set_ai_client(self.ai_client)
        self.model_menu_manager.set_callbacks(self.prestart_checker, self.completion_callback, self.enable_ai_mode)

        # IMPORTANT: Refresh the entire Model menu to use the real manager
        # The menu was created with a temp manager, and Add/Delete API Key actions
        # are still bound to that temp manager. Refreshing recreates everything.
        self.model_menu_manager.refresh_model_menu(self)

        # Clean up temp manager references
        if hasattr(self, "_temp_model_combos"):
            del self._temp_model_combos

        # Display welcome message
        self.message_handler.display_welcome()

    def _create_model_menu_items(self, model_menu):
        """
        Dynamically create model menu items from provider configuration.
        Delegates to ModelMenuManager.

        Args:
            model_menu: The QMenu to add model selection widgets to
        """
        # Delegate to model menu manager (will be called before manager is initialized)
        # So we need to handle this case
        if self.model_menu_manager:
            self.model_menu_manager.create_model_menu_items(model_menu, self)
        else:
            # During initial setup, create a temporary manager
            temp_manager = ModelMenuManager(
                self.provider_config_loader,
                None,  # message_handler not yet initialized
                self.logger,
                self.ui_config_manager,
            )
            temp_manager.create_model_menu_items(model_menu, self)
            # Store the model_combos for later use
            if hasattr(temp_manager, "model_combos"):
                self._temp_model_combos = temp_manager.model_combos

    def clear_conversation(self):
        """Clear the conversation display and AI history."""
        # Clear the AI agent's conversation history
        if self.ai_client:
            self.ai_client.clear_history()

            # Also explicitly clear the chat history manager
            history_manager = self.ai_client.get_history_manager()
            if history_manager:
                history_manager.clear_history()

        self.message_handler.clear_conversation()

    def on_rewind_clicked(self):
        """Handle Rewind button click - show checkpoint selector and restore files."""
        # Get the edits directory from the context provider
        if not self.config:
            self.message_handler.display_error("Context provider not initialized.")
            return

        edits_dir = self.config.get_edits_dir()

        # Check if edits directory exists
        if not edits_dir.exists():
            self.message_handler.append_message(
                "System", "No edit history found. The edits directory does not exist yet."
            )
            return

        # Get all sessions using EditHistory
        from agent.edit_history import EditHistory

        session_names = EditHistory.list_all_sessions(edits_dir)

        if not session_names:
            self.message_handler.append_message("System", "No checkpoints found. Edit history is empty.")
            return

        # Get session info for each session
        sessions = []
        for session_name in session_names:
            session_info = EditHistory.get_session_info(edits_dir, session_name)
            if "error" not in session_info:
                sessions.append(session_info)

        if not sessions:
            self.message_handler.append_message("System", "No valid checkpoints found.")
            return

        # Show checkpoint selector dialog
        dialog = CheckpointSelector(sessions, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_session = dialog.get_selected_session()
            if selected_session:
                self.restore_checkpoint(selected_session)

    def restore_checkpoint(self, session_info):
        """
        Restore files from a selected checkpoint.

        Args:
            session_info: Dictionary containing session information
        """
        session_name = session_info.get("session_name")
        conversation_id = session_info.get("conversation_id")
        file_count = session_info.get("file_count", 0)

        self.message_handler.append_message(
            "System", f"Restoring {file_count} file(s) from checkpoint: {conversation_id}..."
        )

        # Get paths
        working_dir = self.config.working_dir
        edits_dir = self.config.get_edits_dir()

        # Restore using EditHistory
        from agent.edit_history import EditHistory

        success, message = EditHistory.restore_from_session(edits_dir, session_name, working_dir, self.logger)

        if success:
            self.message_handler.append_message("System", f"✓ {message}")
            self.logger.info(f"Restored checkpoint: {conversation_id}")
        else:
            self.message_handler.display_error(f"Failed to restore checkpoint:\n{message}")
            self.logger.error(f"Failed to restore checkpoint {conversation_id}: {message}")

    def set_components(
        self,
        ai_client: "AIAgent",
        history_logger: "HistoryLogger",
        wait_manager,
        permission_input,
        logger: "Logger" = None,
        image_context=None,
        api_debugger=None,
    ):
        """
        Set the AI client and history logger after initialization completes.

        Args:
            ai_client: The AIAgent instance
            history_logger: The HistoryLogger instance
            wait_manager: WaitManager instance for user interactions
            permission_input: PermissionInput instance for permission requests
            logger: Optional Logger instance to update (if logger was recreated)
            image_context: Optional ImageContext instance for capturing screenshots
            api_debugger: Optional APIDebugger instance for API data dumping
        """
        self.ai_client = ai_client
        self.history_logger = history_logger

        # Create bridge to connect agent's wait manager to GUI dialogs
        from agent.async_ops import ClarificationInput

        from .async_ops import ClarificationHandler, PermissionHandler, UserInputBridge

        # Create bridge and register provider/handler pairs
        self.user_input_bridge = UserInputBridge(wait_manager, parent=self, logger=self.logger)
        self.user_input_bridge.register_input_type(ClarificationInput(), ClarificationHandler())
        self.user_input_bridge.register_input_type(permission_input, PermissionHandler())

        # Update image_context if provided
        if image_context is not None:
            self.image_context = image_context
            # Update drag drop handler's image context
            if self.drag_drop_handler:
                self.drag_drop_handler.image_context = image_context

        # Update api_debugger if provided
        if api_debugger is not None:
            self.api_debugger = api_debugger

            # Restore dump_api_data state from config
            saved_dump_api_data = self.ui_config_manager.get("dump_api_data", False)
            if saved_dump_api_data:
                self.api_debugger.set_enabled(True)
                self.toggle_api_dump_action.setChecked(True)

        # Update logger if provided
        if logger is not None:
            # Disconnect old logger
            try:
                self.logger.log_message.disconnect(self.log_view.on_log_message if self.log_view else lambda: None)
            except Exception:
                pass

            # Update to new logger
            self.logger = logger

            # Update handlers' loggers
            if self.message_handler:
                self.message_handler.logger = logger
            if self.file_executor:
                self.file_executor.logger = logger
            if self.drag_drop_handler:
                self.drag_drop_handler.logger = logger
            if self.model_menu_manager:
                self.model_menu_manager.logger = logger

            # Connect new logger
            self.logger.log_message.connect(self.log_view.on_log_message)

        # Update model menu manager's AI client
        if self.model_menu_manager:
            self.model_menu_manager.set_ai_client(self.ai_client)

        # Restore saved model selection to AI client, or sync dropdown with current model
        if self.ai_client and self.model_menu_manager:
            # Try to restore saved model selection
            saved_provider = self.ui_config_manager.get("selected_provider")
            saved_model = self.ui_config_manager.get("selected_model")

            restored = False
            if saved_provider and saved_model:
                # Apply saved model selection to AI client
                restored = self.model_menu_manager.restore_saved_model(saved_provider, saved_model)

            if not restored:
                # Restoration failed or no saved selection, sync dropdown with AI client's current state
                self.model_menu_manager.sync_model_dropdown()

        # Refresh welcome widget now that ai_client is available
        self.welcome_widget.refresh()

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
            context_status = "✓ FORSHAPE.md loaded" if self.config.has_forshape() else "✗ No FORSHAPE.md"
            self.message_handler.append_message(
                "System",
                f"🎉 **Initialization Complete!**\n\n"
                f"**Using model:** {self.ai_client.get_model()}\n"
                f"**Context:** {context_status}\n\n"
                f"You can now chat with the AI to generate 3D shapes!",
            )

        # Bring window to front after initialization completes
        self.raise_()
        self.activateWindow()
        # Restore window if minimized
        if self.isMinimized():
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)

    def on_user_input(self):
        """Handle user input when Enter is pressed."""
        user_input = self.input_field.toPlainText().strip()

        if not user_input:
            return

        # Display user input
        self.message_handler.append_message("You", user_input)

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
            self.message_handler.append_message(
                "System", "⚠ AI is not yet initialized. Please wait for setup to complete."
            )
            return

        # Check if AI is currently busy
        if self.is_ai_busy:
            # Add message to the current step config to be processed during next iteration
            if self.current_step_config:
                self.current_step_config.add_pending_message(user_input)
                self.message_handler.append_message(
                    "System", "✓ Your message will be added to the ongoing conversation..."
                )
            else:
                self.message_handler.append_message("System", "⚠ AI is currently processing. Please wait...")
            return

        # Log user input
        if self.history_logger:
            self.history_logger.log_conversation("user", user_input)

        # Build initial_messages for the main step (files and images)
        initial_messages = []

        # Add attached files as TextMessage
        if self.attached_files:
            file_count = len(self.attached_files)
            self.message_handler.append_message(
                "System", f"📎 Attaching {file_count} Python {self._pluralize('file', file_count)} to message..."
            )
            for file_info in self.attached_files:
                file_content = f"[Attached Python file: {file_info['name']}]\n```python\n{file_info['content']}\n```"
                initial_messages.append(TextMessage("user", file_content))

        # Add images as ImageMessage
        if self.captured_images:
            image_count = len(self.captured_images)
            self.message_handler.append_message(
                "System", f"📷 Attaching {image_count} {self._pluralize('image', image_count)} to message..."
            )
            initial_messages.append(ImageMessage("Screenshot of the FreeCAD scene:", self.captured_images))

        # Show in-progress indicator
        self.message_handler.create_agent_progress_widget()

        # Force UI to update to show the processing indicator
        QCoreApplication.processEvents()

        # Set busy state
        self.is_ai_busy = True

        # Show cancel button when AI starts processing
        self.cancel_button.setVisible(True)

        # Create StepConfig with the user input and store it for pending messages
        main_step_config = StepConfig(initial_message=user_input)
        self.current_step_config = main_step_config

        # Create StepConfigRegistry and set the main step config
        step_configs = StepConfigRegistry()
        step_configs.set_config("main", main_step_config)

        # Configure doc_print step to call print_document tool
        doc_print_tool_call = ToolCallMessage(
            tool_calls=[
                ToolCall(
                    name="print_document",
                    arguments={},
                    copy_result_to_response=True,
                    description="The current FreeCAD document structure",
                    key="doc_print_step_print_document",
                    policy=HistoryPolicy.LATEST,
                )
            ]
        )
        step_configs.append_messages("doc_print", [doc_print_tool_call])

        # Append messages for main step if any exist
        if initial_messages:
            step_configs.append_messages("main", initial_messages)

        # Create and start worker thread for AI processing with step configs
        self.worker = AIWorker(self.ai_client, user_input, step_configs)
        self.worker.finished.connect(self.on_ai_response)
        self.worker.token_update.connect(self.on_token_update)
        self.worker.step_response.connect(self.on_step_response)
        self.worker.start()

        # Reset and show token status label for new request
        self.token_status_label.reset()

        # Clear captured images and reset button after sending
        if self.captured_images:
            self.captured_images = []
            self.update_capture_button_state()

        # Clear attached files and reset placeholder after sending
        if self.attached_files:
            self.attached_files = []
            self.update_input_placeholder()

    def on_cancel_ai(self):
        """Handle cancel button click - cancel the current AI processing."""
        if not self.is_ai_busy or not self.worker:
            return

        # Request cancellation from the worker
        self.worker.cancel()

        # Show cancellation message
        self.message_handler.append_message("System", "Cancellation requested. Waiting for AI to stop...")

        # Force UI to update
        QCoreApplication.processEvents()

    def on_token_update(self, token_data: dict):
        """
        Handle token usage updates during AI processing.

        Args:
            token_data: Dict with token usage information including iteration number
        """
        self.token_status_label.update_tokens(token_data)

        if token_data:
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
        # Update the token status label to show final count
        self.token_status_label.finalize(token_data)

        # Display error if any (success responses are handled by on_step_response)
        if is_error:
            if self.history_logger:
                self.history_logger.log_conversation("error", message)
            self.message_handler.display_error(message)

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

        # Clear the step config
        self.current_step_config = None

        # Hide cancel button when AI finishes
        self.cancel_button.setVisible(False)

        # Clean up worker thread
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

        self.message_handler.agent_progress_done()

    def on_step_response(self, step_name: str, response: str):
        """
        Handle step response from worker thread for async printing.

        Args:
            step_name: The name of the step that completed
            response: The response from the step
        """
        # Display the step response
        self.message_handler.append_message("AI", response)

    def play_notification_sound(self):
        """Play a notification sound when AI finishes processing."""
        try:
            import platform

            if platform.system() == "Windows":
                import winsound

                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:
                print("\a")  # ASCII bell character
        except Exception as e:
            self.logger.debug(f"Could not play notification sound: {e}")

    def toggle_log_panel(self):
        """Toggle the visibility of the log panel."""
        self._set_log_panel_visibility(not self.log_widget.isVisible())

    def toggle_variables_panel(self):
        """Toggle the visibility of the variables panel."""
        self._set_variables_panel_visibility(not self.variables_widget.isVisible())

    def toggle_api_dump(self):
        """Toggle API data dumping."""
        if self.api_debugger is None:
            self.message_handler.append_message("System", "API debugger not initialized yet.")
            self.toggle_api_dump_action.setChecked(False)
            return

        # Toggle the enabled state
        new_state = not self.api_debugger.enabled
        self.api_debugger.set_enabled(new_state)

        # Save to config
        self.ui_config_manager.set("dump_api_data", new_state)

        if new_state:
            dump_dir = self.api_debugger.output_dir
            self.message_handler.append_message(
                "System", f"API data dumping enabled. Data will be saved to: {dump_dir}"
            )
            self.logger.info(f"API data dumping enabled - output: {dump_dir}")
        else:
            self.message_handler.append_message("System", "API data dumping disabled.")
            self.logger.info("API data dumping disabled")

    def dump_history(self):
        """Dump the conversation history to a file."""
        if not self.ai_client:
            self.message_handler.append_message("System", "AI client not initialized yet.")
            return

        try:
            # Get the history manager from AI client
            history_manager = self.ai_client.get_history_manager()

            # Use working directory's .forshape folder for history dumps
            history_dir = self.config.get_history_dumps_dir()

            # Get model name
            model_name = self.ai_client.get_model()

            # Dump history using chat_history_manager
            dump_path = history_manager.dump_history(history_dir, model_name)

            self.message_handler.append_message(
                "System", f"Conversation history dumped successfully!\nSaved to: {dump_path}"
            )
            self.logger.info(f"History dumped to: {dump_path}")

        except Exception as e:
            import traceback

            error_msg = f"Error dumping history: {str(e)}\n{traceback.format_exc()}"
            self.message_handler.display_error(error_msg)
            self.logger.error(f"Failed to dump history: {str(e)}")

    def on_log_level_changed(self, index: int):
        """
        Handle log level dropdown selection change.

        Args:
            index: The index of the selected item in the combo box
        """
        # Get the LogLevel enum value from the combo box data
        log_level = self.log_level_combo.itemData(index)

        # Update the logger's minimum level
        self.logger.set_min_level(log_level)

        # Save to config
        self.ui_config_manager.set("log_level", log_level.name)

        # Show a brief message in the log display
        level_name = log_level.name
        self.logger.info(f"Log level changed to {level_name}")

    def on_run_script(self):
        """Handle Rebuild button click - delegate to file executor."""
        if self.file_executor:
            self.file_executor.on_run_script(self)

    def on_redo_script(self):
        """Handle Teardown button click - delegate to file executor."""
        if self.file_executor:
            self.file_executor.on_redo_script(self)

    def on_incremental_build_script(self):
        """Handle Incremental Build button click - delegate to file executor."""
        if self.file_executor:
            self.file_executor.on_incremental_build_script(self)

    def update_capture_button_state(self):
        """Delegate to drag drop handler."""
        if self.drag_drop_handler:
            self.drag_drop_handler.update_capture_button_state()

    def update_input_placeholder(self):
        """Delegate to drag drop handler."""
        if self.drag_drop_handler:
            self.drag_drop_handler.update_input_placeholder()

    def on_capture_screenshot(self):
        """Handle Capture button click - captures scene screenshot or clears all if already captured."""
        # If images are already captured, clicking again clears all of them
        if len(self.captured_images) > 0:
            image_count = len(self.captured_images)
            self.captured_images = []
            self.update_capture_button_state()
            self.message_handler.append_message(
                "System",
                f"All {image_count} captured {self._pluralize('image', image_count)} discarded. No images will be attached.",
            )
            return

        if not self.image_context:
            self.message_handler.append_message("System", "ImageContext not configured")
            return

        if self.is_ai_busy:
            self.message_handler.append_message("System", "AI is currently processing. Please wait...")
            return

        # Show capturing message
        self.message_handler.append_message("System", "Capturing screenshot...")

        # Force UI to update
        QCoreApplication.processEvents()

        try:
            # Fit all objects in view before capturing (so user can see what will be captured)
            self.image_context.fit()

            # Capture screenshot with base64 encoding using image_context
            result = self.image_context.capture_encoded(perspective="isometric")

            if result is None or not result.get("success"):
                self.message_handler.append_message("System", "Screenshot capture failed")
                return

            file_path = result.get("file", "unknown")

            # Show preview dialog for user to confirm or cancel (and potentially annotate)
            preview_dialog = ImagePreviewDialog(file_path, self)
            if preview_dialog.exec_() == QDialog.Accepted and preview_dialog.is_confirmed():
                # User confirmed - the annotated image has been saved to file_path
                # Re-encode the potentially modified image
                import base64

                try:
                    with open(file_path, "rb") as image_file:
                        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

                    # Update the result with the new base64 encoding
                    result["image_base64"] = image_base64

                    # Add the captured (and potentially annotated) image data to the list
                    self.captured_images.append(result)

                    # Visual feedback - update button to show images are ready
                    self.update_capture_button_state()

                    # Show success message
                    image_count = len(self.captured_images)
                    self.message_handler.append_message(
                        "System",
                        f"Screenshot confirmed!\n"
                        f"Saved to: {file_path}\n"
                        f"{image_count} {self._pluralize('image', image_count)} ready to attach to your next message.",
                    )
                except Exception as e:
                    self.message_handler.append_message("System", f"Error encoding annotated image: {str(e)}")
            else:
                # User cancelled - discard the image
                self.message_handler.append_message("System", "Screenshot cancelled. Image will not be attached.")

        except Exception:
            import traceback

            error_msg = f"Error capturing screenshot:\n{traceback.format_exc()}"
            self.message_handler.append_message("System", error_msg)

    def on_export_clicked(self):
        """Handle Export button click - delegate to file executor."""
        if self.file_executor:
            self.file_executor.on_export_clicked()

    def on_import_clicked(self):
        """Handle Import button click - delegate to file executor."""
        if self.file_executor:
            self.file_executor.on_import_clicked()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Delegate to drag drop handler."""
        if self.drag_drop_handler:
            self.drag_drop_handler.drag_enter_event(event)

    def dragMoveEvent(self, event):
        """Delegate to drag drop handler."""
        if self.drag_drop_handler:
            self.drag_drop_handler.drag_move_event(event)

    def dropEvent(self, event: QDropEvent):
        """Delegate to drag drop handler."""
        if self.drag_drop_handler:
            self.drag_drop_handler.drop_event(event)

    def closeEvent(self, event):
        """Handle window close event."""
        self.handle_exit()

        # Call the window close callback to clear the active window reference
        if self.window_close_callback:
            self.window_close_callback()

        event.accept()
