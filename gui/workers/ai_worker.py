"""
Worker thread for handling AI API calls asynchronously.
"""

from PySide2.QtCore import QThread, Signal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.ai_agent import AIAgent
    from agent.user_input_queue import UserInputQueue


class AIWorker(QThread):
    """Worker thread for handling AI API calls asynchronously."""

    # Signal emitted when AI processing is complete (response, is_error, token_data)
    finished = Signal(str, bool, object)  # (message, is_error, token_data)

    # Signal emitted during processing to update token usage
    token_update = Signal(object)  # (token_data)

    def __init__(self, ai_client: 'AIAgent', input_queue: 'UserInputQueue', image_data=None):
        """
        Initialize the AI worker thread.

        Args:
            ai_client: The AIAgent instance
            input_queue: UserInputQueue containing the initial message and any follow-up messages
            image_data: Optional captured image data to attach
        """
        super().__init__()
        self.ai_client = ai_client
        self.input_queue = input_queue
        self.image_data = image_data
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

            # Process request with input queue
            response = self.ai_client.process_request(self.input_queue, self.image_data, token_callback)

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
