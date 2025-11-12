"""
Tool Manager for AI Agent.

This module provides a tool manager that handles file system operations
including listing files, reading files, and editing files.
"""

import json
from typing import List, Dict, Callable, Any, Optional
from pathlib import Path

from .logger import Logger
from .permission_manager import PermissionManager


class ToolManager:
    """
    Manages tools for file system operations.

    This class handles tool definitions, registration, and execution
    for file system operations used by the AI agent.
    """

    def __init__(
        self,
        working_dir: str,
        logger: Optional[Logger] = None,
        permission_manager: Optional[PermissionManager] = None
    ):
        """
        Initialize the tool manager.

        Args:
            working_dir: Working directory for file operations
            logger: Optional logger for tool call logging
            permission_manager: Optional permission manager for access control
        """
        self.working_dir = working_dir
        self.logger = logger
        self.permission_manager = permission_manager
        self.tools = self._define_tools()
        self.tool_functions = self._register_tool_functions()

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
                    "description": "List all files and directories in a given folder path. Returns a list of file and directory names.",
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
            }
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
            "edit_file": self._tool_edit_file
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

    def _tool_list_files(self, folder_path: str) -> str:
        """
        Implementation of the list_files tool.

        Args:
            folder_path: Path to the folder to list

        Returns:
            JSON string containing the list of files and directories
        """
        try:
            resolved_path = self._resolve_path(folder_path)

            # Check permission
            if self.permission_manager:
                if not self.permission_manager.request_permission(
                    str(resolved_path), "list", is_directory=True
                ):
                    return json.dumps({
                        "error": f"Permission denied: {resolved_path}",
                        "permission_denied": True
                    })

            if not resolved_path.exists():
                return json.dumps({
                    "error": f"Folder does not exist: {resolved_path}"
                })

            if not resolved_path.is_dir():
                return json.dumps({
                    "error": f"Path is not a directory: {resolved_path}"
                })

            items = []
            working_dir = Path(self.working_dir)
            for item in resolved_path.iterdir():
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
                "count": len(items)
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error listing files: {str(e)}"})

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
            if self.permission_manager:
                if not self.permission_manager.request_permission(
                    str(resolved_path), "read", is_directory=False
                ):
                    return json.dumps({
                        "error": f"Permission denied: {resolved_path}",
                        "permission_denied": True
                    })

            if not resolved_path.exists():
                return json.dumps({
                    "error": f"File does not exist: {resolved_path}"
                })

            if not resolved_path.is_file():
                return json.dumps({
                    "error": f"Path is not a file: {resolved_path}"
                })

            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return json.dumps({
                "file": str(resolved_path),
                "content": content,
                "size_bytes": len(content.encode('utf-8'))
            }, indent=2)

        except UnicodeDecodeError:
            return json.dumps({
                "error": f"Cannot read file (not a text file or encoding issue): {file_path}"
            })
        except Exception as e:
            return json.dumps({"error": f"Error reading file: {str(e)}"})

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
            if self.permission_manager:
                if not self.permission_manager.request_permission(
                    str(resolved_path), "write", is_directory=False
                ):
                    return json.dumps({
                        "error": f"Permission denied: {resolved_path}",
                        "permission_denied": True
                    })

            # Handle file creation if it doesn't exist
            if not resolved_path.exists():
                # Create parent directories if they don't exist
                resolved_path.parent.mkdir(parents=True, exist_ok=True)

                # Create new file with new_content
                with open(resolved_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                return json.dumps({
                    "success": True,
                    "file": str(resolved_path),
                    "message": "File created successfully"
                }, indent=2)

            if not resolved_path.is_file():
                return json.dumps({
                    "error": f"Path is not a file: {resolved_path}"
                })

            # Read current content
            with open(resolved_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            # Check if old_content exists in the file
            if old_content not in current_content:
                return json.dumps({
                    "error": f"Content to replace not found in file",
                    "file": str(resolved_path)
                })

            # Replace content
            updated_content = current_content.replace(old_content, new_content)

            # Write back to file
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            return json.dumps({
                "success": True,
                "file": str(resolved_path),
                "message": "File edited successfully"
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error editing file: {str(e)}"})

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
            if self.logger:
                self.logger.error(error_msg)
            return json.dumps({"error": error_msg})

        # Log the tool call
        args_str = ", ".join([f"{k}={repr(v)}" for k, v in tool_arguments.items()])
        if self.logger:
            self.logger.info(f"Tool call: {tool_name}({args_str})")

        tool_func = self.tool_functions[tool_name]
        try:
            result = tool_func(**tool_arguments)

            # Check if result contains an error
            try:
                result_dict = json.loads(result)
                if "error" in result_dict:
                    if self.logger:
                        self.logger.warn(f"Tool {tool_name} failed: {result_dict['error']}")
            except (json.JSONDecodeError, TypeError):
                pass  # Result is not JSON, which is fine

            return result
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            if self.logger:
                self.logger.error(f"Tool {tool_name} error: {error_msg}")
            return json.dumps({"error": error_msg})

    def get_tools(self) -> List[Dict]:
        """
        Get the tool definitions.

        Returns:
            List of tool definitions
        """
        return self.tools
