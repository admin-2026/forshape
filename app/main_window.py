"""
Main window GUI for ForShape AI.

This module provides the interactive GUI interface using PySide2.
"""

from typing import TYPE_CHECKING

from PySide2.QtCore import QCoreApplication, Qt
from PySide2.QtGui import QDragEnterEvent, QDropEvent
from PySide2.QtWidgets import (
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from agent.provider_config_loader import ProviderConfigLoader

from .ui import (
    AIRequestController,
    CheckpointManager,
    ConversationView,
    DragDropHandler,
    FileExecutor,
    InputAreaManager,
    MenuBarManager,
    MessageFormatter,
    ModelMenuManager,
    PrestartHandler,
    ScreenshotHandler,
    WelcomeWidget,
)
from .ui_config_manager import UIConfigManager
from .variables import VariablesView

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
        self.window_close_callback = window_close_callback

        # Shared state for attachments
        self.captured_images = []
        self.attached_files = []

        # API debugger instance (will be set later)
        self.api_debugger = None

        # Initialize message formatter
        self.message_formatter = MessageFormatter(self.logger)

        # Load provider configuration
        self.provider_config_loader = ProviderConfigLoader()

        # Initialize UI config manager for persisting menu selections
        self.ui_config_manager = UIConfigManager(self.config.get_forshape_dir())
        self.ui_config_manager.load()

        # Initialize component managers
        self._init_component_managers(prestart_checker, completion_callback)

        # Enable drag and drop
        self.setAcceptDrops(True)

        self.setup_ui()

    def _init_component_managers(self, prestart_checker, completion_callback):
        """Initialize all component managers."""
        # Menu bar manager
        self.menu_bar_manager = MenuBarManager(self.ui_config_manager, self.logger)

        # Checkpoint manager
        self.checkpoint_manager = CheckpointManager(self.config, self.logger)

        # Screenshot handler
        self.screenshot_handler = ScreenshotHandler(self.image_context, self.logger)

        # Prestart handler
        self.prestart_handler = PrestartHandler(prestart_checker, completion_callback, self.logger)

        # AI request controller
        self.ai_request_controller = AIRequestController(self.logger)
        self.ai_request_controller.set_ai_client(self.ai_client)
        self.ai_request_controller.set_history_logger(self.history_logger)

        # Input area manager
        self.input_area_manager = InputAreaManager(self.message_formatter, self.logger)

        # File executor and drag drop handler (will be configured after UI setup)
        self.file_executor = None
        self.drag_drop_handler = None
        self.model_menu_manager = None

    def setup_ui(self):
        """Setup the user interface components."""
        self.setWindowTitle("ForShape AI - Interactive 3D Shape Generator")
        self.setMinimumSize(1000, 600)

        # Create menu bar using MenuBarManager
        self.menu_bar_manager.create_view_menu(self)

        # Create Model menu dynamically from provider config
        model_menu = self.menuBar().addMenu("Model")
        self._create_model_menu_items(model_menu)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create horizontal splitter for conversation and variables
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Conversation area
        conversation_widget = QWidget()
        conversation_layout = QVBoxLayout(conversation_widget)
        conversation_layout.setContentsMargins(0, 0, 0, 0)

        self.welcome_widget = WelcomeWidget(lambda: self.ai_client, self.config)
        self.message_handler = ConversationView(self.message_formatter, self.logger, self.welcome_widget)

        conversation_layout.addWidget(self.message_handler.get_widget())

        # Variables area
        self.variables_widget = VariablesView(working_dir=self.config.working_dir)

        # Add panels to splitter
        splitter.addWidget(conversation_widget)
        splitter.addWidget(self.variables_widget)

        # Set initial splitter sizes (75% conversation, 25% variables)
        splitter.setSizes([750, 250])

        main_layout.addWidget(splitter, stretch=1)

        # Create input area using InputAreaManager
        input_container = self.input_area_manager.create_widget(self.on_user_input)
        self.input_area_manager.set_state_references(self.captured_images, self.attached_files)
        self.input_area_manager.connect_attachment_removed(self._on_attachment_removed)

        # Connect input area signals
        self.input_area_manager.capture_requested.connect(self._on_capture_screenshot)
        self.input_area_manager.new_chat_requested.connect(self.clear_conversation)
        self.input_area_manager.rewind_requested.connect(self._on_rewind_clicked)
        self.input_area_manager.cancel_requested.connect(self._on_cancel_ai)
        self.input_area_manager.run_script_requested.connect(self._on_run_script)

        main_layout.addWidget(input_container)

        # Wire up component managers with references they need
        self._wire_component_managers()

        # Restore UI state from config
        self.menu_bar_manager.restore_variables_panel_state()

        # Display welcome message
        self.message_handler.display_welcome()

    def _wire_component_managers(self):
        """Wire up all component managers with their required references."""
        # Menu bar manager
        self.menu_bar_manager.set_message_handler(self.message_handler)
        self.menu_bar_manager.set_variables_widget(self.variables_widget)
        self.menu_bar_manager.set_config(self.config)

        # Checkpoint manager
        self.checkpoint_manager.set_message_handler(self.message_handler)

        # Screenshot handler
        self.screenshot_handler.set_message_handler(self.message_handler)
        self.screenshot_handler.set_state_references(
            self.captured_images,
            self.input_area_manager.attachment_widget,
            lambda: self.ai_request_controller.is_busy(),
        )

        # Prestart handler
        self.prestart_handler.set_message_handler(self.message_handler)
        self.prestart_handler.set_config(self.config)
        self.prestart_handler.set_main_window(self)

        # AI request controller
        self.ai_request_controller.set_message_handler(self.message_handler)
        self.ai_request_controller.set_token_status_label(self.input_area_manager.token_status_label)
        self.ai_request_controller.set_cancel_button(self.input_area_manager.cancel_button)
        self.ai_request_controller.set_main_window(self)

        # File executor
        self.file_executor = FileExecutor(self.config, self.message_handler, self.logger)

        # Drag drop handler
        self.drag_drop_handler = DragDropHandler(self.message_handler, self.logger, self.image_context)
        self.drag_drop_handler.set_state_references(
            self.captured_images,
            self.attached_files,
            lambda: self.ai_request_controller.is_busy(),
            self.input_area_manager.input_field,
            self.input_area_manager.attachment_widget,
        )

        # Model menu manager
        self.model_menu_manager = ModelMenuManager(
            self.provider_config_loader, self.message_handler, self.logger, self.ui_config_manager
        )
        self.model_menu_manager.set_ai_client(self.ai_client)
        self.model_menu_manager.set_callbacks(
            self.prestart_handler.prestart_checker,
            self.prestart_handler.completion_callback,
            self.enable_ai_mode,
        )

        # Refresh the entire Model menu to use the real manager
        self.model_menu_manager.refresh_model_menu(self)

        # Clean up temp manager references
        if hasattr(self, "_temp_model_combos"):
            del self._temp_model_combos

    def _create_model_menu_items(self, model_menu):
        """
        Dynamically create model menu items from provider configuration.
        Delegates to ModelMenuManager.

        Args:
            model_menu: The QMenu to add model selection widgets to
        """
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

    # -------------------------------------------------------------------------
    # Signal handlers - delegate to component managers
    # -------------------------------------------------------------------------

    def _on_capture_screenshot(self):
        """Handle Capture button click."""
        self.screenshot_handler.capture(self)

    def _on_rewind_clicked(self):
        """Handle Rewind button click."""
        self.checkpoint_manager.show_checkpoint_selector(self)

    def _on_cancel_ai(self):
        """Handle Cancel button click."""
        self.ai_request_controller.cancel_request()

    def _on_run_script(self, mode: str):
        """Handle script execution button clicks."""
        if not self.file_executor:
            return

        if mode == "rebuild":
            self.file_executor.on_run_script(self)
        elif mode == "teardown":
            self.file_executor.on_redo_script(self)
        elif mode == "incremental":
            self.file_executor.on_incremental_build_script(self)
        elif mode == "export":
            self.file_executor.on_export_clicked()
        elif mode == "import":
            self.file_executor.on_import_clicked()

    def _on_attachment_removed(self, chip_type, data):
        """Handle attachment chip removal."""
        if chip_type == "file":
            self.input_area_manager.update_input_placeholder()

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

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

    def enable_ai_mode(self):
        """Enable normal AI interaction mode after prestart checks pass."""
        self.prestart_handler.enable_ai_mode(self.ai_client)

    def on_user_input(self):
        """Handle user input when Enter is pressed."""
        user_input = self.input_area_manager.get_text()

        if not user_input:
            return

        # Display user input
        self.message_handler.append_message("You", user_input)

        # Clear input field
        self.input_area_manager.clear_input()

        # Force UI to update immediately
        QCoreApplication.processEvents()

        # Handle prestart check mode
        if self.prestart_handler.is_active():
            should_enable_ai = self.prestart_handler.handle_input(user_input, self)
            if should_enable_ai:
                self.enable_ai_mode()
            return

        # Check if AI client is available
        if not self.ai_client:
            self.message_handler.append_message(
                "System", "⚠ AI is not yet initialized. Please wait for setup to complete."
            )
            return

        # Check if AI is currently busy
        if self.ai_request_controller.is_busy():
            self.ai_request_controller.add_pending_message(user_input)
            return

        # Submit request to AI
        self.ai_request_controller.submit_request(user_input, self.attached_files, self.captured_images)

        # Clear captured images after sending
        if self.captured_images:
            self.captured_images.clear()

        # Clear attached files and reset placeholder after sending
        if self.attached_files:
            self.attached_files.clear()
            self.input_area_manager.update_input_placeholder()

        self.input_area_manager.refresh_attachments()

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

        # Update AI request controller
        self.ai_request_controller.set_ai_client(ai_client)
        self.ai_request_controller.set_history_logger(history_logger)

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
            # Update screenshot handler's image context
            self.screenshot_handler.set_image_context(image_context)
            # Update drag drop handler's image context
            if self.drag_drop_handler:
                self.drag_drop_handler.image_context = image_context

        # Update api_debugger if provided
        if api_debugger is not None:
            self.api_debugger = api_debugger
            self.menu_bar_manager.set_api_debugger(api_debugger)
            self.menu_bar_manager.restore_api_dump_state()

        # Update logger if provided
        if logger is not None:
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

        # Update menu bar manager's AI client
        self.menu_bar_manager.set_ai_client(ai_client)

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

    # -------------------------------------------------------------------------
    # Drag and drop event delegation
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Window events
    # -------------------------------------------------------------------------

    def closeEvent(self, event):
        """Handle window close event."""
        self.handle_exit()

        # Call the window close callback to clear the active window reference
        if self.window_close_callback:
            self.window_close_callback()

        event.accept()
