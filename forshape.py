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

from agent import ChatHistoryManager, StepJumpController
from agent.async_ops import PermissionInput, WaitManager
from agent.permission_manager import PermissionManager
from app import (
    ActiveDocumentObserver,
    AIAgent,
    APIDebugger,
    ApiKeyManager,
    ConfigurationManager,
    DependencyManager,
    ForShapeMainWindow,
    HistoryLogger,
    Logger,
    LogLevel,
    PrestartChecker,
)
from app.forshape.step_builders import (
    build_diff_step,
    build_doc_print_step,
    build_drop_lint_history_step,
    build_drop_review_history_step,
    build_lint_err_fix_step,
    build_lint_step,
    build_main_step,
    build_review_step,
    build_router_step,
)


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
        # Initialize configuration manager - single source of truth for working directory
        self.config = ConfigurationManager()
        # Note: Directory setup moved to prestart checker for interactive handling

        # Check and install all dependencies
        self.dependency_manager = DependencyManager(self.config.get_libs_dir())
        success, error_msg = self.dependency_manager.check_and_install_all()

        if not success:
            print(f"\n{'=' * 60}")
            print("ERROR: Cannot initialize ForShapeAI")
            print(f"{'=' * 60}")
            print(f"\n{error_msg}")
            print("\nPlease install the required libraries to use ForShape AI.")
            print(f"{'=' * 60}\n")
            self._init_success = False
            return

        # Mark initialization as successful
        self._init_success = True

        # Initialize prestart checker (will setup directories and check API key)
        self.logger = Logger(min_level=LogLevel.INFO)
        self.prestart_checker = PrestartChecker(
            self.config, self.logger, completion_callback=self._complete_initialization
        )

        # Store model preference for later
        self.model = model

        # These will be initialized after prestart checks pass
        self.history_logger = None
        self.ai_client = None

        # GUI window (will be created in run())
        self.main_window = None
        self.document_observer = None
        self.running = True

    def _complete_initialization(self):
        """
        Complete initialization after prestart checks pass.

        This creates the AI agent, history logger, and other components that
        require the configuration directories and API key to exist.
        """
        self.logger = Logger(min_level=LogLevel.INFO)
        self.logger.info("ForShape AI initialization completed")

        self.history_logger = HistoryLogger(self.config.get_history_dir())

        from shapes.image_context import ImageContext

        images_dir = self.config.get_history_dir() / "images"
        self.image_context = ImageContext(str(images_dir))

        self.api_debugger = APIDebugger(enabled=False, output_dir=str(self.config.get_api_dumps_dir()))

        from agent.edit_history import EditHistory

        self.edit_history = EditHistory(
            working_dir=self.config.working_dir, edits_dir=str(self.config.get_edits_dir()), logger=self.logger
        )

        api_key_manager = ApiKeyManager()
        from agent.provider_config_loader import ProviderConfigLoader

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
            provider = "openai"

        if provider_config and provider_config.default_model:
            agent_model = provider_config.default_model
        else:
            agent_model = self.model if self.model else "gpt-5.1"

        history_manager = ChatHistoryManager()
        wait_manager = WaitManager()
        permission_input = PermissionInput()
        permission_manager = PermissionManager(permission_requester=permission_input)

        # Router can jump to doc_print (which goes to main), main, lint, lint_err_fix
        step_jump_controller = StepJumpController(
            valid_destinations={
                "router": ["doc_print", "main", "lint", "lint_err_fix"],
            }
        )

        main_step, tool_executor = build_main_step(
            self.config, self.logger, self.edit_history, self.image_context, wait_manager, permission_manager
        )
        doc_print_step = build_doc_print_step(tool_executor, self.logger)
        router_step, _ = build_router_step(
            self.config,
            self.logger,
            self.edit_history,
            self.image_context,
            wait_manager,
            permission_manager,
            step_jump_controller,
        )
        lint_step = build_lint_step(self.config, self.logger)
        lint_err_fix_step = build_lint_err_fix_step(self.config, self.logger, self.edit_history, permission_manager)
        diff_step = build_diff_step(self.edit_history, self.logger)
        review_step = build_review_step(self.config, self.logger, self.edit_history, permission_manager)
        drop_lint_history_step = build_drop_lint_history_step(history_manager, self.logger)
        drop_review_history_step = build_drop_review_history_step(history_manager, self.logger)

        # Flow: router -> (doc_print -> main -> diff -> review -> drop_review_history -> lint -> lint_err_fix -> drop_lint_history) or direct tool use
        self.ai_client = AIAgent(
            api_key,
            model=agent_model,
            steps={
                "router": router_step,
                "doc_print": doc_print_step,
                "main": main_step,
                "lint": lint_step,
                "lint_err_fix": lint_err_fix_step,
                "drop_lint_history": drop_lint_history_step,
                "diff": diff_step,
                "review": review_step,
                "drop_review_history": drop_review_history_step,
            },
            # start_step="router",  # routing is under construction
            start_step="doc_print",
            logger=self.logger,
            edit_history=self.edit_history,
            history_manager=history_manager,
            api_debugger=self.api_debugger,
            provider=provider,
            provider_config=provider_config,
            response_steps=["router", "main", "lint_err_fix", "review"],
            step_jump_controller=step_jump_controller,
        )
        self.logger.info(f"AI client initialized with provider: {provider}, model: {agent_model}")

        if self.main_window:
            self.main_window.set_components(
                self.ai_client,
                self.history_logger,
                wait_manager,
                permission_input,
                self.logger,
                self.image_context,
                self.api_debugger,
            )

    def run(self):
        """Start the interactive GUI interface."""
        # Check if initialization was successful
        if not getattr(self, "_init_success", True):
            return 1

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
            config=self.config,
            exit_handler=self.handle_exit,
            prestart_checker=self.prestart_checker,
            window_close_callback=ForShapeAI._clear_active_window,
        )

        # Store the window as the active window
        ForShapeAI._active_window = self.main_window

        self.main_window.show()

        # Set the message handler for prestart checker
        self.prestart_checker.set_message_handler(self.main_window.message_handler)

        # Check for newer version in background
        self.prestart_checker.check_version()

        # Create and register document observer to monitor active document changes
        self.document_observer = ActiveDocumentObserver(
            prestart_checker=self.prestart_checker,
            logger=self.logger,
            message_handler=self.main_window.message_handler,
            enable_ai_mode_callback=self.main_window.enable_ai_mode,
        )
        if self.document_observer.register():
            self.logger.info("Document observer registered successfully")
        else:
            self.logger.warning("Failed to register document observer")

        # Run initial prestart check.
        # If status becomes "ready", the completion_callback on PrestartChecker
        # fires _complete_initialization automatically.
        status = self.prestart_checker.check()
        if status == "ready":
            self.main_window.enable_ai_mode()

        # Bring window to front after initialization
        self.main_window.raise_()
        self.main_window.activateWindow()

        # Start Qt event loop
        return app.exec_()

    def handle_exit(self):
        """Handle graceful exit of the application."""
        # Unregister document observer
        if self.document_observer is not None:
            self.document_observer.unregister()
            self.logger.info("Document observer unregistered")

        # Write session end marker to log
        if self.history_logger is not None:
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
