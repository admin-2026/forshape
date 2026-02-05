"""
Message formatting utilities for converting markdown to HTML.
"""

import html as html_module


class MessageFormatter:
    """Utility class for formatting messages with markdown support."""

    # Background colors for different roles
    BG_COLOR_AI = "#E8F4FF"  # Light blue for AI messages
    BG_COLOR_USER = "#E8FFE8"  # Light green for user messages
    BG_COLOR_SYSTEM = "#FFF8E8"  # Light yellow for system messages
    BG_COLOR_ERROR = "#FFE8E8"  # Light red for error messages

    # Text colors for role labels
    TEXT_COLOR_AI = "#0066CC"  # Blue for AI
    TEXT_COLOR_USER = "#009900"  # Green for user
    TEXT_COLOR_SYSTEM = "#996600"  # Brown for system
    TEXT_COLOR_ERROR = "#CC0000"  # Red for error

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

        # Select colors based on role
        if role == "AI":
            bg_color = self.BG_COLOR_AI
            text_color = self.TEXT_COLOR_AI
        elif role == "You":
            bg_color = self.BG_COLOR_USER
            text_color = self.TEXT_COLOR_USER
        elif role == "Error":
            bg_color = self.BG_COLOR_ERROR
            text_color = self.TEXT_COLOR_ERROR
        else:  # System or other
            bg_color = self.BG_COLOR_SYSTEM
            text_color = self.TEXT_COLOR_SYSTEM

        # Common div style with background color
        div_style = f"margin: 5px 0; padding: 10px; border-radius: 5px; background-color: {bg_color};"

        # Convert markdown to HTML for AI and System messages
        if role == "AI" or role == "System":
            message_html = self.markdown_to_html(message)

            # Add token information if available (only for AI messages)
            token_info_html = ""
            if role == "AI" and token_data:
                token_str = self.format_token_data(token_data, include_iteration=False)
                token_info_html = f'<div style="font-size: 11px; color: #888;">Tokens: {token_str}</div>'

            formatted_message = (
                f'<div style="{div_style}">'
                f'<strong style="color: {text_color};">{role}:</strong>{message_html}'
                f"{token_info_html}</div>"
            )
        else:
            # For user messages, wrap in <p> for consistent formatting (no markdown)
            escaped_message = html_module.escape(message).replace("\n", "<br>")

            formatted_message = (
                f'<div style="{div_style}">'
                f'<strong style="color: {text_color};">{role}:</strong><p>{escaped_message}</p></div>'
            )

        return formatted_message
