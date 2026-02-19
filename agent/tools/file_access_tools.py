"""
File access tools for AI Agent.

This module provides file system operations including listing files,
reading files, editing files, and searching Python files.
"""

import json
import re
from pathlib import Path
from typing import Callable, Optional

from ..edit_history import EditHistory
from ..logger_protocol import LoggerProtocol
from ..permission_manager import PermissionManager, PermissionResponse
from .base import ToolBase

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
        exclude_folders: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
    ):
        """
        Initialize file access tools.

        Args:
            working_dir: Working directory for file operations
            logger: LoggerProtocol instance for logging
            permission_manager: Optional permission manager for access control
            edit_history: Optional EditHistory instance for tracking file edits
            exclude_folders: Optional list of folder patterns to skip when listing/searching files
            exclude_patterns: Optional list of file/directory name patterns to skip (e.g., "__pycache__")
        """
        self.working_dir = working_dir
        self.logger = logger
        self.permission_manager = permission_manager
        self.edit_history = edit_history
        self.exclude_folders = exclude_folders or []
        self.exclude_patterns = exclude_patterns or []

    def get_definitions(self) -> list[dict]:
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
                                "description": "The path to the folder to list files from. Can be relative to the working directory or absolute.",
                            }
                        },
                        "required": ["folder_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file at the given path. Returns the file contents as a string. Optionally read only specific lines by providing start_line and limit.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path to the file to read. Can be relative to the working directory or absolute.",
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "The line number to start reading from (1-based). If not provided, reads from the beginning.",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "The maximum number of lines to read. If not provided, reads until the end of the file.",
                            },
                        },
                        "required": ["file_path"],
                    },
                },
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
                                "description": "The path to the file to edit. Can be relative to the working directory or absolute.",
                            },
                            "old_content": {
                                "type": "string",
                                "description": "The exact content to be replaced in the file. Use empty string for new files.",
                            },
                            "new_content": {
                                "type": "string",
                                "description": "The new content to replace the old content with. For new files, this is the entire file content.",
                            },
                        },
                        "required": ["file_path", "old_content", "new_content"],
                    },
                },
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
                                "description": "The regex pattern to search for in Python files.",
                            },
                            "paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional list of files or folders to search within. Each path must be relative to the working directory. If not provided, searches the entire working directory.",
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "If true, searches recursively in subdirectories (default: true).",
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "If true, performs case-sensitive search (default: true).",
                            },
                        },
                        "required": ["pattern"],
                    },
                },
            },
        ]

    def get_functions(self) -> dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "list_files": self._tool_list_files,
            "read_file": self._tool_read_file,
            "edit_file": self._tool_edit_file,
            "search_python_files": self._tool_search_python_files,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for file access tools."""
        return """
### File Management Tools
1. **list_files** - List files and directories in any folder
2. **read_file** - Read the contents of any file (supports reading specific lines with start_line and limit)
3. **edit_file** - Edit files by replacing content
4. **search_python_files** - Search for regex patterns in Python files within the working directory

### Working with Generated files

When users ask you to generate or modify files:
1. You can use your tools to **directly update the generated files**
2. You can read existing files to understand what's already been created
3. You can edit files to fix issues, add features, or improve code

### File Management Examples

**User says: "The script has an error on line 15"**
> Read the script file, identify the issue, edit the file to fix it, confirm the fix

**User says: "What scripts have I created?"**
> List files in the working directory to show them their generated scripts

**User says: "Find all files that import FreeCAD"**
> Use search_python_files with pattern="import FreeCAD" or "from FreeCAD"

**User says: "Search for all functions that create boxes"**
> Use search_python_files with pattern="def.*box" (case insensitive if needed)

