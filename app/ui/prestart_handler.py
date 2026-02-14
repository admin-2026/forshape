"""
Prestart validation handling for ForShape AI GUI.

This module provides functionality for managing the prestart validation flow
and transition to AI mode.
"""

from PySide2.QtCore import Qt


class PrestartHandler:
    """Manages prestart validation flow and transition to AI mode."""

    def __init__(self, prestart_checker, completion_callback, logger):
        """
        Initialize the prestart handler.

        Args:
            prestart_checker: PrestartChecker instance for validation (can be None)
            completion_callback: Callback to complete initialization after checks pass
            logger: Logger instance
        """
        self.prestart_checker = prestart_checker
        self.completion_callback = completion_callback
        self.logger = logger

        # Prestart check mode - True if prestart checks are pending
        self.prestart_check_mode = True if prestart_checker else False

        # References that will be set later
        self.message_handler = None
        self.config = None
        self.main_window = None

    def set_message_handler(self, message_handler):
        """Set the message handler reference."""
        self.message_handler = message_handler

    def set_config(self, config):
        """Set the config reference."""
        self.config = config

    def set_main_window(self, main_window):
        """Set the main window reference for bringing to front."""
        self.main_window = main_window

    def is_active(self) -> bool:
        """Check if prestart check mode is active."""
        return self.prestart_check_mode

    def handle_input(self, user_input: str, parent_widget):
        """
        Handle user input during prestart check mode.

        Args:
            user_input: The user's input
            parent_widget: Parent widget for dialogs

        Returns:
            bool: True if input was handled in prestart mode, False if prestart is complete
        """
        if not self.prestart_check_mode:
            return False

        if not self.prestart_checker:
            self.prestart_check_mode = False
            return False

        current_status = self.prestart_checker.get_status()

        if current_status == "dir_mismatch":
            # Handle directory mismatch response (yes/no/cancel)
            should_continue = self.prestart_checker.handle_directory_mismatch(user_input)
            if should_continue:
                # Re-run prestart checks
                status = self.prestart_checker.check()
                if status == "ready":
                    # Complete initialization if callback provided
                    if self.completion_callback:
                        self.completion_callback()
                    return True  # Signal that AI mode should be enabled
            else:
                # User cancelled or error
                self.prestart_check_mode = False
        else:
            # For "waiting", "need_api_key", or other status, re-run checks when user provides input
            status = self.prestart_checker.check()
            if status == "ready":
                # Complete initialization if callback provided
                if self.completion_callback:
                    self.completion_callback()
                return True  # Signal that AI mode should be enabled
            elif status == "error":
                self.prestart_check_mode = False

        return False

    def enable_ai_mode(self, ai_client):
        """
        Enable normal AI interaction mode after prestart checks pass.

        Args:
            ai_client: The initialized AI client
        """
        self.prestart_check_mode = False

        # Update welcome message to show full AI details now that ai_client is initialized
        if ai_client and self.message_handler and self.config:
            context_status = "✓ FORSHAPE.md loaded" if self.config.has_forshape() else "✗ No FORSHAPE.md"
            self.message_handler.append_message(
                "System",
                f"🎉 **Initialization Complete!**\n\n"
                f"**Using model:** {ai_client.get_model()}\n"
                f"**Context:** {context_status}\n\n"
                f"You can now chat with the AI to generate 3D shapes!",
            )

        # Bring window to front after initialization completes
        if self.main_window:
            self.main_window.raise_()
            self.main_window.activateWindow()
            # Restore window if minimized
            if self.main_window.isMinimized():
                self.main_window.setWindowState(self.main_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)

    def enable_prestart_mode(self):
        """Re-enable prestart check mode (e.g., when document changes)."""
        self.prestart_check_mode = True

    def disable(self):
        """Disable prestart check mode without enabling AI mode."""
        self.prestart_check_mode = False
