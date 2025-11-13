"""
Tool Manager for AI Agent.

This module provides a tool manager that handles file system operations
including listing files, reading files, and editing files.
"""

import json
import re
from typing import List, Dict, Callable, Any, Optional
from pathlib import Path

from .logger import Logger
from .permission_manager import PermissionManager
from shapes.context import Context


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
            "edit_file": self._tool_edit_file,
            "print_object": self._tool_print_object,
            "find_objects_by_regex": self._tool_find_objects_by_regex,
            "print_document": self._tool_print_document,
            "rename_object": self._tool_rename_object,
            "remove_object": self._tool_remove_object,
            "search_python_files": self._tool_search_python_files
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
            import io
            import sys

            # Capture print output
            captured_output = io.StringIO()
            sys.stdout = captured_output

            Context.print_object(obj_or_label, indent=indent, verbose=verbose)

            # Restore stdout
            sys.stdout = sys.__stdout__

            output = captured_output.getvalue()

            return json.dumps({
                "success": True,
                "output": output
            }, indent=2)

        except Exception as e:
            sys.stdout = sys.__stdout__
            return json.dumps({"error": f"Error printing object: {str(e)}"})

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

            return json.dumps({
                "success": True,
                "matches": matches_list,
                "count": len(matches_list)
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error finding objects by regex: {str(e)}"})

    def _tool_print_document(self, verbose: bool = False) -> str:
        """
        Implementation of the print_document tool.

        Args:
            verbose: If true, prints detailed information

        Returns:
            JSON string with success or error message
        """
        try:
            import io
            import sys

            # Capture print output
            captured_output = io.StringIO()
            sys.stdout = captured_output

            Context.print_document(verbose=verbose)

            # Restore stdout
            sys.stdout = sys.__stdout__

            output = captured_output.getvalue()

            return json.dumps({
                "success": True,
                "output": output
            }, indent=2)

        except Exception as e:
            sys.stdout = sys.__stdout__
            return json.dumps({"error": f"Error printing document: {str(e)}"})

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
            import io
            import sys

            # Capture print output
            captured_output = io.StringIO()
            sys.stdout = captured_output

            Context.rename_object(obj_or_label, new_label)

            # Restore stdout
            sys.stdout = sys.__stdout__

            output = captured_output.getvalue()

            # Check if there was an error message in the output
            if "not found" in output or "cannot rename" in output:
                return json.dumps({
                    "success": False,
                    "message": output.strip()
                }, indent=2)

            return json.dumps({
                "success": True,
                "message": output.strip()
            }, indent=2)

        except Exception as e:
            sys.stdout = sys.__stdout__
            return json.dumps({"error": f"Error renaming object: {str(e)}"})

    def _tool_remove_object(self, obj_or_label: str) -> str:
        """
        Implementation of the remove_object tool.

        Args:
            obj_or_label: The object label or name to identify the object

        Returns:
            JSON string with success or error message
        """
        try:
            # Check permission
            if self.permission_manager:
                if not self.permission_manager.request_object_deletion_permission(obj_or_label):
                    return json.dumps({
                        "error": f"Permission denied: Cannot delete object '{obj_or_label}'",
                        "permission_denied": True
                    })

            import io
            import sys

            # Capture print output
            captured_output = io.StringIO()
            sys.stdout = captured_output

            Context.remove_object(obj_or_label)

            # Restore stdout
            sys.stdout = sys.__stdout__

            output = captured_output.getvalue()

            # Check if there was an error message in the output
            if "not found" in output or "cannot remove" in output or "Unsupported" in output:
                return json.dumps({
                    "success": False,
                    "message": output.strip()
                }, indent=2)

            return json.dumps({
                "success": True,
                "message": output.strip()
            }, indent=2)

        except Exception as e:
            sys.stdout = sys.__stdout__
            return json.dumps({"error": f"Error removing object: {str(e)}"})

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

            # Check permission
            if self.permission_manager:
                if not self.permission_manager.request_permission(
                    str(search_path), "list", is_directory=True
                ):
                    return json.dumps({
                        "error": f"Permission denied: {search_path}",
                        "permission_denied": True
                    })

            if not search_path.exists():
                return json.dumps({
                    "error": f"Folder does not exist: {search_path}"
                })

            if not search_path.is_dir():
                return json.dumps({
                    "error": f"Path is not a directory: {search_path}"
                })

            # Compile regex pattern
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                regex = re.compile(pattern, flags)
            except re.error as e:
                return json.dumps({
                    "error": f"Invalid regex pattern: {str(e)}"
                })

            # Find all Python files
            if recursive:
                python_files = list(search_path.rglob("*.py"))
            else:
                python_files = list(search_path.glob("*.py"))

            # Search for pattern in each file
            matches = []
            working_dir = Path(self.working_dir)

            for py_file in python_files:
                # Check read permission for each file
                if self.permission_manager:
                    if not self.permission_manager.request_permission(
                        str(py_file), "read", is_directory=False
                    ):
                        continue  # Skip files without permission

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

            return json.dumps({
                "success": True,
                "pattern": pattern,
                "search_path": str(search_path),
                "matches": matches,
                "total_matches": len(matches),
                "files_searched": len(python_files)
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error searching Python files: {str(e)}"})

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
5. **print_object** - Print information about a FreeCAD object by label or name
6. **find_objects_by_regex** - Find objects whose label, name, or label2 matches a regex pattern
7. **print_document** - Print information about all objects in the active document
8. **rename_object** - Rename a FreeCAD object by changing its Label property
9. **remove_object** - Remove a FreeCAD object from the document

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

Use these tools proactively to provide a better user experience!"""
