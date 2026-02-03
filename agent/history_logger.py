"""
History logging for ForShape AI.

This module handles conversation history logging to daily log files.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional


class HistoryLogger:
    """Handles conversation history logging to files."""

    def __init__(self, history_dir: Path):
        """
        Initialize the history logger.

        Args:
            history_dir: Directory where history log files will be stored
        """
        self.history_dir = history_dir
        self.history_file: Optional[Path] = None
        self._initialize_history_log()

    def _initialize_history_log(self):
        """Initialize history log file based on current date."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.history_file = self.history_dir / f"{today}.log"

        # Create file if it doesn't exist
        if not self.history_file.exists():
            self.history_file.touch()

        # Write session start marker
        self._write_session_start()

    def _write_session_start(self):
        """Write session start marker to log file."""
        if self.history_file is None:
            return

        with open(self.history_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{'=' * 60}\n")
            f.write(f"Session started: {timestamp}\n")
            f.write(f"{'=' * 60}\n\n")

    def log_conversation(self, role: str, content: str):
        """
        Log a conversation message to the history file.

        Args:
            role: The role (user, assistant, system, error, etc.)
            content: The message content
        """
        if self.history_file is None:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {role.upper()}:\n")
            f.write(f"{content}\n\n")

    def write_session_end(self):
        """Write session end marker to log file."""
        if self.history_file is None:
            return

        with open(self.history_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{'=' * 60}\n")
            f.write(f"Session ended: {timestamp}\n")
            f.write(f"{'=' * 60}\n\n")

    def get_history_file(self) -> Optional[Path]:
        """
        Get the current history file path.

        Returns:
            Path to history file, or None if not initialized
        """
        return self.history_file
