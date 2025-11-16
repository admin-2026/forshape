"""
Message formatting utilities for converting markdown to HTML.
"""

import html as html_module


class MessageFormatter:
    """Utility class for formatting messages with markdown support."""

    def __init__(self, logger=None):
        """
        Initialize the message formatter.

        Args:
            logger: Optional logger instance for debugging
        """
        self.logger = logger

    def markdown_to_html(self, text: str) -> str:
        """
        Convert markdown text to HTML.

        Args:
            text: Markdown text to convert

        Returns:
            HTML string
        """
        # Try to import markdown library (lazy import to allow dependency manager to install it first)
        try:
            import markdown as md

            # Configure markdown extensions for better rendering
            extensions = [
                'markdown.extensions.fenced_code',  # Code blocks with ```
                'markdown.extensions.tables',        # Tables
                'markdown.extensions.nl2br',         # Newline to <br>
                'markdown.extensions.codehilite',    # Syntax highlighting
            ]

            try:
                html_output = md.markdown(text, extensions=extensions)
                # Debug: Log that markdown conversion succeeded
                if self.logger:
                    self.logger.debug(f"Markdown converted to HTML: {html_output[:100]}...")
                return html_output
            except Exception as e:
                # Fallback if conversion fails
                if self.logger:
                    self.logger.warn(f"Markdown conversion failed: {e}, using fallback")
                return self._fallback_format(text)

        except ImportError:
            # Fallback: basic HTML escaping and line break conversion if markdown not available
            if self.logger:
                self.logger.warn("Markdown library not available, using fallback rendering")
            return self._fallback_format(text)

    def _fallback_format(self, text: str) -> str:
        """
        Fallback formatting when markdown library is not available.

        Args:
            text: Text to format

        Returns:
            Escaped HTML string
        """
        text = html_module.escape(text)
        text = text.replace('\n', '<br>')
        return text

    def format_message(self, role: str, message: str) -> str:
        """
        Format a message for display with appropriate styling.

        Args:
            role: The role (You, AI, Error, etc.)
            message: The message content (supports markdown for AI messages)

        Returns:
            Formatted HTML string
        """
        # Convert markdown to HTML for AI messages
        if role == "AI":
            message_html = self.markdown_to_html(message)
            formatted_message = (
                f'<div style="margin: 15px 0; padding: 8px; background-color: #f9f9f9; '
                f'border-left: 3px solid #0066CC;">'
                f'<strong style="color: #0066CC;">{role}:</strong><br>{message_html}</div>'
            )
        else:
            # For user messages and system messages, use simpler formatting
            escaped_message = html_module.escape(message).replace('\n', '<br>')
            formatted_message = (
                f'<div style="margin: 15px 0; padding: 8px;">'
                f'<strong style="color: #333;">{role}:</strong><br>{escaped_message}</div>'
            )

        return formatted_message
