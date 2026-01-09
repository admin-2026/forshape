"""
User Input Queue for handling user messages during AI agent processing.

This class encapsulates user input, allowing both initial messages and
follow-up messages to be queued and retrieved during AI agent iterations.
"""

from typing import Optional


class UserInputQueue:
    """
    A queue for managing user input messages during AI agent processing.

    This class holds the initial user message and allows additional messages
    to be queued while the AI agent is processing. The agent can check for
    and retrieve new messages during its iteration loop.
    """

    def __init__(self, initial_message: str):
        """
        Initialize the user input queue with an initial message.

        Args:
            initial_message: The initial user message that starts the conversation
        """
        self.initial_message = initial_message
        self.pending_messages = []  # Queue of additional messages added during processing

    def add_message(self, message: str):
        """
        Add a new message to the pending queue.

        This is called when the user types additional input while the AI is processing.

        Args:
            message: The new message to add to the queue
        """
        if message:  # Only add non-empty messages
            self.pending_messages.append(message)

    def get_initial_message(self) -> str:
        """
        Get the initial message that started this conversation.

        Returns:
            The initial user message
        """
        return self.initial_message

    def get_next_message(self) -> Optional[str]:
        """
        Get and remove the next pending message from the queue.

        This is called by the AI agent during iterations to check for new user input.

        Returns:
            The next pending message, or None if the queue is empty
        """
        if self.pending_messages:
            return self.pending_messages.pop(0)
        return None

    def has_pending_messages(self) -> bool:
        """
        Check if there are any pending messages in the queue.

        Returns:
            True if there are pending messages, False otherwise
        """
        return len(self.pending_messages) > 0

    def clear_pending_messages(self):
        """Clear all pending messages from the queue."""
        self.pending_messages.clear()
