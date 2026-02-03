"""
Message handling for ForShape AI GUI.

This module provides functionality for displaying messages, logs, and handling
message formatting in the conversation display.
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QFont, QTextCursor
from PySide2.QtWidgets import QTextEdit


class MessageHandler:
    """Handles message display, formatting, and log management."""

    def __init__(self, log_display, message_formatter, logger):
        """
        Initialize the message handler.

        Args:
            log_display: QTextEdit widget for log display
            message_formatter: MessageFormatter instance
            logger: Logger instance
        """
        self.conversation_display = self._create_conversation_display()
        self.log_display = log_display
        self.message_formatter = message_formatter
        self.logger = logger

    def _create_conversation_display(self) -> QTextEdit:
        """
        Create and configure a QTextEdit widget for conversation display.

        Returns:
            Configured QTextEdit widget ready for conversation display
        """
        conversation_display = QTextEdit()
        conversation_display.setReadOnly(True)
        conversation_display.setFont(QFont("Consolas", 10))
        # Enable rich text (HTML) rendering for markdown support
        conversation_display.setAcceptRichText(True)
        # Enable word wrapping at widget width
        conversation_display.setLineWrapMode(QTextEdit.WidgetWidth)
        # Enable text selection and copying
        conversation_display.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )

        # Set default stylesheet for better markdown rendering
        conversation_display.document().setDefaultStyleSheet("""
            p {
                margin: 0 0 5px 0;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }
            p:first-of-type {
                margin-top: 0;
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
        """)

        return conversation_display

    def get_widget(self) -> QTextEdit:
        """
        Get the conversation display widget.

        Returns:
            The QTextEdit widget for conversation display
        """
        return self.conversation_display

    def markdown_to_html(self, text: str) -> str:
        """
        Convert markdown text to HTML using MessageFormatter.

        Args:
            text: Markdown text to convert

        Returns:
            HTML string
        """
        return self.message_formatter.markdown_to_html(text)

    def append_message(self, role: str, message: str, token_data: dict = None):
        """
        Append a message to the conversation display with markdown support.

        Args:
            role: The role (You, AI, Error, etc.)
            message: The message content (supports markdown)
            token_data: Optional dict with token usage information
        """
        # Move cursor to end before inserting
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conversation_display.setTextCursor(cursor)

        # Use MessageFormatter to format the message
        formatted_message = self.message_formatter.format_message(role, message, token_data)

        # Use insertHtml instead of append for proper HTML rendering
        self.conversation_display.insertHtml(formatted_message)

        # Add a line break after each message to separate consecutive messages
        self.conversation_display.insertHtml("<br>")

        # Scroll to bottom
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conversation_display.setTextCursor(cursor)

    def remove_last_message(self):
        """Remove the last message from the conversation display."""
        # Get the document
        self.conversation_display.document()

        # Start from the end and work backwards to find and remove the last div block
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Move to the start of the document and select all
        cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)

        # Get HTML content
        html_content = cursor.selection().toHtml()

        # Find and remove the last message div (work from the end)
        # Look for the last occurrence of a div with our message styling
        last_div_start = html_content.rfind('<div style="margin: 15px 0; padding: 8px')

        if last_div_start != -1:
            # Find the closing </div> after this opening tag
            search_from = last_div_start + 10
            div_end = html_content.find("</div>", search_from)

            if div_end != -1:
                # Also remove the <br> that follows
                br_end = html_content.find("<br>", div_end)
                if br_end != -1 and br_end - div_end < 20:  # Make sure it's the immediate <br>
                    end_pos = br_end + 4  # Include the <br>
                else:
                    end_pos = div_end + 6  # Just </div>

                # Remove the last message div and br
                html_content = html_content[:last_div_start] + html_content[end_pos:]

                # Set the modified HTML back
                cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
                cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                cursor.insertHtml(html_content)

        # Scroll to bottom
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conversation_display.setTextCursor(cursor)

    def display_error(self, error_message: str):
        """
        Display an error message.

        Args:
            error_message: The error message to display
        """
        self.append_message("[ERROR]", error_message)

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

    def display_welcome(self, ai_client_ready: bool, has_forshape: bool, model_name: str = None):
        """
        Display welcome message in the conversation area.

        Args:
            ai_client_ready: True if AI client is initialized
            has_forshape: True if FORSHAPE.md is loaded
            model_name: The model name (required if ai_client_ready is True)
        """
        # Check if AI client is initialized
        if ai_client_ready:
            context_status = "✓ FORSHAPE.md loaded" if has_forshape else "✗ No FORSHAPE.md"
            model_info = f"<strong>Using model:</strong> {model_name}<br>"
            context_info = f"<strong>Context:</strong> {context_status}"
            start_message = "Start chatting to generate 3D shapes!"
        else:
            # During prestart checks
            model_info = ""
            context_info = "<strong>Status:</strong> Setting up..."
            start_message = "Please complete the setup steps below to begin."

        welcome_html = f"""
<div style="font-family: Consolas, monospace; margin: 10px 0;">
<pre style="margin: 0;">{"=" * 60}
Welcome to ForShape AI - Interactive 3D Shape Generator
{"=" * 60}</pre>
<p style="margin: 5px 0;">{model_info}{context_info}</p>

<p style="margin: 5px 0;"><strong>Tip:</strong> Drag & drop images or .py files to attach them to your messages</p>

<p style="margin: 5px 0;">{start_message}</p>
<pre style="margin: 0;">{"=" * 60}</pre>
</div>
"""
        self.conversation_display.insertHtml(welcome_html)
        # Add line breaks after welcome message to separate from first user message
        self.conversation_display.insertHtml("<br><br>")

    def clear_conversation(self, ai_client_ready: bool, has_forshape: bool, model_name: str = None):
        """
        Clear the conversation display and redisplay welcome message.

        Args:
            ai_client_ready: True if AI client is initialized
            has_forshape: True if FORSHAPE.md is loaded
            model_name: The model name (required if ai_client_ready is True)
        """
        # Clear the conversation display
        self.conversation_display.clear()

        # Redisplay the welcome message
        self.display_welcome(ai_client_ready, has_forshape, model_name)

        # Show confirmation message
        self.append_message("System", "Conversation history cleared.")
