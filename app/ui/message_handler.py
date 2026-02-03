"""
Message handling for ForShape AI GUI.

This module provides functionality for displaying messages, logs, and handling
message formatting in the conversation display.
"""

from PySide2.QtGui import QTextCursor


class MessageHandler:
    """Handles message display, formatting, and log management."""

    def __init__(self, conversation_display, log_display, message_formatter, logger):
        """
        Initialize the message handler.

        Args:
            conversation_display: QTextEdit widget for conversation display
            log_display: QTextEdit widget for log display
            message_formatter: MessageFormatter instance
            logger: Logger instance
        """
        self.conversation_display = conversation_display
        self.log_display = log_display
        self.message_formatter = message_formatter
        self.logger = logger

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
        document = self.conversation_display.document()

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

    def play_notification_sound(self):
        """Play a notification sound when AI finishes processing."""
        try:
            # Play system beep sound
            # On Windows, this will play the system default beep
            # On other platforms, it will attempt to play a system sound
            import platform

            if platform.system() == "Windows":
                # Use winsound for a simple beep on Windows
                import winsound

                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:
                # On other platforms, try to use system bell
                print("\a")  # ASCII bell character
        except Exception as e:
            # If sound fails, just log it and continue
            self.logger.debug(f"Could not play notification sound: {e}")
