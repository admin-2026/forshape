"""
Message handling for ForShape AI GUI.

This module provides functionality for displaying messages, logs, and handling
message formatting in the conversation display.
"""

import uuid

from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QFont, QTextCursor
from PySide2.QtWidgets import QListWidget, QListWidgetItem, QTextBrowser


class MessageHandler:
    """Handles message display, formatting, and log management."""

    # Default stylesheet for message widgets
    DEFAULT_STYLESHEET = """
        p {
            margin: 0;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 3px;
            font-family: Consolas, monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        code {
            background-color: #f0f0f0;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: Consolas, monospace;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        div {
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        strong { font-weight: bold; }
        em { font-style: italic; }
    """

    def __init__(self, log_display, message_formatter, logger, welcome_widget):
        """
        Initialize the message handler.

        Args:
            log_display: QTextEdit widget for log display
            message_formatter: MessageFormatter instance
            logger: Logger instance
            welcome_widget: WelcomeWidget instance
        """
        self.message_items = {}  # msg_id -> {"item": QListWidgetItem, "widget": QTextBrowser, "role": str, "token_data": dict}
        self.message_order = []  # List of msg_ids in order
        self.welcome_widget = welcome_widget
        self.conversation_display = self._create_conversation_display()
        self.log_display = log_display
        self.message_formatter = message_formatter
        self.logger = logger

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

    def _create_message_widget(self, html_content: str) -> QTextBrowser:
        """
        Create a QTextBrowser widget for displaying a single message.

        Args:
            html_content: HTML content to display

        Returns:
            Configured QTextBrowser widget
        """
        widget = QTextBrowser()
        widget.setFont(QFont("Consolas", 10))
        widget.setReadOnly(True)
        widget.setOpenExternalLinks(True)
        widget.setFrameShape(QTextBrowser.NoFrame)
        # Disable scrollbars - the parent QListWidget handles scrolling
        widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Enable text selection
        widget.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )
        # Remove internal margins/padding
        widget.setContentsMargins(0, 0, 0, 0)
        widget.document().setDocumentMargin(0)
        # Set stylesheet for markdown rendering
        widget.document().setDefaultStyleSheet(self.DEFAULT_STYLESHEET)
        # Set the HTML content
        widget.setHtml(html_content)
        # Calculate appropriate height based on content
        viewport_width = self.conversation_display.viewport().width() - 20
        widget.document().setTextWidth(viewport_width)
        doc_height = int(widget.document().size().height()) + 5  # Add buffer for full visibility
        widget.setFixedHeight(doc_height)
        return widget

    def _update_widget_size(self, widget: QTextBrowser):
        """Update widget size based on current viewport width."""
        widget.document().setDocumentMargin(0)
        widget.document().setTextWidth(self.conversation_display.viewport().width() - 20)
        doc_height = int(widget.document().size().height()) + 5  # Add buffer for full visibility
        widget.setFixedHeight(doc_height)

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

        # Use MessageFormatter to format the message
        formatted_message = self.message_formatter.format_message(role, message, token_data)

        # Create widget and list item
        widget = self._create_message_widget(formatted_message)
        item = QListWidgetItem()
        item.setSizeHint(QSize(widget.width(), widget.height()))

        # Add to list widget
        self.conversation_display.addItem(item)
        self.conversation_display.setItemWidget(item, widget)

        # Store reference
        self.message_items[msg_id] = {
            "item": item,
            "widget": widget,
            "role": role,
            "token_data": token_data,
        }
        self.message_order.append(msg_id)

        # Scroll to bottom
        self.conversation_display.scrollToBottom()

        return msg_id

    def update_message(self, msg_id: str, new_content: str, role: str = None, token_data: dict = None):
        """
        Update an existing message's content.

        Args:
            msg_id: The message ID returned by append_message
            new_content: The new message content
            role: Optional new role (uses existing role if not provided)
            token_data: Optional new token data (uses existing if not provided)
        """
        if msg_id not in self.message_items:
            return

        msg_data = self.message_items[msg_id]
        widget = msg_data["widget"]
        item = msg_data["item"]

        # Use provided values or fall back to existing
        use_role = role if role is not None else msg_data["role"]
        use_token_data = token_data if token_data is not None else msg_data["token_data"]

        # Format and update content
        formatted_message = self.message_formatter.format_message(use_role, new_content, use_token_data)
        widget.setHtml(formatted_message)

        # Update size
        self._update_widget_size(widget)
        item.setSizeHint(QSize(widget.width(), widget.height()))

        # Update stored data
        msg_data["role"] = use_role
        msg_data["token_data"] = use_token_data

        # Scroll to bottom
        self.conversation_display.scrollToBottom()

    def remove_last_message(self) -> str | None:
        """
        Remove the last message from the conversation display.

        Returns:
            The ID of the removed message, or None if no messages exist
        """
        if not self.message_order:
            return None

        # Get the last message ID
        msg_id = self.message_order.pop()
        msg_data = self.message_items.pop(msg_id)

        # Remove from list widget
        row = self.conversation_display.row(msg_data["item"])
        self.conversation_display.takeItem(row)

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

    def on_log_message(self, level: str, message: str, timestamp: str):
        """
        Handle log messages from the logger.

        Args:
            level: Log level (DEBUG, INFO, WARN, ERROR)
            message: Log message
            timestamp: Timestamp of the log
        """
        # Color code based on log level
        color_map = {"DEBUG": "#888888", "INFO": "#0066CC", "WARN": "#FF8800", "ERROR": "#CC0000"}
        color = color_map.get(level, "#000000")

        # Format the log message with color
        formatted_log = f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span><br>'

        # Move cursor to end before inserting
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)

        # Insert HTML
        self.log_display.insertHtml(formatted_log)

        # Scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)

    def display_welcome(self) -> str:
        """
        Display welcome message in the conversation area.

        Returns:
            Message ID of the welcome message
        """
        welcome_html = self.welcome_widget.generate_html()

        # Create a special welcome message (not using append_message to avoid role formatting)
        msg_id = str(uuid.uuid4())
        widget = self._create_message_widget(welcome_html)
        item = QListWidgetItem()
        item.setSizeHint(QSize(widget.width(), widget.height()))

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

    def clear_conversation(self):
        """Clear the conversation display and redisplay welcome message."""
        # Clear all messages
        self.conversation_display.clear()
        self.message_items.clear()
        self.message_order.clear()
        self.welcome_widget.msg_id = None

        # Redisplay the welcome message
        self.display_welcome()

        # Show confirmation message
        self.append_message("System", "Conversation history cleared.")
