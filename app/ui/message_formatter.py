"""
Message formatting utilities for converting markdown to HTML.
"""

import html as html_module


class MessageFormatter:
    """Utility class for formatting messages with markdown support."""

    def __init__(self, logger):
        """
        Initialize the message formatter.

        Args:
            logger: Logger instance for debugging
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
                "markdown.extensions.fenced_code",  # Code blocks with ```
                "markdown.extensions.tables",  # Tables
                "markdown.extensions.nl2br",  # Newline to <br>
                "markdown.extensions.codehilite",  # Syntax highlighting
            ]

            try:
                html_output = md.markdown(text, extensions=extensions)
                # Debug: Log that markdown conversion succeeded
                self.logger.debug(f"Markdown converted to HTML: {html_output[:100]}...")
                return html_output
            except Exception as e:
                # Fallback if conversion fails
                self.logger.warn(f"Markdown conversion failed: {e}, using fallback")
                return self._fallback_format(text)

        except ImportError:
            # Fallback: basic HTML escaping and line break conversion if markdown not available
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
        text = text.replace("\n", "<br>")
        return text

    @staticmethod
    def format_token_data(token_data: dict, include_iteration: bool = False) -> str:
        """
        Format token usage data into a readable string.

        Args:
            token_data: Dict with token usage information (prompt_tokens, completion_tokens, total_tokens, iteration)
            include_iteration: Whether to include iteration number in the output

        Returns:
            Formatted token usage string
        """
        if not token_data:
            return ""

        prompt_tokens = token_data.get("prompt_tokens", 0)
        completion_tokens = token_data.get("completion_tokens", 0)
        total_tokens = token_data.get("total_tokens", 0)

        # Base format
        token_str = f"Request: {prompt_tokens:,} | Response: {completion_tokens:,} | Total: {total_tokens:,}"

        # Add iteration if requested
        if include_iteration and "iteration" in token_data:
            iteration = token_data.get("iteration", "?")
            token_str = f"Iteration {iteration}: {token_str}"

        return token_str

    def format_message(self, role: str, message: str, token_data: dict = None) -> str:
        """
        Format a message for display with appropriate styling.

        Args:
            role: The role (You, AI, Error, etc.)
            message: The message content (supports markdown for AI messages)
            token_data: Optional dict with token usage information

        Returns:
            Formatted HTML string
        """
        # Use different colors for different roles
        if role == "AI":
            role_color = "#0066CC"  # Blue for AI messages
        elif role == "You":
            role_color = "#009900"  # Green for user messages
        else:
            role_color = "#333"  # Default gray for system messages

        # Convert markdown to HTML for AI and System messages
        if role == "AI" or role == "System":
            message_html = self.markdown_to_html(message)

            # Add token information if available (only for AI messages)
            token_info_html = ""
            if role == "AI" and token_data:
                token_str = self.format_token_data(token_data, include_iteration=False)
                token_info_html = f'<div style="font-size: 11px; color: #888;">Tokens: {token_str}</div>'

            formatted_message = (
                f'<div style="margin: 0;">'
                f'<strong style="color: {role_color};">{role}:</strong><br>{message_html}'
                f"{token_info_html}</div>"
            )
        else:
            # For user messages, use simpler formatting (no markdown)
            escaped_message = html_module.escape(message).replace("\n", "<br>")

            formatted_message = (
                f'<div style="margin: 0;">'
                f'<strong style="color: {role_color};">{role}:</strong><br>{escaped_message}</div>'
            )

        return formatted_message
