"""
Tool Manager for AI Agent.

This module provides a tool manager that handles file system operations
including listing files, reading files, and editing files.
"""

import json
import re
import threading
from typing import List, Dict, Callable, Any, Optional
from pathlib import Path

from PySide2.QtCore import QObject, Signal

from .logger import Logger
from .permission_manager import PermissionManager, PermissionResponse
from .script_executor import ScriptExecutor
from .edit_history import EditHistory
from shapes.context import Context
from shapes.image_context import ImageContext


# Large file read protection threshold (in bytes)
LARGE_FILE_SIZE_THRESHOLD = 50000  # 50KB


class ToolManager(QObject):
    """
    Manages tools for file system operations.

    This class handles tool definitions, registration, and execution
    for file system operations used by the AI agent.
    """

    # Signal to request clarification dialog on the main thread
    # Emits: list of questions
    clarification_requested = Signal(list)

    def __init__(
        self,
        working_dir: str,
        logger: Logger,
        permission_manager: Optional[PermissionManager] = None,
        image_context: Optional[ImageContext] = None,
        edit_history: Optional[EditHistory] = None,
        config_manager = None
    ):
        """
        Initialize the tool manager.

        Args:
            working_dir: Working directory for file operations
            logger: Logger instance for tool call logging
            permission_manager: Optional permission manager for access control
            image_context: Optional ImageContext instance for screenshot capture
            edit_history: Optional EditHistory instance for tracking file edits
            config_manager: Optional ConfigurationManager instance for configuration
        """
        super().__init__()
        self.working_dir = working_dir
        self.logger = logger
        self.permission_manager = permission_manager
        self.image_context = image_context
        self.edit_history = edit_history
        self.config_manager = config_manager

        # Threading primitives for clarification dialog
        self._clarification_event = threading.Event()
        self._clarification_response = None

        self.tools = self._define_tools()
        self.tool_functions = self._register_tool_functions()

    def start_conversation(self, conversation_id: str, user_request: Optional[str] = None) -> None:
        """
        Start a new conversation with the given ID.

        This delegates to the edit history to prepare for tracking file edits
        in this conversation.

        Args:
            conversation_id: Unique conversation ID from AIAgent
            user_request: Optional user request text to store with this checkpoint
        """
        if self.edit_history:
            self.edit_history.start_new_conversation(conversation_id, user_request)

    def _define_tools(self) -> List[Dict]:
        """
        Define the tools available in OpenAI function format.

        Returns:
            List of tool definitions
        """
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
                    "name": "print_object",
                    "description": "Print information about a FreeCAD object by its label or name. Optionally prints recursively with verbose details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "obj_or_label": {
                                "type": "string",
                                "description": "The object label, name, or the object itself to print information about."
                            },
                            "indent": {
                                "type": "integer",
                                "description": "Indentation level for nested objects (default: 0)."
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "If true, prints detailed information including object types and properties (default: false)."
                            }
                        },
                        "required": ["obj_or_label"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_objects_by_regex",
                    "description": "Scan all objects in the active FreeCAD document to find objects whose label, name, or label2 matches a regex pattern. Returns a list of matched strings and field names.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "A regex pattern string to match against object attributes (Label, Name, or Label2)."
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "print_document",
                    "description": "Print information about all objects in the active FreeCAD document.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "verbose": {
                                "type": "boolean",
                                "description": "If true, prints detailed information including object types and properties (default: false)."
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rename_object",
                    "description": "Rename a FreeCAD object by changing its Label property.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "obj_or_label": {
                                "type": "string",
                                "description": "The object label or internal name to identify the object to rename."
                            },
                            "new_label": {
                                "type": "string",
                                "description": "The new label for the object."
                            }
                        },
                        "required": ["obj_or_label", "new_label"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "remove_object",
                    "description": "Remove a FreeCAD object from the document. Handles different object types appropriately (Sketcher, Pad, Boolean, Body, etc.).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "obj_or_label": {
                                "type": "string",
                                "description": "The object label or internal name to identify the object to remove."
                            }
                        },
                        "required": ["obj_or_label"]
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
            },
            {
                "type": "function",
                "function": {
                    "name": "capture_screenshot",
                    "description": "Capture a screenshot of the FreeCAD 3D view. Automatically saves to history/images folder with timestamp. Can capture entire scene or focus on a specific object, from various perspectives (front, top, isometric, etc.). Supports multiple perspectives in a single call.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Optional object label/name to focus on. If not specified, captures entire scene."
                            },
                            "perspective": {
                                "type": "string",
                                "description": "View angle: 'front', 'back', 'top', 'bottom', 'left', 'right', or 'isometric' (default: 'isometric'). Ignored if perspectives is specified."
                            },
                            "perspectives": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Optional list of perspectives for multiple captures. Example: ['front', 'top', 'isometric']. When provided, ignores the 'perspective' parameter."
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ask_user_clarification",
                    "description": "Ask the user one or more clarification questions and collect their responses. Use this when you need user input to proceed with a task. The user will see a dialog with all questions and can provide responses for each.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "questions": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "List of questions to ask the user. Each question should be clear and specific."
                            }
                        },
                        "required": ["questions"]
                    }
                }
            }
            # {
            #     "type": "function",
            #     "function": {
            #         "name": "run_python_script",
            #         "description": "Load and execute a Python script from the working directory. The script will be executed in the FreeCAD Python environment with access to FreeCAD modules and the Context class. Requires user permission before execution. Automatically runs in teardown mode first to clean up existing objects before running in normal mode.",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "script_path": {
            #                     "type": "string",
            #                     "description": "The path to the Python script to execute. Can be relative to the working directory or absolute."
            #                 },
            #                 "description": {
            #                     "type": "string",
            #                     "description": "A brief description of what the script does (shown to user in permission request)."
            #                 }
            #             },
            #             "required": ["script_path", "description"]
            #         }
            #     }
            # }
        ]

    def _register_tool_functions(self) -> Dict[str, Callable]:
        """
        Register the actual Python functions that implement the tools.

        Returns:
            Dictionary mapping tool names to their implementation functions
        """
        return {
            "list_files": self._tool_list_files,
            "read_file": self._tool_read_file,
            "edit_file": self._tool_edit_file,
            "print_object": self._tool_print_object,
            "find_objects_by_regex": self._tool_find_objects_by_regex,
            "print_document": self._tool_print_document,
            "rename_object": self._tool_rename_object,
            "remove_object": self._tool_remove_object,
            "search_python_files": self._tool_search_python_files,
            "capture_screenshot": self._tool_capture_screenshot,
            "ask_user_clarification": self._tool_ask_user_clarification,
            # "run_python_script": self._tool_run_python_script
        }

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to the working directory.

        Args:
            path: Path string (relative or absolute)

        Returns:
            Resolved Path object
        """
        path_obj = Path(path)
        if not path_obj.is_absolute():
            working_dir = Path(self.working_dir)
            path_obj = working_dir / path_obj
        return path_obj.resolve()

    def _check_permission(self, path: str, action: str, is_directory: bool = False) -> Optional[str]:
        """
        Check permission for a file/directory operation.

        Args:
            path: Path to check permission for
            action: Action type (e.g., "read", "write", "list", "execute")
            is_directory: Whether the path is a directory

        Returns:
            JSON error string if permission denied, None if allowed
        """
        if self.permission_manager:
            if not self.permission_manager.request_permission(path, action, is_directory=is_directory):
                return json.dumps({
                    "error": f"Permission denied: {path}",
                    "permission_denied": True
                })
        return None

    def _validate_file_exists(self, path: Path) -> Optional[str]:
        """
        Validate that a file exists and is a file.

        Args:
            path: Path to validate

        Returns:
            JSON error string if validation fails, None if valid
        """
        if not path.exists():
            return json.dumps({"error": f"File does not exist: {path}"})
        if not path.is_file():
            return json.dumps({"error": f"Path is not a file: {path}"})
        return None

    def _validate_directory_exists(self, path: Path) -> Optional[str]:
        """
        Validate that a directory exists and is a directory.

        Args:
            path: Path to validate

        Returns:
            JSON error string if validation fails, None if valid
        """
        if not path.exists():
            return json.dumps({"error": f"Folder does not exist: {path}"})
        if not path.is_dir():
            return json.dumps({"error": f"Path is not a directory: {path}"})
        return None

    def _json_error(self, message: str, **kwargs) -> str:
        """
        Create a JSON error response.

        Args:
            message: Error message
            **kwargs: Additional fields to include in the response

        Returns:
            JSON string with error
        """
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _json_success(self, **kwargs) -> str:
        """
        Create a JSON success response.

        Args:
            **kwargs: Fields to include in the response

        Returns:
            JSON string with success=True and provided fields
        """
        response = {"success": True}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _capture_output(self):
        """
        Context manager for capturing stdout and stderr.

        Yields:
            A function that returns the captured output as a string
        """
        import io
        import sys
        from contextlib import contextmanager

        @contextmanager
        def _capture():
            captured = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = captured
                sys.stderr = captured
                yield lambda: captured.getvalue()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        return _capture()

    def _tool_list_files(self, folder_path: str, only_python: bool = True) -> str:
        """
        Implementation of the list_files tool.

        Args:
            folder_path: Path to the folder to list
            only_python: If True, only list Python files (.py). If False, list all files (default: True)

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
            self.logger.warn(forshape_folder)
            for item in resolved_path.iterdir():
                # Skip files/directories in the forshape folder
                self.logger.warn(f'item: {item} | item.parts: {item.parts} | item.name: {item.name}')
                if forshape_folder in item.parts:
                    self.logger.warn('skip')
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
                # "filter": "Python files only (.py)" if only_python else "All files"
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
                    result = self.permission_manager.permission_callback(
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

    def _tool_print_object(self, obj_or_label: str, indent: int = 0, verbose: bool = False) -> str:
        """
        Implementation of the print_object tool.

        Args:
            obj_or_label: The object label or name to print
            indent: Indentation level for nested objects
            verbose: If true, prints detailed information

        Returns:
            JSON string with success or error message
        """
        try:
            with self._capture_output() as get_output:
                Context.print_object(obj_or_label, indent=indent, verbose=verbose)
                output = get_output()

            return self._json_success(output=output)

        except Exception as e:
            return self._json_error(f"Error printing object: {str(e)}")

    def _tool_find_objects_by_regex(self, pattern: str) -> str:
        """
        Implementation of the find_objects_by_regex tool.

        Args:
            pattern: Regex pattern to match against object attributes

        Returns:
            JSON string with list of matches or error message
        """
        try:
            matches = Context.find_objects_by_regex(pattern)

            # Convert to list of dicts for better JSON representation
            matches_list = [
                {"matched_string": matched_str, "field_name": field_name}
                for matched_str, field_name in matches
            ]

            return self._json_success(
                matches=matches_list,
                count=len(matches_list)
            )

        except Exception as e:
            return self._json_error(f"Error finding objects by regex: {str(e)}")

    def _tool_print_document(self, verbose: bool = False) -> str:
        """
        Implementation of the print_document tool.

        Args:
            verbose: If true, prints detailed information

        Returns:
            JSON string with success or error message
        """
        try:
            with self._capture_output() as get_output:
                Context.print_document(verbose=verbose)
                output = get_output()

            return self._json_success(output=output)

        except Exception as e:
            return self._json_error(f"Error printing document: {str(e)}")

    def _tool_rename_object(self, obj_or_label: str, new_label: str) -> str:
        """
        Implementation of the rename_object tool.

        Args:
            obj_or_label: The object label or name to identify the object
            new_label: The new label for the object

        Returns:
            JSON string with success or error message
        """
        try:
            with self._capture_output() as get_output:
                Context.rename_object(obj_or_label, new_label)
                output = get_output()

            # Check if there was an error message in the output
            if "not found" in output or "cannot rename" in output:
                return json.dumps({
                    "success": False,
                    "message": output.strip()
                }, indent=2)

            return self._json_success(message=output.strip())

        except Exception as e:
            return self._json_error(f"Error renaming object: {str(e)}")

    def _tool_remove_object(self, obj_or_label: str) -> str:
        """
        Implementation of the remove_object tool.

        Args:
            obj_or_label: The object label or name to identify the object

        Returns:
            JSON string with success or error message
        """
        try:
            # Check permission (using special deletion permission)
            if self.permission_manager:
                if not self.permission_manager.request_object_deletion_permission(obj_or_label):
                    return json.dumps({
                        "error": f"Permission denied: Cannot delete object '{obj_or_label}'",
                        "permission_denied": True
                    })

            with self._capture_output() as get_output:
                Context.remove_object(obj_or_label)
                output = get_output()

            # Check if there was an error message in the output
            if "not found" in output or "cannot remove" in output or "Unsupported" in output:
                return json.dumps({
                    "success": False,
                    "message": output.strip()
                }, indent=2)

            return self._json_success(message=output.strip())

        except Exception as e:
            return self._json_error(f"Error removing object: {str(e)}")

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

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, start=1):
                            if regex.search(line):
                                # Compute relative path for better readability
                                relative_path = str(py_file.relative_to(working_dir)) if py_file.is_relative_to(working_dir) else str(py_file)

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

    def _tool_capture_screenshot(
        self,
        target: Optional[str] = None,
        perspective: str = "isometric",
        perspectives: Optional[List[str]] = None
    ) -> str:
        """
        Implementation of the capture_screenshot tool.
        Automatically saves screenshots to history/images folder with timestamp.
        Returns the image data as base64 so the LLM can see it.

        Args:
            target: Optional object label/name to focus on
            perspective: View angle (default: "isometric")
            perspectives: Optional list of perspectives for multiple captures

        Returns:
            JSON string with success or error message, including base64-encoded image(s)
        """
        try:
            # Check if image_context is available
            if self.image_context is None:
                return json.dumps({
                    "success": False,
                    "message": "ImageContext not configured"
                })

            with self._capture_output() as get_output:
                # Call image_context.capture_encoded() - handles both capture and base64 encoding
                result = self.image_context.capture_encoded(
                    target=target,
                    perspective=perspective,
                    perspectives=perspectives
                )
                output = get_output()

            # Check if capture was successful
            if result is None:
                return json.dumps({
                    "success": False,
                    "message": output.strip() if output else "Screenshot capture failed"
                }, indent=2)

            # Add captured output to the result
            result["output"] = output.strip()

            # Add success message if not present
            if "message" not in result:
                if "images" in result:
                    result["message"] = "Screenshots captured successfully"
                else:
                    result["message"] = "Screenshot captured successfully"

            return json.dumps(result, indent=2)

        except Exception as e:
            return self._json_error(f"Error capturing screenshot: {str(e)}")

    def _tool_ask_user_clarification(self, questions: List[str]) -> str:
        """
        Implementation of the ask_user_clarification tool.
        Shows a dialog to ask the user clarification questions.

        This method emits a signal to request the dialog be shown on the main thread,
        then waits for the response using a threading event.

        Args:
            questions: List of questions to ask the user

        Returns:
            JSON string with user responses or error message
        """
        try:
            # Validate questions
            if not questions or not isinstance(questions, list):
                return self._json_error("questions must be a non-empty list")

            if len(questions) == 0:
                return self._json_error("At least one question is required")

            # Reset the event and response before requesting
            self._clarification_event.clear()
            self._clarification_response = None

            # Emit signal to show dialog on main thread
            self.clarification_requested.emit(questions)

            # Wait for the response (blocking until main thread responds)
            self._clarification_event.wait()

            # Process the response
            response = self._clarification_response
            if response is None:
                return self._json_error("No response received from clarification dialog")

            if response.get("cancelled", False):
                return json.dumps({
                    "success": False,
                    "message": "User cancelled the clarification dialog",
                    "cancelled": True
                }, indent=2)

            return self._json_success(
                message="User provided clarification responses",
                responses=response.get("responses", {})
            )

        except Exception as e:
            return self._json_error(f"Error asking user clarification: {str(e)}")

    def set_clarification_response(self, responses: Optional[Dict], cancelled: bool = False) -> None:
        """
        Set the clarification response from the main thread.

        This method should be called from the main GUI thread after the
        clarification dialog is closed.

        Args:
            responses: Dictionary of responses from the dialog, or None if cancelled
            cancelled: Whether the user cancelled the dialog
        """
        if cancelled:
            self._clarification_response = {"cancelled": True}
        else:
            self._clarification_response = {"responses": responses, "cancelled": False}
        # Signal the waiting thread that the response is ready
        self._clarification_event.set()

    def _tool_run_python_script(self, script_path: str, description: str, teardown_first: bool = True) -> str:
        """
        Implementation of the run_python_script tool.
        Executes a Python script from the working directory with user permission.
        Always runs teardown first to clean up existing objects before normal execution.

        Args:
            script_path: Path to the Python script to execute
            description: Description of what the script does (for permission request)
            teardown_first: Internal parameter to control teardown behavior (defaults to True)

        Returns:
            JSON string with execution results or error message
        """
        try:
            resolved_path = self._resolve_path(script_path)

            # Validate that it's a Python file
            if not str(resolved_path).endswith('.py'):
                return self._json_error(f"File must be a Python script (.py): {resolved_path}")

            # Validate file exists
            file_error = self._validate_file_exists(resolved_path)
            if file_error:
                return file_error

            # Check permission
            perm_error = self._check_permission(str(resolved_path), "execute", is_directory=False)
            if perm_error:
                # Add description to permission error
                error_dict = json.loads(perm_error)
                error_dict["description"] = description
                return json.dumps(error_dict)

            # Read the script content
            with open(resolved_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Execute the script using ScriptExecutor
            if teardown_first:
                # Run in teardown mode first, then normal mode
                teardown_result, normal_result = ScriptExecutor.execute_with_teardown(
                    script_content, resolved_path, import_freecad=True
                )
                success = normal_result.success
                output = normal_result.output
                error_msg = normal_result.error
                teardown_output = teardown_result.output
            else:
                # Run in normal mode only
                result = ScriptExecutor.execute(
                    script_content, resolved_path, teardown_mode=False, import_freecad=True
                )
                success = result.success
                output = result.output
                error_msg = result.error
                teardown_output = None

            if success:
                result = {
                    "success": True,
                    "script": str(resolved_path),
                    "description": description,
                    "output": output.strip() if output else "(no output)",
                    "message": "Script executed successfully"
                }
                if teardown_first and teardown_output is not None:
                    result["teardown_output"] = teardown_output.strip() if teardown_output else "(no teardown output)"
                    result["message"] = "Script executed successfully (with teardown first)"
                return json.dumps(result, indent=2)
            else:
                result = {
                    "success": False,
                    "script": str(resolved_path),
                    "description": description,
                    "error": error_msg,
                    "output": output.strip() if output else "(no output)"
                }
                if teardown_first and teardown_output is not None:
                    result["teardown_output"] = teardown_output.strip() if teardown_output else "(no teardown output)"
                return json.dumps(result, indent=2)

        except UnicodeDecodeError:
            return self._json_error(f"Cannot read script file (encoding issue): {script_path}")
        except Exception as e:
            return self._json_error(f"Error executing script: {str(e)}")

    def execute_tool(self, tool_name: str, tool_arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name with given arguments.

        Args:
            tool_name: Name of the tool to execute
            tool_arguments: Arguments to pass to the tool

        Returns:
            Tool execution result as string
        """
        if tool_name not in self.tool_functions:
            error_msg = f"Unknown tool: {tool_name}"
            self.logger.error(error_msg)
            return json.dumps({"error": error_msg})

        # Log the tool call
        args_str = ", ".join([f"{k}={repr(v)}" for k, v in tool_arguments.items()])
        self.logger.info(f"Tool call: {tool_name}({args_str})")

        tool_func = self.tool_functions[tool_name]
        try:
            result = tool_func(**tool_arguments)

            # Check if result contains an error
            try:
                result_dict = json.loads(result)
                if "error" in result_dict:
                    self.logger.warn(f"Tool {tool_name} failed: {result_dict['error']}")
            except (json.JSONDecodeError, TypeError):
                pass  # Result is not JSON, which is fine

            return result
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            self.logger.error(f"Tool {tool_name} error: {error_msg}")
            return json.dumps({"error": error_msg})

    def get_tools(self) -> List[Dict]:
        """
        Get the tool definitions.

        Returns:
            List of tool definitions
        """
        return self.tools

    @staticmethod
    def get_tool_usage_instructions() -> str:
        """
        Get comprehensive tool usage instructions for the AI agent.

        Returns:
            Formatted string with tool usage instructions
        """
        return """

## Available Tools

You have access to the following tools:

### File Management Tools
1. **list_files** - List files and directories in any folder
2. **read_file** - Read the contents of any file
3. **edit_file** - Edit files by replacing content
4. **search_python_files** - Search for regex patterns in Python files within the working directory

### FreeCAD Object Tools
6. **print_object** - Print information about a FreeCAD object by label or name
7. **find_objects_by_regex** - Find objects whose label, name, or label2 matches a regex pattern
8. **print_document** - Print information about all objects in the active document
9. **rename_object** - Rename a FreeCAD object by changing its Label property
10. **remove_object** - Remove a FreeCAD object from the document

### FreeCAD Visualization Tools
11. **capture_screenshot** - Capture screenshots of the FreeCAD 3D view from various perspectives

### User Interaction Tools
12. **ask_user_clarification** - Ask the user one or more clarification questions and collect their responses

### Working with Generated Scripts

When users ask you to generate or modify Python scripts for shapes:
1. You can use your tools to **directly update the generated script files**
2. You can read existing scripts to understand what's already been created
3. You can edit scripts to fix issues, add features, or improve code
4. Scripts are typically stored in the working directory or shapes folder

### Working with FreeCAD Objects

When users ask about objects in their FreeCAD document:
1. Use **print_document** to see all objects in the scene
2. Use **print_object** with verbose=true to get detailed information about specific objects
3. Use **find_objects_by_regex** to search for objects by name patterns

### Best Practices

- When a user reports an error in a generated script, **read the script first** to understand the issue
- After generating new code, you can **directly write or edit the script file** instead of just showing code
- Use **list_files** to explore the project structure when needed
- Always verify changes by reading the file after editing
- Use **find_objects_by_regex** to locate objects when you need to reference them by pattern

### Example Workflows

**User says: "Add a red sphere to the scene"**
→ Generate the code and either tell the user to save it, OR directly edit their current script file

**User says: "The script has an error on line 15"**
→ Read the script file, identify the issue, edit the file to fix it, confirm the fix

**User says: "What scripts have I created?"**
→ List files in the working directory to show them their generated scripts

**User says: "Show me all objects in the document"**
→ Use print_document with verbose=true to show the full object hierarchy

**User says: "Find all boxes in the scene"**
→ Use find_objects_by_regex with pattern like "box.*" or "Box.*"

**User says: "Rename the box to 'MainBox'"**
→ Use rename_object with obj_or_label="box" and new_label="MainBox"

**User says: "Delete the sphere" or "Remove the cylinder"**
→ Use remove_object with obj_or_label="sphere" or "cylinder"

**User says: "Find all files that import FreeCAD"**
→ Use search_python_files with pattern="import FreeCAD" or "from FreeCAD"

**User says: "Search for all functions that create boxes"**
→ Use search_python_files with pattern="def.*box" (case insensitive if needed)

**User says: "Find usages of the Context class"**
→ Use search_python_files with pattern="Context\\." to find all references

**User says: "Take a screenshot of the model"**
→ Use capture_screenshot (no parameters needed - auto-saves with timestamp)

**User says: "Capture the box from the front view"**
→ Use capture_screenshot with target="box", perspective="front"

**User says: "Take screenshots from multiple angles"**
→ Use capture_screenshot with perspectives=["front", "top", "isometric"]

**User says: "Show me what the object looks like"**
→ Use capture_screenshot to capture an image of the object and return the image

**User says: "Create a custom shape"**
→ Use ask_user_clarification with questions like ["What type of shape do you want?", "What dimensions should it have?", "What color would you like?"]

**AI Agent needs clarification:**
→ If the user's request is ambiguous or missing key information, use ask_user_clarification to gather the necessary details before proceeding

Use these tools proactively to provide a better user experience!"""
