"""
Message handling for ForShape AI GUI.

This module provides functionality for displaying messages, logs, and handling
message formatting in the conversation display.
"""

import uuid

from PySide2.QtGui import QFont
from PySide2.QtWidgets import QListWidget

from .agent_progress_widget import AgentProgressWidget
from .message_widget import MessageWidget


class ConversationView:
    """Handles message display, formatting, and log management."""

    def __init__(self, message_formatter, logger, welcome_widget):
        """
        Initialize the message handler.

        Args:
            message_formatter: MessageFormatter instance
            logger: Logger instance
            welcome_widget: WelcomeWidget instance
        """
        self.message_items = {}  # msg_id -> {"item": QListWidgetItem, "widget": QTextBrowser, "role": str, "token_data": dict}
        self.message_order = []  # List of msg_ids in order
        self._agent_progress_id = None  # msg_id of the active agent progress widget
        self.welcome_widget = welcome_widget
        self.conversation_display = self._create_conversation_display()
        self.message_formatter = message_formatter
        self.logger = logger
        self.message_widget = MessageWidget(message_formatter, self.conversation_display)

    def _create_conversation_display(self) -> QListWidget:
        """
        Create and configure a QListWidget for conversation display.

        Returns:
            Configured QListWidget ready for conversation display
        """
        conversation_display = QListWidget()
        conversation_display.setFont(QFont("Consolas", 10))
        # Remove item selection highlight
        conversation_display.setSelectionMode(QListWidget.NoSelection)
        # Enable smooth scrolling
        conversation_display.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        # Remove spacing between items
        conversation_display.setSpacing(0)
        # Style the list widget
        conversation_display.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: none;
                padding: 0px;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
                margin: 0px;
                background: transparent;
            }
            QListWidget::item:hover {
                background: transparent;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)
        conversation_display.setContentsMargins(0, 0, 0, 0)
        return conversation_display

    def get_widget(self) -> QListWidget:
        """
        Get the conversation display widget.

        Returns:
            The QListWidget for conversation display
        """
        return self.conversation_display

    def append_message(self, role: str, message: str, token_data: dict = None) -> str:
        """
        Append a message to the conversation display with markdown support.

        Args:
            role: The role (You, AI, Error, etc.)
            message: The message content (supports markdown)
            token_data: Optional dict with token usage information

        Returns:
            Message ID that can be used for later updates
        """
        msg_id = str(uuid.uuid4())

        widget, item = self.message_widget.create(role, message, token_data)

        # Insert before agent progress widget if one is active, otherwise append
        if self._agent_progress_id and self._agent_progress_id in self.message_items:
            progress_data = self.message_items[self._agent_progress_id]
            row = self.conversation_display.row(progress_data["item"])
            self.conversation_display.insertItem(row, item)
            # Insert in message_order before the progress widget
            progress_index = self.message_order.index(self._agent_progress_id)
            self.message_order.insert(progress_index, msg_id)
        else:
            self.conversation_display.addItem(item)
            self.message_order.append(msg_id)

        self.conversation_display.setItemWidget(item, widget)

        # Store reference
        self.message_items[msg_id] = {
            "item": item,
            "widget": widget,
            "role": role,
            "token_data": token_data,
        }

        # Scroll to bottom
        self.conversation_display.scrollToBottom()

        return msg_id

    def remove_message(self, msg_id: str) -> bool:
        """
        Remove a specific message by ID.

        Args:
            msg_id: The message ID to remove

        Returns:
            True if message was removed, False if not found
        """
        if msg_id not in self.message_items:
            return False

        msg_data = self.message_items.pop(msg_id)
        self.message_order.remove(msg_id)

        # Remove from list widget
        row = self.conversation_display.row(msg_data["item"])
        self.conversation_display.takeItem(row)

        return True

    def display_error(self, error_message: str) -> str:
        """
        Display an error message.

        Args:
            error_message: The error message to display

        Returns:
            Message ID
        """
        return self.append_message("ERROR", error_message)

    def display_welcome(self) -> str:
        """
        Display welcome message in the conversation area.

        Returns:
            Message ID of the welcome message
        """
        msg_id = str(uuid.uuid4())

        widget, item = self.welcome_widget.create(self.conversation_display)

        self.conversation_display.addItem(item)
        self.conversation_display.setItemWidget(item, widget)

        self.message_items[msg_id] = {
            "item": item,
            "widget": widget,
            "role": "_welcome",
            "token_data": None,
        }
        self.message_order.append(msg_id)
        self.welcome_widget.msg_id = msg_id

        # Scroll to bottom
        self.conversation_display.scrollToBottom()

        return msg_id

    def create_agent_progress_widget(self) -> str:
        """Create an AgentProgressWidget and append it to the widget list.

        Returns:
            Message ID of the progress widget
        """
        msg_id = str(uuid.uuid4())

        progress = AgentProgressWidget(self.message_formatter, self.conversation_display)
        widget, item = progress.create()

        self.conversation_display.addItem(item)
        self.conversation_display.setItemWidget(item, widget)

        self.message_items[msg_id] = {
            "item": item,
            "widget": widget,
            "role": "_agent_progress",
            "token_data": None,
            "agent_progress": progress,
        }
        self.message_order.append(msg_id)
        self._agent_progress_id = msg_id

        self.conversation_display.scrollToBottom()

        return msg_id

    def agent_progress_done(self):
        """Remove the active agent progress widget from the conversation."""
        if not self._agent_progress_id or self._agent_progress_id not in self.message_items:
            self._agent_progress_id = None
            return

        self.remove_message(self._agent_progress_id)
        self._agent_progress_id = None

    def clear_conversation(self):
        """Clear the conversation display and redisplay welcome message."""
        # Clear all messages
        self.conversation_display.clear()
        self.message_items.clear()
        self.message_order.clear()
        self._agent_progress_id = None
        self.welcome_widget.msg_id = None

        # Redisplay the welcome message
        self.display_welcome()

        # Show confirmation message
        self.append_message("System", "Conversation history cleared.")
