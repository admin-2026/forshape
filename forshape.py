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

import sys
from typing import Optional
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QObject, Signal, QMutex, QWaitCondition

from gui import (
    DependencyManager,
    ConfigurationManager,
    HistoryLogger,
    AIAgent,
    ContextProvider,
    ForShapeMainWindow,
    Logger,
    LogLevel,
    PermissionManager,
    PermissionResponse,
    PrestartChecker,
    APIDebugger
)


class PermissionDialogHelper(QObject):
    """Helper class to show permission dialogs on the main thread using signals."""

    # Signal to request permission dialog on main thread
    request_permission = Signal(str, str)  # path, operation

    def __init__(self, logger):
        """Initialize the helper.

        Args:
            logger: Logger instance for logging
        """
        super().__init__()
        self.logger = logger
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.permission_choice = None  # PermissionResponse enum value

        # Connect signal to slot
        self.request_permission.connect(self._show_dialog_slot)

    def _show_dialog_slot(self, path: str, operation: str):
        """Slot that shows the dialog on the main thread.

        Args:
            path: The path being accessed
            operation: The operation being performed
        """
        from PySide2.QtWidgets import QMessageBox
        from PySide2.QtCore import Qt

        try:
            msg = QMessageBox()
            msg.setWindowTitle("Permission Request")
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
            msg.setText(f"The AI agent is requesting permission to {operation} a file/directory.")
            msg.setInformativeText(f"Path: {path}")
            msg.setIcon(QMessageBox.Question)

            # Add buttons
            allow_once = msg.addButton("Allow Once", QMessageBox.AcceptRole)
            allow_session = msg.addButton("Allow for Session", QMessageBox.AcceptRole)
            deny = msg.addButton("Deny", QMessageBox.RejectRole)

            msg.exec_()
            clicked = msg.clickedButton()

            # Store the user's choice as a PermissionResponse enum
            self.mutex.lock()
            if clicked == allow_once:
                self.permission_choice = PermissionResponse.ALLOW_ONCE
                self.logger.info(f"Permission granted (once): {operation} on {path}")
            elif clicked == allow_session:
                self.permission_choice = PermissionResponse.ALLOW_SESSION
                self.logger.info(f"Permission granted (session): {operation} on {path}")
            else:
                self.permission_choice = PermissionResponse.DENY
                self.logger.info(f"Permission denied: {operation} on {path}")

            # Wake up the waiting thread
            self.wait_condition.wakeAll()
            self.mutex.unlock()

        except Exception as e:
            self.logger.error(f"Error showing permission dialog: {e}")
            self.mutex.lock()
            self.permission_choice = PermissionResponse.DENY
            self.wait_condition.wakeAll()
            self.mutex.unlock()


