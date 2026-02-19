"""
Chat History Manager for AI Agent

Simplified manager for conversation history with support for:
- Message storage and retrieval
- Context window management (max messages)
- API-ready message formatting
- History policies (ONCE, LATEST, DEFAULT, DISCARD)
"""

import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional


class HistoryPolicy(Enum):
    """Policy for handling messages with duplicate keys."""

    DEFAULT = auto()  # No special handling, all messages are kept
    ONCE = auto()  # Keep only the first message with a given key, ignore duplicates
    LATEST = auto()  # Keep only the latest message with a given key
    DISCARD = auto()  # Never save this message to history


@dataclass
class HistoryMessage:
    """
    A message to be saved to chat history.

    This represents a message that should be added to the conversation history
    after a step completes.
    """

    role: str  # "user" or "assistant"
    content: Any  # Can be string or list for multi-modal content
    key: str  # Unique key for deduplication
    policy: HistoryPolicy = HistoryPolicy.DEFAULT
    timestamp: Optional[str] = None
    conversation_id: Optional[str] = None
    step: Optional[str] = None


class ChatHistoryManager:
    """Manages chat history for the AI agent."""

    def __init__(self, max_messages: Optional[int] = None):
        """
        Initialize the chat history manager.

        Args:
            max_messages: Maximum number of messages to keep (None for unlimited)
        """
        self._history: list[HistoryMessage] = []
        self.max_messages = max_messages
        self.current_conversation_id: Optional[str] = None  # Track current conversation

    def add_message(
        self,
        role: str,
        content: Any,
        key: str,
        policy: HistoryPolicy = HistoryPolicy.DEFAULT,
        step: Optional[str] = None,
    ) -> None:
        """
        Add a message to the history.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content (can be string or list for multi-modal content)
            key: Unique key for the message (used for policy-based deduplication)
            policy: History policy for handling duplicate keys
            step: Optional step name this message belongs to
        """
        # Apply policy-based handling
        if policy == HistoryPolicy.DISCARD:
            # Never save this message
            return
        if policy == HistoryPolicy.ONCE:
            # If a message with the same key already exists, don't add
            if any(msg.key == key for msg in self._history):
                return
        elif policy == HistoryPolicy.LATEST:
            # Remove any existing messages with the same key
            self._history = [msg for msg in self._history if msg.key != key]

        message = HistoryMessage(
            role=role,
            content=content,
            key=key,
            policy=policy,
            timestamp=datetime.now().isoformat(),
            conversation_id=self.current_conversation_id,
            step=step,
        )

        self._history.append(message)

        # Apply message limit if set
        if self.max_messages is not None and len(self._history) > self.max_messages:
            self._history = self._history[-self.max_messages :]

    def add_user_message(
        self,
        content: Any,
        key: str,
        policy: HistoryPolicy = HistoryPolicy.DEFAULT,
    ) -> None:
        """Add a user message to the history."""
        self.add_message("user", content, key, policy)

    def add_history_messages(self, messages: list["HistoryMessage"], step_name: Optional[str] = None) -> None:
        """
        Add multiple HistoryMessage objects to the history.

        Args:
            messages: List of HistoryMessage objects to add
            step_name: Optional step name to save with each message's metadata
        """
        for msg in messages:
            self.add_message(msg.role, msg.content, msg.key, msg.policy, step=step_name)

    def get_history(self, last_n: Optional[int] = None) -> list[dict]:
        """
        Get the conversation history.

        Args:
            last_n: Return only the last N messages (None for all)

        Returns:
            List of message dictionaries compatible with OpenAI API
            (keys are removed from messages)
        """
        # Create clean message dicts for API (without internal fields like timestamps and keys)
        filtered = [{"role": msg.role, "content": msg.content} for msg in self._history]

        # Return last N messages if specified
        if last_n is not None:
            return filtered[-last_n:]

        return filtered

    def drop_history_by_step(self, step_name: str) -> int:
        """
        Remove all messages belonging to a given step.

        Args:
            step_name: The step name whose messages to remove

        Returns:
            Number of messages removed
        """
        original_count = len(self._history)
        self._history = [msg for msg in self._history if msg.step != step_name]
        return original_count - len(self._history)

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
                role = message.role
                content = message.content
                timestamp_str = message.timestamp or "N/A"
                conversation_id = message.conversation_id or "N/A"

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
