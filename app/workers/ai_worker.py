"""
Worker thread for handling AI API calls asynchronously.
"""

from typing import TYPE_CHECKING

from PySide2.QtCore import QThread, Signal

if TYPE_CHECKING:
    from agent.ai_agent import AIAgent

from agent.step_config import StepConfigRegistry


class AIWorker(QThread):
    """Worker thread for handling AI API calls asynchronously."""

    # Signal emitted when AI processing is complete (response, is_error, token_data)
    finished = Signal(str, bool, object)  # (message, is_error, token_data)

    # Signal emitted during processing to update token usage
    token_update = Signal(object)  # (token_data)

    # Signal emitted when a step response is available (step_name, response)
    step_response = Signal(str, str)

    def __init__(
        self,
        ai_client: "AIAgent",
        user_input: str,
        step_configs: StepConfigRegistry,
    ):
        """
        Initialize the AI worker thread.

        Args:
            ai_client: The AIAgent instance
            user_input: The user's input message
            step_configs: Registry with step-specific configurations
        """
        super().__init__()
        self.ai_client = ai_client
        self.user_input = user_input
        self.step_configs = step_configs
        self._is_cancelled = False

    def cancel(self):
        """Request cancellation of the AI processing."""
        self._is_cancelled = True
        self.ai_client.request_cancellation()

    def is_cancelled(self):
        """Check if cancellation has been requested."""
        return self._is_cancelled

    def run(self):
        """Run the AI request in a separate thread."""
        try:
            # Create a callback to emit token updates during processing
            def token_callback(token_data):
                self.token_update.emit(token_data)

            # Create a callback to emit step responses during processing
            def step_response_callback(step_name, response):
                self.step_response.emit(step_name, response)

            # Process request with user input and step configs
            response = self.ai_client.process_request(
                self.user_input,
                self.step_configs,
                token_callback,
                step_response_callback,
            )

            # Check if cancelled
            if self._is_cancelled:
                self.finished.emit("Operation cancelled by user.", True, None)
                return

            # Get token usage data from the AI agent
            token_data = self.ai_client.get_last_token_usage()
            self.finished.emit(response, False, token_data)  # False = not an error
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.finished.emit(error_msg, True, None)  # True = is an error, None = no token data
