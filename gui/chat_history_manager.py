"""
Chat History Manager for AI Agent

Simplified manager for conversation history with support for:
- Message storage and retrieval
- Context window management (max messages)
- API-ready message formatting
"""

from typing import List, Dict, Optional, Any
from datetime import datetime


class ChatHistoryManager:
    """Manages chat history for the AI agent."""

    def __init__(self, max_messages: Optional[int] = None):
        """
        Initialize the chat history manager.

        Args:
            max_messages: Maximum number of messages to keep (None for unlimited)
        """
        self._history: List[Dict[str, Any]] = []
        self.max_messages = max_messages

    def add_message(self, role: str, content: Any, metadata: Optional[Dict] = None) -> None:
        """
        Add a message to the history.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content (can be string or list for multi-modal content)
            metadata: Optional metadata (timestamp, tokens, etc.)
        """
        message = {
            "role": role,
            "content": content
        }

        # Add metadata if provided
        if metadata:
            message.update(metadata)

        # Add timestamp if not provided
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        self._history.append(message)

        # Apply message limit if set
        if self.max_messages is not None and len(self._history) > self.max_messages:
            self._history = self._history[-self.max_messages:]

    def add_user_message(self, content: Any, metadata: Optional[Dict] = None) -> None:
        """Add a user message to the history."""
        self.add_message("user", content, metadata)

    def add_assistant_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """Add an assistant message to the history."""
        self.add_message("assistant", content, metadata)

    def get_history(self, last_n: Optional[int] = None) -> List[Dict]:
        """
        Get the conversation history.

        Args:
            last_n: Return only the last N messages (None for all)

        Returns:
            List of message dictionaries compatible with OpenAI API
        """
        # Create clean message dicts for API (without internal metadata like timestamps)
        filtered = []
        for msg in self._history:
            api_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            filtered.append(api_msg)

        # Return last N messages if specified
        if last_n is not None:
            return filtered[-last_n:]

        return filtered

    def clear_history(self) -> None:
        """Clear all conversation history."""
        self._history = []

    def get_context_for_api(self, system_message: Optional[str] = None,
                           max_history_messages: Optional[int] = None) -> List[Dict]:
        """
        Get formatted message list for OpenAI API call.

        Args:
            system_message: Optional system message to prepend (not stored in history)
            max_history_messages: Maximum number of history messages to include

        Returns:
            List of messages formatted for OpenAI API
        """
        messages = []

        # Add system message if provided (NOT stored in history)
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add conversation history
        history = self.get_history(last_n=max_history_messages)
        messages.extend(history)

        return messages

    def __len__(self) -> int:
        """Return the number of messages in history."""
        return len(self._history)

    def __repr__(self) -> str:
        """String representation of the history manager."""
        return f"ChatHistoryManager(messages={len(self._history)}, max_messages={self.max_messages})"
