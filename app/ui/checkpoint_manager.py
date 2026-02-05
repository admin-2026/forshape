"""
Checkpoint management for ForShape AI GUI.

This module provides functionality for listing and restoring checkpoints
from the edit history.
"""

from PySide2.QtWidgets import QDialog

from ..dialogs import CheckpointSelector


class CheckpointManager:
    """Handles checkpoint listing and restoration."""

    def __init__(self, config, logger):
        """
        Initialize the checkpoint manager.

        Args:
            config: ConfigurationManager instance for accessing directories
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # Message handler will be set later
        self.message_handler = None

    def set_message_handler(self, message_handler):
        """Set the message handler reference."""
        self.message_handler = message_handler

    def show_checkpoint_selector(self, parent_widget):
        """
        Show checkpoint selector and restore files if user confirms.

        Args:
            parent_widget: Parent widget for the dialog
        """
        # Get the edits directory from the context provider
        if not self.config:
            if self.message_handler:
                self.message_handler.display_error("Context provider not initialized.")
            return

        edits_dir = self.config.get_edits_dir()

        # Check if edits directory exists
        if not edits_dir.exists():
            if self.message_handler:
                self.message_handler.append_message(
                    "System", "No edit history found. The edits directory does not exist yet."
                )
            return

        # Get all sessions using EditHistory
        from agent.edit_history import EditHistory

        session_names = EditHistory.list_all_sessions(edits_dir)

        if not session_names:
            if self.message_handler:
                self.message_handler.append_message("System", "No checkpoints found. Edit history is empty.")
            return

        # Get session info for each session
        sessions = []
        for session_name in session_names:
            session_info = EditHistory.get_session_info(edits_dir, session_name)
            if "error" not in session_info:
                sessions.append(session_info)

        if not sessions:
            if self.message_handler:
                self.message_handler.append_message("System", "No valid checkpoints found.")
            return

        # Show checkpoint selector dialog
        dialog = CheckpointSelector(sessions, parent_widget)
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

        if self.message_handler:
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
            if self.message_handler:
                self.message_handler.append_message("System", f"✓ {message}")
            self.logger.info(f"Restored checkpoint: {conversation_id}")
        else:
            if self.message_handler:
                self.message_handler.display_error(f"Failed to restore checkpoint:\n{message}")
            self.logger.error(f"Failed to restore checkpoint {conversation_id}: {message}")
