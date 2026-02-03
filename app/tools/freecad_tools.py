"""
FreeCAD object manipulation tools.

This module provides tools for interacting with FreeCAD objects,
including printing, finding, renaming, and removing objects.
"""

import io
import json
import sys
from contextlib import contextmanager
from typing import Callable, Dict, List, Optional

from agent.permission_manager import PermissionManager
from agent.tools.base import ToolBase
from shapes.context import Context


class FreeCADTools(ToolBase):
    """
    FreeCAD object manipulation tools - injected into ToolManager.

    Provides: print_object, find_objects_by_regex, print_document,
              rename_object, remove_object
    """

    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        """
        Initialize FreeCAD tools.

        Args:
            permission_manager: Optional permission manager for access control
        """
        self.permission_manager = permission_manager

    def get_definitions(self) -> List[Dict]:
        """Get tool definitions in OpenAI function format."""
        return [
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
                                "description": "The object label, name, or the object itself to print information about.",
                            },
                            "indent": {
                                "type": "integer",
                                "description": "Indentation level for nested objects (default: 0).",
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "If true, prints detailed information including object types and properties (default: false).",
                            },
                        },
                        "required": ["obj_or_label"],
                    },
                },
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
                                "description": "A regex pattern string to match against object attributes (Label, Name, or Label2).",
                            }
                        },
                        "required": ["pattern"],
                    },
                },
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
                                "description": "If true, prints detailed information including object types and properties (default: false).",
                            }
                        },
                    },
                },
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
                                "description": "The object label or internal name to identify the object to rename.",
                            },
                            "new_label": {"type": "string", "description": "The new label for the object."},
                        },
                        "required": ["obj_or_label", "new_label"],
                    },
                },
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
                                "description": "The object label or internal name to identify the object to remove.",
                            }
                        },
                        "required": ["obj_or_label"],
                    },
                },
            },
        ]

    def get_functions(self) -> Dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "print_object": self._tool_print_object,
            "find_objects_by_regex": self._tool_find_objects_by_regex,
            "print_document": self._tool_print_document,
            "rename_object": self._tool_rename_object,
            "remove_object": self._tool_remove_object,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for FreeCAD tools."""
        return """
### FreeCAD Object Tools
1. **print_object** - Print information about a FreeCAD object by label or name
2. **find_objects_by_regex** - Find objects whose label, name, or label2 matches a regex pattern
3. **print_document** - Print information about all objects in the active document
4. **rename_object** - Rename a FreeCAD object by changing its Label property
5. **remove_object** - Remove a FreeCAD object from the document

### Working with FreeCAD Objects

When users ask about objects in their FreeCAD document:
1. Use **print_document** to see all objects in the scene
2. Use **print_object** with verbose=true to get detailed information about specific objects
3. Use **find_objects_by_regex** to search for objects by name patterns

### FreeCAD Object Examples

**User says: "Show me all objects in the document"**
> Use print_document with verbose=true to show the full object hierarchy

**User says: "Find all boxes in the scene"**
> Use find_objects_by_regex with pattern like "box.*" or "Box.*"

**User says: "Rename the box to 'MainBox'"**
> Use rename_object with obj_or_label="box" and new_label="MainBox"

**User says: "Delete the sphere" or "Remove the cylinder"**
> Use remove_object with obj_or_label="sphere" or "cylinder"
"""

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

    @contextmanager
    def _capture_output(self):
        """Context manager for capturing stdout and stderr."""
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
                {"matched_string": matched_str, "field_name": field_name} for matched_str, field_name in matches
            ]

            return self._json_success(matches=matches_list, count=len(matches_list))

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
                return json.dumps({"success": False, "message": output.strip()}, indent=2)

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
                    return json.dumps(
                        {
                            "error": f"Permission denied: Cannot delete object '{obj_or_label}'",
                            "permission_denied": True,
                        }
                    )

            with self._capture_output() as get_output:
                Context.remove_object(obj_or_label)
                output = get_output()

            # Check if there was an error message in the output
            if "not found" in output or "cannot remove" in output or "Unsupported" in output:
                return json.dumps({"success": False, "message": output.strip()}, indent=2)

            return self._json_success(message=output.strip())

        except Exception as e:
            return self._json_error(f"Error removing object: {str(e)}")
