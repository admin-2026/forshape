"""
Edit History Manager for AI Agent.

This module provides an edit history system that backs up files before editing
them, organized by conversation ID and timestamp.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from .logger import Logger


class EditHistory:
    """
    Manages edit history for files, allowing rollback of changes per conversation.

    The edit history is stored in .forshap/edits/{conversation_id}_{timestamp}/
    and mirrors the structure of the working directory.

    Conversation IDs are provided by the AIAgent. EditHistory only receives
    and uses these IDs for organizing backups - it does not generate them.
    """

    METADATA_FILENAME = "_session_metadata.json"

    def __init__(self, working_dir: str, edits_dir: str, logger: Logger):
        """
        Initialize the edit history manager.

        Args:
            working_dir: Working directory for file operations
            edits_dir: Directory where edit history should be stored
            logger: Logger instance for logging operations
        """
        self.working_dir = Path(working_dir)
        self.history_base = Path(edits_dir)
        self.logger = logger
        self.conversation_id: Optional[str] = None
        self.session_folder: Optional[Path] = None
        self.file_operations: List[Dict] = []  # Track file operations in current session

    def start_new_conversation(self, conversation_id: str) -> None:
        """
        Start a new conversation with the provided ID.

        This should be called by the AIAgent at the beginning of each user request
        to create a new conversation session with its own backup folder.

        Args:
            conversation_id: Unique conversation ID provided by AIAgent
        """
        self.conversation_id = conversation_id
        self.session_folder = None  # Reset session folder for new conversation
        self.file_operations = []  # Reset file operations for new conversation

    def _get_or_create_session_folder(self) -> Path:
        """
        Get or create the session folder for the current conversation.

        Creates a folder with the format: {conversation_id}_{timestamp}

        Returns:
            Path to the session folder
        """
        if self.session_folder is None:
            # Ensure we have a conversation ID (fallback to default if not set by AIAgent)
            if self.conversation_id is None:
                self.conversation_id = "default"

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:17]  # Include milliseconds
            folder_name = f"{self.conversation_id}_{timestamp}"
            self.session_folder = self.history_base / folder_name
            self.session_folder.mkdir(parents=True, exist_ok=True)

        return self.session_folder

    def backup_file(self, file_path: Path) -> bool:
        """
        Backup a file before editing it.

        Args:
            file_path: Path to the file to backup (can be absolute or relative)

        Returns:
            True if backup was successful, False otherwise
        """
        try:
            # Resolve the file path
            if not file_path.is_absolute():
                file_path = (self.working_dir / file_path).resolve()
            else:
                file_path = file_path.resolve()

            # Only backup if the file exists
            if not file_path.exists():
                return False

            # Get session folder
            session_folder = self._get_or_create_session_folder()

            # Compute relative path from working directory
            try:
                relative_path = file_path.relative_to(self.working_dir)
            except ValueError:
                # File is outside working directory, use absolute path structure
                # Remove drive letter on Windows and leading slash on Unix
                if file_path.drive:
                    relative_path = Path(str(file_path)[len(file_path.drive)+1:])
                else:
                    relative_path = Path(str(file_path).lstrip('/'))

            # Create backup path
            backup_path = session_folder / relative_path

            # Create parent directories
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(file_path, backup_path)

            # Track this operation in metadata
            self.file_operations.append({
                "action": "edit",
                "file": relative_path,
                "absolute_path": str(file_path),
                "backup_path": str(backup_path.relative_to(session_folder))
            })
            self._save_metadata()

            return True

        except Exception as e:
            # Log failure - edit history is best-effort
            import traceback
            self.logger.error(f"Failed to backup {file_path}: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def track_file_creation(self, file_path: Path) -> bool:
        """
        Track that a new file was created (for deletion during rewind).

        Args:
            file_path: Path to the newly created file

        Returns:
            True if tracking was successful, False otherwise
        """
        try:
            # Resolve the file path
            if not file_path.is_absolute():
                file_path = (self.working_dir / file_path).resolve()
            else:
                file_path = file_path.resolve()

            # Get session folder (creates it if needed)
            session_folder = self._get_or_create_session_folder()

            # Compute relative path from working directory
            try:
                relative_path = str(file_path.relative_to(self.working_dir))
            except ValueError:
                # File is outside working directory, use absolute path structure
                if file_path.drive:
                    relative_path = str(file_path)[len(file_path.drive)+1:]
                else:
                    relative_path = str(file_path).lstrip('/')

            # Track this operation
            self.file_operations.append({
                "action": "create",
                "file": relative_path,
                "absolute_path": str(file_path)
            })

            # Save metadata
            self._save_metadata()

            return True

        except Exception as e:
            import traceback
            self.logger.error(f"Failed to track file creation {file_path}: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _save_metadata(self) -> None:
        """Save the session metadata to disk."""
        if self.session_folder is None:
            return

        metadata_path = self.session_folder / self.METADATA_FILENAME
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "conversation_id": self.conversation_id,
                    "file_operations": self.file_operations
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {str(e)}")

    @staticmethod
    def _load_metadata(session_folder: Path, logger: Optional[Logger] = None) -> Dict:
        """
        Load session metadata from disk.

        Args:
            session_folder: Path to the session folder
            logger: Optional logger for error reporting

        Returns:
            Dictionary with metadata, or empty dict if not found
        """
        metadata_path = session_folder / EditHistory.METADATA_FILENAME
        if not metadata_path.exists():
            return {"file_operations": []}

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            if logger:
                logger.error(f"Failed to load metadata: {str(e)}")
            return {"file_operations": []}

    def get_session_folder_path(self) -> Optional[str]:
        """
        Get the path to the current session folder.

        Returns:
            String path to session folder, or None if no session created yet
        """
        return str(self.session_folder) if self.session_folder else None

    @staticmethod
    def list_all_sessions(edits_dir: str) -> list:
        """
        List all edit history sessions.

        Args:
            edits_dir: Directory where edit history is stored

        Returns:
            List of session folder names sorted by timestamp (newest first)
        """
        history_base = Path(edits_dir)

        if not history_base.exists():
            return []

        sessions = [
            folder.name
            for folder in history_base.iterdir()
            if folder.is_dir()
        ]

        # Sort by name (which includes timestamp) in reverse order
        sessions.sort(reverse=True)

        return sessions

    @staticmethod
    def get_session_info(edits_dir: str, session_name: str) -> dict:
        """
        Get information about a specific session.

        Args:
            edits_dir: Directory where edit history is stored
            session_name: Name of the session folder

        Returns:
            Dictionary with session information
        """
        history_base = Path(edits_dir)
        session_path = history_base / session_name

        if not session_path.exists():
            return {"error": "Session not found"}

        # Parse conversation ID and timestamp from folder name
        parts = session_name.split('_')
        if len(parts) >= 3:
            conversation_id = parts[0]
            timestamp = '_'.join(parts[1:])
        else:
            conversation_id = session_name
            timestamp = "unknown"

        # Count backed up files
        file_count = sum(1 for _ in session_path.rglob('*') if _.is_file())

        return {
            "session_name": session_name,
            "conversation_id": conversation_id,
            "timestamp": timestamp,
            "path": str(session_path),
            "file_count": file_count
        }

    @staticmethod
    def restore_from_session(edits_dir: str, session_name: str, working_dir: str, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Restore files from a specific checkpoint session.
        - Restores backed up files (edited files)
        - Deletes files that were created (didn't exist before)

        Args:
            edits_dir: Directory where edit history is stored
            session_name: Name of the session folder to restore from
            working_dir: Working directory to restore files to
            logger: Optional logger for operation reporting

        Returns:
            Tuple of (success: bool, message: str)
        """
        history_base = Path(edits_dir)
        session_path = history_base / session_name
        working_dir_path = Path(working_dir)

        if not session_path.exists():
            return False, f"Session not found: {session_name}"

        try:
            # Load metadata to understand what operations were performed
            metadata = EditHistory._load_metadata(session_path, logger)
            file_operations = metadata.get("file_operations", [])

            if not file_operations:
                return False, "No file operations found in checkpoint metadata"

            restored_count = 0
            deleted_count = 0
            errors = []

            # Process file operations in reverse order (to undo them)
            for operation in reversed(file_operations):
                try:
                    action = operation.get("action")
                    file_path = operation.get("file")
                    target_path = working_dir_path / file_path

                    if action == "edit":
                        # Restore the backed up file
                        backup_rel_path = operation.get("backup_path")
                        if backup_rel_path:
                            backup_file = session_path / backup_rel_path
                            if backup_file.exists():
                                # Create parent directories if needed
                                target_path.parent.mkdir(parents=True, exist_ok=True)
                                # Copy the backup over the current file
                                shutil.copy2(backup_file, target_path)
                                restored_count += 1
                            else:
                                errors.append(f"Backup not found for {file_path}")
                        else:
                            errors.append(f"No backup path in metadata for {file_path}")

                    elif action == "create":
                        # Delete the file that was created
                        if target_path.exists():
                            target_path.unlink()
                            deleted_count += 1
                            print(f"[EditHistory] Deleted created file: {file_path}")
                        else:
                            print(f"[EditHistory] File already deleted: {file_path}")

                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")

            # Build result message
            message_parts = []
            if restored_count > 0:
                message_parts.append(f"Restored {restored_count} file(s)")
            if deleted_count > 0:
                message_parts.append(f"Deleted {deleted_count} created file(s)")

            if errors:
                error_msg = "\n".join(errors)
                summary = ", ".join(message_parts) if message_parts else "No operations"
                return False, f"{summary} with errors:\n{error_msg}"
            else:
                summary = ", ".join(message_parts) if message_parts else "No operations performed"
                return True, f"Successfully completed: {summary}"

        except Exception as e:
            return False, f"Error restoring from checkpoint: {str(e)}"
