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

from gui import (
    DependencyManager,
    ConfigurationManager,
    HistoryLogger,
    AIAgent,
    ForShapeMainWindow,
    Logger,
    LogLevel
)


class ForShapeAI:
    """Main orchestrator class for the AI-powered GUI interface."""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the ForShape AI application.

        Args:
            model: Optional AI model identifier to use
        """
        # Initialize configuration manager
        self.config = ConfigurationManager()
        self.config.setup_directories()

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

        # Initialize history logger
        self.history_logger = HistoryLogger(self.config.get_history_dir())

        # Initialize logger for tool calls and system events
        log_file = self.config.get_history_dir() / "system.log"
        self.logger = Logger(log_file=log_file, min_level=LogLevel.INFO)
        self.logger.info("ForShape AI initialized")

        # Initialize AI agent with working directory for file operations and context
        api_key = self.config.get_api_key()
        working_dir = str(self.config.get_base_dir())
        # Use gpt-4o for tool calling support, fallback to user's model choice
        agent_model = model if model else "gpt-4o"
        self.ai_client = AIAgent(api_key, model=agent_model, working_dir=working_dir, logger=self.logger)

        # GUI window (will be created in run())
        self.main_window = None
        self.running = True

    def run(self):
        """Start the interactive GUI interface."""
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Create and show main window
        self.main_window = ForShapeMainWindow(
            ai_client=self.ai_client,
            history_logger=self.history_logger,
            logger=self.logger,
            special_commands_handler=self.handle_special_commands,
            exit_handler=self.handle_exit
        )
        self.main_window.show()

        # Start Qt event loop
        return app.exec_()

    def handle_special_commands(self, user_input: str, window: ForShapeMainWindow) -> bool:
        """
        Handle special commands like /help, /exit, /clear, etc.

        Args:
            user_input: The user's input string
            window: The main window instance

        Returns:
            True if a special command was handled, False otherwise
        """
        command = user_input.strip().lower()

        if command == "/exit":
            self.handle_exit()
            return True

        if command == "/help":
            help_text = """Available commands:
  /exit - Exit the program
  /help - Show this help message
  /clear - Clear conversation history (coming soon)

Simply type your questions or requests to interact with the AI."""
            window.append_message("System", help_text)
            return True

        # TODO: Implement other special commands (/clear, etc.)

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