class ForShapeAI:
    """Main orchestrator class for the AI-powered GUI interface."""

    # Class variable to track the existing GUI window across instances
    _active_window = None

    @classmethod
    def _clear_active_window(cls):
        """Clear the active window reference when window is closed."""
        cls._active_window = None

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the ForShape AI application.

        Args:
            model: Optional AI model identifier to use
        """
        # Initialize context provider first - single source of truth for working directory
        self.context_provider = ContextProvider()

        # Initialize configuration manager with context provider
        self.config = ConfigurationManager(self.context_provider)
        # Note: Directory setup moved to prestart checker for interactive handling

        # Check and install dependencies
        self.dependency_manager = DependencyManager(self.config.get_libs_dir())
        success, error_msg = self.dependency_manager.check_and_install_openai()

        if not success:
            print(f"\n{'='*60}")
            print(f"ERROR: Cannot initialize ForShapeAI")
            print(f"{'='*60}")
            print(f"\n{error_msg}")
            print("\nPlease install the OpenAI library to use ForShape AI.")
            print(f"{'='*60}\n")
            return

        # Check and install markdown library (optional, for GUI markdown support)
        markdown_success, markdown_error = self.dependency_manager.check_and_install_markdown()
        if not markdown_success:
            print(f"Warning: Failed to install markdown library - GUI will use fallback rendering")
            print(f"Details: {markdown_error}")

        # Initialize prestart checker (will setup directories and check API key)
        # Create a minimal logger before directories exist
        import tempfile
        from pathlib import Path
        temp_log = Path(tempfile.gettempdir()) / "forshape_init.log"
        self.logger = Logger(log_file=temp_log, min_level=LogLevel.INFO)
        self.prestart_checker = PrestartChecker(self.context_provider, self.config, self.logger)

        # Store model preference for later
        self.model = model

        # These will be initialized after prestart checks pass
        self.history_logger = None
        self.permission_dialog_helper = None
        self.permission_manager = None
        self.ai_client = None

        # GUI window (will be created in run())
        self.main_window = None
        self.running = True

    def _complete_initialization(self):
        """
        Complete initialization after prestart checks pass.

        This creates the AI agent, history logger, and other components that
        require the configuration directories and API key to exist.
        """
        # Reinitialize logger with proper log file in .forshape directory
        log_file = self.config.get_history_dir() / "system.log"
        self.logger = Logger(log_file=log_file, min_level=LogLevel.INFO)
        self.logger.info("ForShape AI initialization completed")

        # Initialize history logger
        self.history_logger = HistoryLogger(self.config.get_history_dir())

        # Initialize permission dialog helper for cross-thread communication
        self.permission_dialog_helper = PermissionDialogHelper(self.logger)

        # Initialize permission manager with GUI callback
        self.permission_manager = PermissionManager(self._permission_callback)

        # Initialize ImageContext for screenshot capture
        from shapes.image_context import ImageContext
        images_dir = self.config.get_history_dir() / "images"
        self.image_context = ImageContext(str(images_dir))

        # Initialize API debugger (disabled by default)
        self.api_debugger = APIDebugger(enabled=False)

        # Initialize AI agent with API key and provider configuration
        provider_config = self.config.get_provider_config()
        providers = provider_config.get("providers", {})

        # Default to OpenAI provider
        provider = "openai"
        api_key = providers.get(provider)

        if not api_key:
            self.logger.warning("No OpenAI API key found in provider-config.json. AI features will not work.")

        # Use gpt-5 for tool calling support, fallback to user's model choice
        agent_model = self.model if self.model else "gpt-5"
        self.ai_client = AIAgent(
            api_key,
            self.context_provider,
            model=agent_model,
            logger=self.logger,
            permission_manager=self.permission_manager,
            image_context=self.image_context,
            api_debugger=self.api_debugger,
            provider=provider
        )
        self.logger.info(f"AI client initialized with provider: {provider}, model: {agent_model}")

        # Update the main window with the initialized components
        if self.main_window:
            self.main_window.set_components(self.ai_client, self.history_logger, self.logger, self.image_context, self.api_debugger)

    def run(self):
        """Start the interactive GUI interface."""
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Check if a window already exists and is visible
        if ForShapeAI._active_window is not None:
            try:
                # Check if the window is still valid and visible
                if ForShapeAI._active_window.isVisible():
                    # Bring the existing window to front
                    ForShapeAI._active_window.raise_()
                    ForShapeAI._active_window.activateWindow()
                    self.logger.info("Existing GUI window brought to front")
                    return 0
            except RuntimeError:
                # Window was deleted, clear the reference
                ForShapeAI._active_window = None

        # Create and show main window first (so user can see messages and interact with FreeCAD)
        # Pass None for components that haven't been initialized yet
        self.main_window = ForShapeMainWindow(
            ai_client=None,  # Will be set after prestart checks
            history_logger=None,  # Will be set after prestart checks
            logger=self.logger,
            context_provider=self.context_provider,
            special_commands_handler=self.handle_special_commands,
            exit_handler=self.handle_exit,
            prestart_checker=self.prestart_checker,
            completion_callback=self._complete_initialization,
            window_close_callback=ForShapeAI._clear_active_window
        )

        # Store the window as the active window
        ForShapeAI._active_window = self.main_window

        self.main_window.show()

        # Run initial prestart check
        status = self.prestart_checker.check(self.main_window)
        if status == "ready":
            # All checks passed, complete initialization (which also sets components) and enable AI
            self._complete_initialization()
            self.main_window.enable_ai_mode()
        elif status == "error":
            # Fatal error, keep window open but AI disabled
            self.main_window.prestart_check_mode = False
        else:
            # Waiting for user action ("waiting", "dir_mismatch", or "need_api_key")
            # Window will handle user input and re-run checks
            pass

        # Start Qt event loop
        return app.exec_()

    def _permission_callback(self, path: str, operation: str) -> PermissionResponse:
        """
        GUI-based permission callback for file access.

        This method uses signals and mutex/wait conditions to safely
        show dialogs from worker threads.

        Args:
            path: The path being accessed
            operation: The operation being performed (read, write, list)

        Returns:
            PermissionResponse indicating the user's choice
        """
        # Lock the mutex before emitting signal
        helper = self.permission_dialog_helper
        helper.mutex.lock()

        # Emit signal to show dialog on main thread
        helper.request_permission.emit(path, operation)

        # Wait for the dialog to complete (max 60 seconds)
        wait_result = helper.wait_condition.wait(helper.mutex, 60000)  # 60 second timeout

        if not wait_result:
            self.logger.error(f"Timeout waiting for permission response")
            helper.mutex.unlock()
            return PermissionResponse.DENY

        # Get the permission choice (already a PermissionResponse enum)
        choice = helper.permission_choice
        helper.mutex.unlock()

        # Return the PermissionResponse directly
        return choice

    def handle_special_commands(self, user_input: str, window: ForShapeMainWindow) -> bool:
        """
        Handle special commands like /help, /clear, etc.

        Args:
            user_input: The user's input string
            window: The main window instance

        Returns:
            True if a special command was handled, False otherwise
        """
        command = user_input.strip().lower()

        if command == "/help":
            help_text = """Available commands:
  /help - Show this help message
  /clear - Clear conversation history

Simply type your questions or requests to interact with the AI."""
            window.append_message("System", help_text)
            return True

        if command == "/clear":
            window.clear_conversation()
            return True

        return False

    def handle_exit(self):
        """Handle graceful exit of the application."""
        # Write session end marker to log
        self.history_logger.write_session_end()
        self.running = False


def start(model: Optional[str] = None):
    """
    Convenience function to start the interactive interface.

    Args:
        model: Optional AI model identifier to use
    """
    ai = ForShapeAI(model=model)
    ai.run()