**User says: "Find usages of the Context class"**
> Use search_python_files with pattern="Context\\." to find all references
"""

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
                return json.dumps({"error": f"Permission denied: {path}", "permission_denied": True})
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

            for item in resolved_path.iterdir():
                # Skip files/directories in excluded folders
                if any(folder in item.parts for folder in self.exclude_folders):
                    continue

                # Skip files/directories matching exclude patterns
                if item.name in self.exclude_patterns:
                    continue

                # If only_python is True, filter out non-Python files
                if only_python and item.is_file() and not item.name.endswith(".py"):
                    continue

                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item.relative_to(working_dir)) if item.is_relative_to(working_dir) else str(item),
                }
                items.append(item_info)

            # Sort: directories first, then files, alphabetically
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))

            return json.dumps(
                {
                    "folder": str(resolved_path),
                    "items": items,
                    "count": len(items),
                },
                indent=2,
            )

        except Exception as e:
            return self._json_error(f"Error listing files: {str(e)}")

    def _tool_read_file(self, file_path: str, start_line: Optional[int] = None, limit: Optional[int] = None) -> str:
        """
        Implementation of the read_file tool.

        Args:
            file_path: Path to the file to read
            start_line: Line number to start reading from (1-based). If None, reads from the beginning.
            limit: Maximum number of lines to read. If None, reads until the end.

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

            # Validate parameters
            if start_line is not None and start_line < 1:
                return self._json_error("start_line must be >= 1")
            if limit is not None and limit < 1:
                return self._json_error("limit must be >= 1")

            # Check file size before reading (only for full file reads)
            file_size = resolved_path.stat().st_size
            if start_line is None and limit is None and file_size > LARGE_FILE_SIZE_THRESHOLD:
                # Request permission for large file read
                if self.permission_manager:
                    result = self.permission_manager._request_user_permission(
                        str(resolved_path), f"read_large_file ({file_size:,} bytes, exceeds 50KB limit)"
                    )
                    if result == PermissionResponse.DENY:
                        return json.dumps(
                            {
                                "error": f"Permission denied: File is too large ({file_size:,} bytes)",
                                "file_size": file_size,
                                "permission_denied": True,
                            }
                        )

            with open(resolved_path, encoding="utf-8") as f:
                if start_line is None and limit is None:
                    # Read entire file
                    content = f.read()
                    total_lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
                    return json.dumps(
                        {
                            "file": str(resolved_path),
                            "content": content,
                            "size_bytes": len(content.encode("utf-8")),
                            "total_lines": total_lines,
                        },
                        indent=2,
                    )
                else:
                    # Read specific lines
                    lines = f.readlines()
                    total_lines = len(lines)

                    # Convert to 0-based index
                    start_idx = (start_line - 1) if start_line else 0

                    if start_idx >= total_lines:
                        return self._json_error(
                            f"start_line {start_line} exceeds total lines ({total_lines})",
                            total_lines=total_lines,
                        )

                    end_idx = start_idx + limit if limit else total_lines
                    selected_lines = lines[start_idx:end_idx]
                    content = "".join(selected_lines)

                    return json.dumps(
                        {
                            "file": str(resolved_path),
                            "content": content,
                            "start_line": start_idx + 1,
                            "end_line": min(start_idx + len(selected_lines), total_lines),
                            "lines_read": len(selected_lines),
                            "total_lines": total_lines,
                        },
                        indent=2,
                    )

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
                with open(resolved_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                # Track file creation in edit history (for deletion during rewind)
                if self.edit_history:
                    creation_tracked = self.edit_history.track_file_creation(resolved_path)
                    if creation_tracked:
                        self.logger.info(f"File creation tracked in edit history: {resolved_path}")
                    else:
                        self.logger.warn(f"Failed to track file creation in edit history: {resolved_path}")

                return self._json_success(file=str(resolved_path), message="File created successfully")

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
            with open(resolved_path, encoding="utf-8") as f:
                current_content = f.read()

            # Remove null bytes to avoid SyntaxError
            current_content = current_content.replace("\x00", "")
            old_content = old_content.replace("\x00", "")
            new_content = new_content.replace("\x00", "")

            # Check if old_content exists in the file
            if old_content not in current_content:
                return self._json_error("Content to replace not found in file", file=str(resolved_path))

            # Replace content
            updated_content = current_content.replace(old_content, new_content)

            # Write back to file
            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            return self._json_success(file=str(resolved_path), message="File edited successfully")

        except Exception as e:
            return self._json_error(f"Error editing file: {str(e)}")

    def _tool_search_python_files(
        self,
        pattern: str,
        paths: Optional[list[str]] = None,
        recursive: bool = True,
        case_sensitive: bool = True,
    ) -> str:
        """
        Implementation of the search_python_files tool.

        Args:
            pattern: Regex pattern to search for
            paths: Optional list of files/folders to search within (must be in working directory)
            recursive: If true, searches recursively in subdirectories
            case_sensitive: If true, performs case-sensitive search

        Returns:
            JSON string with search results or error message
        """
        try:
            working_dir = Path(self.working_dir)
            self.logger.info(
                f"Searching Python files for pattern: '{pattern}' "
                f"(paths={paths}, recursive={recursive}, case_sensitive={case_sensitive})"
            )

            # Check permission for search_python_files tool
            perm_error = self._check_permission(str(working_dir), "search_python_files", is_directory=True)
            if perm_error:
                return perm_error

            # Validate working directory
            dir_error = self._validate_directory_exists(working_dir)
            if dir_error:
                return dir_error

            # Compile regex pattern
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                regex = re.compile(pattern, flags)
            except re.error as e:
                return self._json_error(f"Invalid regex pattern: {str(e)}")

            # Collect Python files to search
            python_files: list[Path] = []

            if paths:
                for p in paths:
                    resolved = (working_dir / p).resolve()
                    # Ensure the path is within the working directory
                    if not resolved.is_relative_to(working_dir):
                        return self._json_error(f"Path is outside the working directory: {p}")
                    if resolved.is_file():
                        if resolved.suffix == ".py":
                            python_files.append(resolved)
                    elif resolved.is_dir():
                        if recursive:
                            python_files.extend(resolved.rglob("*.py"))
                        else:
                            python_files.extend(resolved.glob("*.py"))
                    else:
                        return self._json_error(f"Path does not exist: {p}")
            else:
                if recursive:
                    python_files = list(working_dir.rglob("*.py"))
                else:
                    python_files = list(working_dir.glob("*.py"))

            # Search for pattern in each file
            matches = []

            for py_file in python_files:
                # Skip files inside excluded folders
                if any(folder in py_file.parts for folder in self.exclude_folders):
                    continue
                # Skip files matching exclude patterns
                if py_file.name in self.exclude_patterns:
                    continue
                self.logger.info(f"Search file: {py_file}")
                try:
                    with open(py_file, encoding="utf-8") as f:
                        for line_num, line in enumerate(f, start=1):
                            if regex.search(line):
                                # Compute relative path for better readability
                                relative_path = (
                                    str(py_file.relative_to(working_dir))
                                    if py_file.is_relative_to(working_dir)
                                    else str(py_file)
                                )

                                self.logger.info(
                                    f"Found match in: {py_file}, line: {line_num}, content: {line.rstrip()}"
                                )

                                matches.append({"file": relative_path, "line": line_num, "content": line.rstrip()})
                except (UnicodeDecodeError, PermissionError):
                    # Skip files that can't be read
                    continue

            self.logger.info(f"Search completed: {len(matches)} matches found in {len(python_files)} files searched")

            return self._json_success(
                pattern=pattern,
                search_path=str(working_dir),
                matches=matches,
                total_matches=len(matches),
                files_searched=len(python_files),
            )

        except Exception as e:
            return self._json_error(f"Error searching Python files: {str(e)}")
