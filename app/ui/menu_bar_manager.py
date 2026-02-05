"""
Menu bar management for ForShape AI GUI.

This module provides functionality for creating and managing the main window's menu bar,
including View menu actions (toggle variables, API dump, history dump, log level).
"""

from PySide2.QtWidgets import QAction

from .log_level_selector import LogLevelSelector


class MenuBarManager:
    """Creates and manages the main window menu bar."""

    def __init__(self, ui_config_manager, logger):
        """
        Initialize the menu bar manager.

        Args:
            ui_config_manager: UIConfigManager instance for persisting menu selections
            logger: Logger instance
        """
        self.ui_config_manager = ui_config_manager
        self.logger = logger

        # References that will be set later
        self.api_debugger = None
        self.ai_client = None
        self.message_handler = None
        self.variables_widget = None
        self.config = None

        # UI elements created by this manager
        self.toggle_variables_action = None
        self.toggle_api_dump_action = None
        self.dump_history_action = None
        self.log_level_selector = None

    def set_api_debugger(self, api_debugger):
        """Set the API debugger reference."""
        self.api_debugger = api_debugger

    def set_ai_client(self, ai_client):
        """Set the AI client reference."""
        self.ai_client = ai_client

    def set_message_handler(self, message_handler):
        """Set the message handler reference."""
        self.message_handler = message_handler

    def set_variables_widget(self, variables_widget):
        """Set the variables widget reference."""
        self.variables_widget = variables_widget

    def set_config(self, config):
        """Set the config reference."""
        self.config = config

    def create_view_menu(self, main_window):
        """
        Create and populate the View menu.

        Args:
            main_window: The main window to attach the menu to

        Returns:
            The created view menu
        """
        menubar = main_window.menuBar()
        view_menu = menubar.addMenu("View")

        # Add toggle variables action
        self.toggle_variables_action = QAction("Show Variables", main_window)
        self.toggle_variables_action.setCheckable(True)
        self.toggle_variables_action.triggered.connect(self.toggle_variables_panel)
        view_menu.addAction(self.toggle_variables_action)

        # Add toggle API dump action
        self.toggle_api_dump_action = QAction("Dump API Data", main_window)
        self.toggle_api_dump_action.setCheckable(True)
        self.toggle_api_dump_action.triggered.connect(self.toggle_api_dump)
        view_menu.addAction(self.toggle_api_dump_action)

        # Add dump history action
        self.dump_history_action = QAction("Dump History", main_window)
        self.dump_history_action.triggered.connect(self.dump_history)
        view_menu.addAction(self.dump_history_action)

        # Add log level dropdown
        view_menu.addSeparator()
        self.log_level_selector = LogLevelSelector()
        saved_log_level = self.ui_config_manager.get("log_level", "INFO")
        self.log_level_selector.set_level(saved_log_level)
        self.log_level_selector.combo.currentIndexChanged.connect(self.on_log_level_changed)
        view_menu.addAction(self.log_level_selector.create_menu_action(main_window))

        return view_menu

    def set_variables_panel_visibility(self, visible: bool):
        """
        Set the visibility of the variables panel and update the action text.

        Args:
            visible: True to show the variables panel, False to hide it
        """
        if not self.variables_widget:
            return

        if visible:
            self.variables_widget.show()
        else:
            self.variables_widget.hide()

        # Always set text to "Show Variables" as requested
        if self.toggle_variables_action:
            self.toggle_variables_action.setText("Show Variables")
            self.toggle_variables_action.setChecked(visible)

        # Save to config
        self.ui_config_manager.set("show_variables", visible)

    def toggle_variables_panel(self):
        """Toggle the visibility of the variables panel."""
        if self.variables_widget:
            self.set_variables_panel_visibility(not self.variables_widget.isVisible())

    def toggle_api_dump(self):
        """Toggle API data dumping."""
        if self.api_debugger is None:
            if self.message_handler:
                self.message_handler.append_message("System", "API debugger not initialized yet.")
            if self.toggle_api_dump_action:
                self.toggle_api_dump_action.setChecked(False)
            return

        # Toggle the enabled state
        new_state = not self.api_debugger.enabled
        self.api_debugger.set_enabled(new_state)

        # Save to config
        self.ui_config_manager.set("dump_api_data", new_state)

        if self.message_handler:
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
            if self.message_handler:
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

            if self.message_handler:
                self.message_handler.append_message(
                    "System", f"Conversation history dumped successfully!\nSaved to: {dump_path}"
                )
            self.logger.info(f"History dumped to: {dump_path}")

        except Exception as e:
            import traceback

            error_msg = f"Error dumping history: {str(e)}\n{traceback.format_exc()}"
            if self.message_handler:
                self.message_handler.display_error(error_msg)
            self.logger.error(f"Failed to dump history: {str(e)}")

    def on_log_level_changed(self, index: int):
        """
        Handle log level dropdown selection change.

        Args:
            index: The index of the selected item in the combo box
        """
        log_level = self.log_level_selector.current_level()
        self.logger.set_min_level(log_level)
        self.ui_config_manager.set("log_level", log_level.name)
        self.logger.info(f"Log level changed to {log_level.name}")

    def restore_api_dump_state(self):
        """Restore the API dump state from saved config."""
        if self.api_debugger:
            saved_dump_api_data = self.ui_config_manager.get("dump_api_data", False)
            if saved_dump_api_data:
                self.api_debugger.set_enabled(True)
                if self.toggle_api_dump_action:
                    self.toggle_api_dump_action.setChecked(True)

    def restore_variables_panel_state(self):
        """Restore the variables panel visibility from saved config."""
        show_variables = self.ui_config_manager.get("show_variables", True)
        self.set_variables_panel_visibility(show_variables)
