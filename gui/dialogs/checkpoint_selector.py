"""
Checkpoint selector dialog for choosing an edit history checkpoint to rewind to.
"""

from PySide2.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget,
                                QListWidgetItem, QDialogButtonBox, QTextEdit)
from PySide2.QtGui import QFont
from PySide2.QtCore import Qt


class CheckpointSelector(QDialog):
    """Dialog for selecting an edit history checkpoint to restore."""

    def __init__(self, sessions, parent=None):
        """
        Initialize the checkpoint selector dialog.

        Args:
            sessions: List of session dictionaries with checkpoint information
            parent: Parent widget
        """
        super().__init__(parent)
        self.sessions = sessions
        self.selected_session = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Rewind to Checkpoint")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Add label
        label = QLabel("Select a checkpoint to restore file edits from:")
        label.setFont(QFont("Consolas", 10, QFont.Bold))
        layout.addWidget(label)

        # Add list widget
        self.checkpoint_list = QListWidget()
        self.checkpoint_list.setFont(QFont("Consolas", 9))

        for session in self.sessions:
            # Format display text
            conv_id = session.get("conversation_id", "unknown")
            timestamp = session.get("timestamp", "unknown")
            file_count = session.get("file_count", 0)

            display_text = f"{conv_id} | {timestamp} | {file_count} file(s)"

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, session)  # Store session data
            self.checkpoint_list.addItem(item)

        self.checkpoint_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.checkpoint_list.currentItemChanged.connect(self.on_selection_changed)
        layout.addWidget(self.checkpoint_list, stretch=3)

        # Add info panel to show details about selected checkpoint
        info_label = QLabel("Checkpoint Details:")
        info_label.setFont(QFont("Consolas", 9, QFont.Bold))
        layout.addWidget(info_label)

        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setFont(QFont("Consolas", 9))
        self.info_display.setMaximumHeight(100)
        self.info_display.setText("Select a checkpoint to see details...")
        layout.addWidget(self.info_display, stretch=1)

        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_selection_changed(self, current, previous):
        """
        Handle selection change to update info display.

        Args:
            current: Current selected item
            previous: Previous selected item
        """
        if current:
            session = current.data(Qt.UserRole)
            info_text = f"Conversation ID: {session.get('conversation_id', 'unknown')}\n"
            info_text += f"Timestamp: {session.get('timestamp', 'unknown')}\n"
            info_text += f"Files backed up: {session.get('file_count', 0)}\n"

            # Add user request if available
            user_request = session.get('user_request')
            if user_request:
                # Truncate long requests for display
                if len(user_request) > 200:
                    user_request = user_request[:200] + "..."
                info_text += f"User Request: {user_request}\n"

            info_text += f"Path: {session.get('path', 'unknown')}"
            self.info_display.setText(info_text)
        else:
            self.info_display.setText("Select a checkpoint to see details...")

    def on_item_double_clicked(self, item):
        """Handle double-click on a list item."""
        self.selected_session = item.data(Qt.UserRole)
        self.accept()

    def on_ok_clicked(self):
        """Handle OK button click."""
        current_item = self.checkpoint_list.currentItem()
        if current_item:
            self.selected_session = current_item.data(Qt.UserRole)
            self.accept()

    def get_selected_session(self):
        """Return the selected session data."""
        return self.selected_session
