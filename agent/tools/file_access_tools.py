"""
File access tools for AI Agent.

This module provides file system operations including listing files,
reading files, editing files, and searching Python files.
"""

import json
import re
from typing import Dict, List, Callable, Optional
from pathlib import Path

from .base import ToolBase
from ..logger_protocol import LoggerProtocol
from ..permission_manager import PermissionManager, PermissionResponse
from ..edit_history import EditHistory


# Large file read protection threshold (in bytes)
LARGE_FILE_SIZE_THRESHOLD = 50000  # 50KB


class FileAccessTools(ToolBase):
    """
    File system tools - always available as part of the agent core.

    Provides: list_files, read_file, edit_file, search_python_files
    """

    def __init__(
        self,
        working_dir: str,
        logger: LoggerProtocol,
        permission_manager: Optional[PermissionManager] = None,
        edit_history: Optional[EditHistory] = None,
        config_manager=None
    ):
        """
        Initialize file access tools.

        Args:
            working_dir: Working directory for file operations
            logger: LoggerProtocol instance for logging
            permission_manager: Optional permission manager for access control
            edit_history: Optional EditHistory instance for tracking file edits
            config_manager: Optional ConfigurationManager for configuration
        """
        self.working_dir = working_dir
        self.logger = logger
        self.permission_manager = permission_manager
        self.edit_history = edit_history
        self.config_manager = config_manager

    def get_definitions(self) -> List[Dict]:
        """Get tool definitions in OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List files and directories in a given folder path. Returns a list of file and directory names.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "folder_path": {
                                "type": "string",
                                "description": "The path to the folder to list files from. Can be relative to the working directory or absolute."
                            }
                        },
                        "required": ["folder_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file at the given path. Returns the file contents as a string.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path to the file to read. Can be relative to the working directory or absolute."
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edit a file by replacing old content with new content. If the file doesn't exist, it will be created with the new_content. For new files, set old_content to an empty string.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path to the file to edit. Can be relative to the working directory or absolute."
                            },
                            "old_content": {
                                "type": "string",
                                "description": "The exact content to be replaced in the file. Use empty string for new files."
                            },
                            "new_content": {
                                "type": "string",
                                "description": "The new content to replace the old content with. For new files, this is the entire file content."
                            }
                        },
                        "required": ["file_path", "old_content", "new_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_python_files",
                    "description": "Search for a regex pattern in Python files (.py) within the working directory. Returns matches with file paths, line numbers, and matching content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "The regex pattern to search for in Python files."
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "If true, searches recursively in subdirectories (default: true)."
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "If true, performs case-sensitive search (default: true)."
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "list_files": self._tool_list_files,
            "read_file": self._tool_read_file,
            "edit_file": self._tool_edit_file,
            "search_python_files": self._tool_search_python_files,
        }

    def start_conversation(self, conversation_id: str, user_request: Optional[str] = None) -> None:
        """
        Start a new conversation with the given ID.

        This delegates to the edit history to prepare for tracking file edits.

        Args:
            conversation_id: Unique conversation ID from AIAgent
            user_request: Optional user request text to store with this checkpoint
        """
        if self.edit_history:
            self.edit_history.start_new_conversation(conversation_id, user_request)

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to the working directory."""
        path_obj = Path(path)
        if not path_obj.is_absolute():
            working_dir = Path(self.working_dir)
            path_obj = working_dir / path_obj
        return path_obj.resolve()

    def _check_permission(self, path: str, action: str, is_directory: bool = False) -> Optional[str]:
        """Check permission for a file/directory operation."""
        if self.permission_manager:
            if not self.permission_manager.request_permission(path, action, is_directory=is_directory):
                return json.dumps({
                    "error": f"Permission denied: {path}",
                    "permission_denied": True
                })
        return None

    def _validate_file_exists(self, path: Path) -> Optional[str]:
        """Validate that a file exists and is a file."""
        if not path.exists():
            return json.dumps({"error": f"File does not exist: {path}"})
        if not path.is_file():
            return json.dumps({"error": f"Path is not a file: {path}"})
        return None

    def _validate_directory_exists(self, path: Path) -> Optional[str]:
        """Validate that a directory exists and is a directory."""
        if not path.exists():
            return json.dumps({"error": f"Folder does not exist: {path}"})
        if not path.is_dir():
            return json.dumps({"error": f"Path is not a directory: {path}"})
        return None

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _json_success(self, **kwargs) -> str:
        """Create a JSON success response."""
        response = {"success": True}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _tool_list_files(self, folder_path: str, only_python: bool = True) -> str:
        """
        Implementation of the list_files tool.

        Args:
            folder_path: Path to the folder to list
            only_python: If True, only list Python files (.py)

        Returns:
            JSON string containing the list of files and directories
        """
        try:
            resolved_path = self._resolve_path(folder_path)

            # Check permission
            perm_error = self._check_permission(str(resolved_path), "list", is_directory=True)
            if perm_error:
                return perm_error

            # Validate directory
            dir_error = self._validate_directory_exists(resolved_path)
            if dir_error:
                return dir_error

            items = []
            working_dir = Path(self.working_dir)

            # Get the forshape folder name from config_manager, fallback to ".forshape"
            forshape_folder = self.config_manager.get_forshape_folder_name() if self.config_manager else ".forshape"

            for item in resolved_path.iterdir():
                # Skip files/directories in the forshape folder
                if forshape_folder in item.parts:
                    continue

                # Skip __pycache__ directories
                if item.name == "__pycache__":
                    continue

                # If only_python is True, filter out non-Python files
                if only_python and item.is_file() and not item.name.endswith('.py'):
                    continue

                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item.relative_to(working_dir)) if item.is_relative_to(working_dir) else str(item)
                }
                items.append(item_info)

            # Sort: directories first, then files, alphabetically
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))

            return json.dumps({
                "folder": str(resolved_path),
                "items": items,
                "count": len(items),
            }, indent=2)

        except Exception as e:
            return self._json_error(f"Error listing files: {str(e)}")

    def _tool_read_file(self, file_path: str) -> str:
        """
        Implementation of the read_file tool.

        Args:
            file_path: Path to the file to read

        Returns:
            File contents or error message
        """
        try:
            resolved_path = self._resolve_path(file_path)

            # Check permission
            perm_error = self._check_permission(str(resolved_path), "read", is_directory=False)
            if perm_error:
                return perm_error

            # Validate file
            file_error = self._validate_file_exists(resolved_path)
            if file_error:
                return file_error

            # Check file size before reading
            file_size = resolved_path.stat().st_size
            if file_size > LARGE_FILE_SIZE_THRESHOLD:
                # Request permission for large file read
                if self.permission_manager:
                    result = self.permission_manager._request_user_permission(
                        str(resolved_path),
                        f"read_large_file ({file_size:,} bytes, exceeds 50KB limit)"
                    )
                    if result == PermissionResponse.DENY:
                        return json.dumps({
                            "error": f"Permission denied: File is too large ({file_size:,} bytes)",
                            "file_size": file_size,
                            "permission_denied": True
                        })

            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return json.dumps({
                "file": str(resolved_path),
                "content": content,
                "size_bytes": len(content.encode('utf-8'))
            }, indent=2)

        except UnicodeDecodeError:
            return self._json_error(f"Cannot read file (not a text file or encoding issue): {file_path}")
        except Exception as e:
            return self._json_error(f"Error reading file: {str(e)}")

    def _tool_edit_file(self, file_path: str, old_content: str, new_content: str) -> str:
        """
        Implementation of the edit_file tool.

        Args:
            file_path: Path to the file to edit
            old_content: Content to be replaced (empty string for new files)
            new_content: New content to insert

        Returns:
            Success message or error
        """
        try:
            resolved_path = self._resolve_path(file_path)

            # Check permission
            perm_error = self._check_permission(str(resolved_path), "write", is_directory=False)
            if perm_error:
                return perm_error

            # Handle file creation if it doesn't exist
            if not resolved_path.exists():
                # Create parent directories if they don't exist
                resolved_path.parent.mkdir(parents=True, exist_ok=True)

                # Create new file with new_content
                with open(resolved_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                # Track file creation in edit history (for deletion during rewind)
                if self.edit_history:
                    creation_tracked = self.edit_history.track_file_creation(resolved_path)
                    if creation_tracked:
                        self.logger.info(f"File creation tracked in edit history: {resolved_path}")
                    else:
                        self.logger.warn(f"Failed to track file creation in edit history: {resolved_path}")

                return self._json_success(
                    file=str(resolved_path),
                    message="File created successfully"
                )

            if not resolved_path.is_file():
                return self._json_error(f"Path is not a file: {resolved_path}")

            # Backup the file before editing (if edit history is enabled)
            if self.edit_history:
                backup_success = self.edit_history.backup_file(resolved_path)
                if backup_success:
                    self.logger.info(f"File backed up to edit history: {resolved_path}")
                else:
                    self.logger.warn(f"Failed to backup file to edit history: {resolved_path}")

            # Read current content
            with open(resolved_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            # Check if old_content exists in the file
            if old_content not in current_content:
                return self._json_error(
                    "Content to replace not found in file",
                    file=str(resolved_path)
                )

            # Replace content
            updated_content = current_content.replace(old_content, new_content)

            # Write back to file
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            return self._json_success(
                file=str(resolved_path),
                message="File edited successfully"
            )

        except Exception as e:
            return self._json_error(f"Error editing file: {str(e)}")

    def _tool_search_python_files(
        self,
        pattern: str,
        recursive: bool = True,
        case_sensitive: bool = True
    ) -> str:
        """
        Implementation of the search_python_files tool.

        Args:
            pattern: Regex pattern to search for
            recursive: If true, searches recursively in subdirectories
            case_sensitive: If true, performs case-sensitive search

        Returns:
            JSON string with search results or error message
        """
        try:
            # Always use working directory
            search_path = Path(self.working_dir)
            self.logger.info(f"Searching Python files for pattern: '{pattern}' (recursive={recursive}, case_sensitive={case_sensitive})")

            # Check permission for search_python_files tool
            perm_error = self._check_permission(str(search_path), "search_python_files", is_directory=True)
            if perm_error:
                return perm_error

            # Validate directory
            dir_error = self._validate_directory_exists(search_path)
            if dir_error:
                return dir_error

            # Compile regex pattern
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                regex = re.compile(pattern, flags)
            except re.error as e:
                return self._json_error(f"Invalid regex pattern: {str(e)}")

            # Get the forshape folder name from config_manager, fallback to ".forshape"
            forshape_folder = self.config_manager.get_forshape_folder_name() if self.config_manager else ".forshape"

            # Find all Python files
            if recursive:
                python_files = list(search_path.rglob("*.py"))
            else:
                python_files = list(search_path.glob("*.py"))

            # Search for pattern in each file
            matches = []
            working_dir = Path(self.working_dir)

            for py_file in python_files:
                # Skip files inside the forshape folder
                if forshape_folder in py_file.parts:
                    continue
                self.logger.info(f"Search file: {py_file}")
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, start=1):
                            if regex.search(line):
                                # Compute relative path for better readability
                                relative_path = str(py_file.relative_to(working_dir)) if py_file.is_relative_to(working_dir) else str(py_file)

                                self.logger.info(f"Found match in: {py_file}, line: {line_num}, content: {line.rstrip()}")

                                matches.append({
                                    "file": relative_path,
                                    "line": line_num,
                                    "content": line.rstrip()
                                })
                except (UnicodeDecodeError, PermissionError):
                    # Skip files that can't be read
                    continue

            self.logger.info(f"Search completed: {len(matches)} matches found in {len(python_files)} files searched")

            return self._json_success(
                pattern=pattern,
                search_path=str(search_path),
                matches=matches,
                total_matches=len(matches),
                files_searched=len(python_files)
            )

        except Exception as e:
            return self._json_error(f"Error searching Python files: {str(e)}")
