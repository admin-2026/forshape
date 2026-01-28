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
    ContextProvider,
    ForShapeMainWindow,
    Logger,
    LogLevel,
    PrestartChecker,
    APIDebugger,
    ApiKeyManager
)
from agent.tools.tool_manager import ToolManager
from agent.request import RequestBuilder
from agent.async_ops import WaitManager, PermissionInput
from agent.permission_manager import PermissionManager


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

        # Check and install all dependencies
        self.dependency_manager = DependencyManager(self.config.get_libs_dir())
        success, error_msg = self.dependency_manager.check_and_install_all()

        if not success:
            print(f"\n{'='*60}")
            print(f"ERROR: Cannot initialize ForShapeAI")
            print(f"{'='*60}")
            print(f"\n{error_msg}")
            print("\nPlease install the required libraries to use ForShape AI.")
            print(f"{'='*60}\n")
            return

        # Initialize prestart checker (will setup directories and check API key)
        # Create a minimal logger before directories exist
        self.logger = Logger(min_level=LogLevel.INFO)
        self.prestart_checker = PrestartChecker(self.context_provider, self.config, self.logger)

        # Store model preference for later
        self.model = model

        # These will be initialized after prestart checks pass
        self.history_logger = None
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
        # Reinitialize logger for terminal output
        self.logger = Logger(min_level=LogLevel.INFO)
        self.logger.info("ForShape AI initialization completed")

        # Initialize history logger
        self.history_logger = HistoryLogger(self.config.get_history_dir())

        # Initialize ImageContext for screenshot capture
        from shapes.image_context import ImageContext
        images_dir = self.config.get_history_dir() / "images"
        self.image_context = ImageContext(str(images_dir))

        # Initialize API debugger (disabled by default)
        self.api_debugger = APIDebugger(enabled=False, output_dir=str(self.config.get_api_dumps_dir()))

        # Initialize edit history for tracking file changes
        from agent.edit_history import EditHistory
        self.edit_history = EditHistory(
            working_dir=self.context_provider.working_dir,
            edits_dir=str(self.config.get_edits_dir()),
            logger=self.logger
        )

        # Initialize AI agent with API key from keyring
        api_key_manager = ApiKeyManager()
        from agent.provider_config_loader import ProviderConfigLoader

        # Find the first provider with an API key
        provider_loader = ProviderConfigLoader()
        configured_providers = provider_loader.get_providers()

        provider = None
        api_key = None
        provider_config = None

        for prov_config in configured_providers:
            key = api_key_manager.get_api_key(prov_config.name)
            if key:
                provider = prov_config.name
                api_key = key
                provider_config = prov_config
                self.logger.info(f"Using provider: {prov_config.display_name} ({prov_config.name})")
                break

        if not api_key:
            self.logger.warning("No API keys found for any configured provider. AI features will not work.")
            # Default to openai for backwards compatibility
            provider = "openai"

        # Determine the model to use
        if provider_config and provider_config.default_model:
            agent_model = provider_config.default_model
        else:
            agent_model = self.model if self.model else "gpt-5.1"

        # Create wait manager and permission system
        wait_manager = WaitManager()
        permission_input = PermissionInput()
        permission_manager = PermissionManager(permission_requester=permission_input)

        # Create and configure tool manager with all tools
        tool_manager = ToolManager(logger=self.logger)
        self._register_tools(
            tool_manager,
            wait_manager,
            permission_manager
        )

        # Create request builder for AI context
        request_builder = RequestBuilder(self.context_provider)

        # Create AI agent with pre-configured tool manager
        self.ai_client = AIAgent(
            api_key,
            self.context_provider,
            request_builder,
            model=agent_model,
            logger=self.logger,
            tool_manager=tool_manager,
            wait_manager=wait_manager,
            permission_input=permission_input,
            api_debugger=self.api_debugger,
            provider=provider,
            provider_config=provider_config
        )
        self.logger.info(f"AI client initialized with provider: {provider}, model: {agent_model}")

        # Update the main window with the initialized components
        if self.main_window:
            self.main_window.set_components(self.ai_client, self.history_logger, self.logger, self.image_context, self.api_debugger)

    def _register_tools(
        self,
        tool_manager: ToolManager,
        wait_manager: WaitManager,
        permission_manager: PermissionManager
    ) -> None:
        """
        Register all tools with the tool manager.

        Args:
            tool_manager: ToolManager instance to register tools with
            wait_manager: WaitManager instance for user interactions
            permission_manager: PermissionManager instance for permission checks
        """
        from agent.tools.file_access_tools import FileAccessTools
        from agent.tools.interaction_tools import InteractionTools
        from gui.tools import FreeCADTools, VisualizationTools

        # Register file access tools
        file_access_tools = FileAccessTools(
            working_dir=self.context_provider.working_dir,
            logger=self.logger,
            permission_manager=permission_manager,
            edit_history=self.edit_history,
            exclude_folders=[self.config.get_forshape_folder_name(), ".git", "__pycache__"],
            exclude_patterns=[]
        )
        tool_manager.register_provider(file_access_tools)

        # Register interaction tools
        interaction_tools = InteractionTools(wait_manager)
        tool_manager.register_provider(interaction_tools)

        # Register FreeCAD object manipulation tools
        freecad_tools = FreeCADTools(permission_manager=permission_manager)
        tool_manager.register_provider(freecad_tools)

        # Register visualization tools if image_context is available
        if self.image_context is not None:
            visualization_tools = VisualizationTools(image_context=self.image_context)
            tool_manager.register_provider(visualization_tools)

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
