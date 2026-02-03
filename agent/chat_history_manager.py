"""
Chat History Manager for AI Agent

Simplified manager for conversation history with support for:
- Message storage and retrieval
- Context window management (max messages)
- API-ready message formatting
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional


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
        self.current_conversation_id: Optional[str] = None  # Track current conversation

    def add_message(self, role: str, content: Any, metadata: Optional[Dict] = None) -> None:
        """
        Add a message to the history.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content (can be string or list for multi-modal content)
            metadata: Optional metadata (timestamp, tokens, etc.)
        """
        message = {"role": role, "content": content}

        # Add metadata if provided
        if metadata:
            message.update(metadata)

        # Add timestamp if not provided
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        # Add conversation_id if available
        if self.current_conversation_id is not None:
            message["conversation_id"] = self.current_conversation_id

        self._history.append(message)

        # Apply message limit if set
        if self.max_messages is not None and len(self._history) > self.max_messages:
            self._history = self._history[-self.max_messages :]

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
            api_msg = {"role": msg["role"], "content": msg["content"]}
            filtered.append(api_msg)

        # Return last N messages if specified
        if last_n is not None:
            return filtered[-last_n:]

        return filtered

    def clear_history(self) -> None:
        """Clear all conversation history."""
        self._history = []

    def set_conversation_id(self, conversation_id: str) -> None:
        """
        Set the current conversation ID.

        All subsequent messages added will be tagged with this conversation ID.

        Args:
            conversation_id: Unique conversation ID
        """
        self.current_conversation_id = conversation_id

    def dump_history(self, output_dir: str, model_name: str = "Unknown") -> str:
        """
        Dump the conversation history to a timestamped file.

        Args:
            output_dir: Directory to save the history dump
            model_name: Name of the model being used

        Returns:
            Path to the dumped history file

        Raises:
            Exception: If history dump fails
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_filename = f"history_dump_{timestamp}.txt"
        dump_path = os.path.join(output_dir, dump_filename)

        # Write history to file
        with open(dump_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("ForShape AI - Conversation History Dump\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model: {model_name}\n")
            f.write(f"Total Messages: {len(self._history)}\n")
            f.write("=" * 80 + "\n\n")

            for i, message in enumerate(self._history, 1):
                role = message.get("role", "unknown")
                content = message.get("content", "")
                timestamp_str = message.get("timestamp", "N/A")
                conversation_id = message.get("conversation_id", "N/A")

                f.write(f"\n{'=' * 80}\n")
                f.write(f"Message #{i} - Role: {role.upper()}\n")
                f.write(f"Timestamp: {timestamp_str}\n")
                f.write(f"Conversation ID: {conversation_id}\n")
                f.write(f"{'=' * 80}\n")

                # Handle multi-modal content (lists) and plain text
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                f.write(f"{item.get('text', '')}\n")
                            elif item.get("type") == "image_url":
                                f.write(f"[IMAGE: {item.get('image_url', {}).get('url', 'N/A')[:100]}...]\n")
                            else:
                                f.write(f"[{item.get('type', 'unknown').upper()} CONTENT]\n")
                        else:
                            f.write(f"{item}\n")
                else:
                    f.write(f"{content}\n")

        return dump_path

    def __len__(self) -> int:
        """Return the number of messages in history."""
        return len(self._history)

    def __repr__(self) -> str:
        """String representation of the history manager."""
        return f"ChatHistoryManager(messages={len(self._history)}, max_messages={self.max_messages})"
