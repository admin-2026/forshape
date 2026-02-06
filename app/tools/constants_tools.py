"""
Constants analysis tools for AI Agent.

This module provides tools for analyzing constants defined in Python files,
finding their definitions and references across the codebase.
"""

import ast
import glob
import json
import logging
import os
from typing import Callable

import yaml

from agent.tools.base import ToolBase
from app.variables.constants_parser import ConstantsParser


class _ReferenceVisitor(ast.NodeVisitor):
    """AST visitor to find Load references to a constant name."""

    def __init__(self, constant_name: str):
        self.constant_name = constant_name
        self.has_reference = False

    def visit_Name(self, node):
        if node.id == self.constant_name and isinstance(node.ctx, ast.Load):
            self.has_reference = True
        self.generic_visit(node)


class ConstantsTools(ToolBase):
    """
    Constants analysis tools - injected into ToolManager.

    Provides: analyze_constants
    """

    def __init__(self, working_dir: str, logger: logging.Logger | None = None):
        """
        Initialize constants tools.

        Args:
            working_dir: Working directory for finding constants files
            logger: Optional logger instance for debugging
        """
        self.working_dir = working_dir
        self.logger = logger

    # All available fields for constants
    ALL_FIELDS = ["name", "value", "expression", "source", "referenced"]

    def get_definitions(self) -> list[dict]:
        """Get tool definitions in OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_constants",
                    "description": "Analyze constants defined in constants.py and *_constants.py files. Returns a report with each constant's name, value, expression, source file, and list of files that reference it.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "output_yaml": {
                                "type": "boolean",
                                "description": "Whether to output the result as a YAML file in the working directory. Defaults to false.",
                                "default": False,
                            },
                            "fields": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["name", "value", "expression", "source", "referenced"],
                                },
                                "description": "List of fields to include in the output. Available fields: name, value, expression, source, referenced. Defaults to all fields.",
                            },
                            "source_filter": {
                                "type": "string",
                                "description": "Filter constants by source file name (e.g., 'constants.py' or 'shape_constants.py'). Only constants from this source will be included.",
                            },
                            "min_references": {
                                "type": "integer",
                                "description": "Minimum number of references required. Only constants with at least this many references will be included.",
                            },
                            "max_references": {
                                "type": "integer",
                                "description": "Maximum number of references allowed. Only constants with at most this many references will be included.",
                            },
                        },
                        "required": [],
                    },
                },
            }
        ]

    def get_functions(self) -> dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "analyze_constants": self._tool_analyze_constants,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for constants tools."""
        return """
### Constants Analysis Tools
1. **analyze_constants** - Analyze constants and find their references across the codebase

### Constants Analysis Examples

**User says: "What constants are defined in this project?"**
> Use analyze_constants to get a report of all constants with their values and references

**User says: "Which files use the WIDTH constant?"**
> Use analyze_constants and look at the referenced field for WIDTH

**User says: "Export constants report to a file"**
> Use analyze_constants with output_yaml=true to save the report as constants_report.yaml
"""

    def _find_constants_files(self) -> list[str]:
        """Find all constants files in the working directory.

        Returns:
            List of paths to constants files, with constants.py first if it exists
        """
        files = []
        base_constants = os.path.join(self.working_dir, "constants.py")

        # Add base constants.py first if it exists
        if os.path.exists(base_constants):
            files.append(base_constants)

        # Find all *_constants.py files
        pattern = os.path.join(self.working_dir, "*_constants.py")
        for path in glob.glob(pattern):
            if path not in files:
                files.append(path)

        return files

    def _find_python_files(self) -> list[str]:
        """Find all Python files in the working directory recursively.

        Returns:
            List of paths to Python files
        """
        python_files = []
        for root, dirs, files in os.walk(self.working_dir):
            # Skip common directories that shouldn't be searched
            dirs[:] = [
                d
                for d in dirs
                if d
                not in {
                    "__pycache__",
                    ".git",
                    ".forshape",
                    "venv",
                    ".venv",
                    "node_modules",
                    ".idea",
                    ".vscode",
                    "build",
                    "dist",
                    ".pytest_cache",
                    ".mypy_cache",
                }
            ]
            for filename in files:
                if filename.endswith(".py"):
                    python_files.append(os.path.join(root, filename))
        return python_files

    def _find_references(self, constant_name: str, source_file: str, python_files: list[str]) -> list[str]:
        """Find files that reference a constant using AST.

        Uses AST to distinguish between definitions (Store context) and
        references (Load context), so the source file is included in the search.

        Args:
            constant_name: Name of the constant to search for
            source_file: Path to the file where the constant is defined (kept for API compatibility)
            python_files: List of Python files to search in

        Returns:
            List of unique file paths that reference the constant
        """
        references = []
        seen = set()

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                visitor = _ReferenceVisitor(constant_name)
                visitor.visit(tree)

                if visitor.has_reference:
                    rel_path = os.path.relpath(file_path, self.working_dir)
                    if rel_path not in seen:
                        seen.add(rel_path)
                        references.append(rel_path)
            except (OSError, UnicodeDecodeError, SyntaxError):
                # Skip files that can't be read or parsed
                continue

        return references

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _tool_analyze_constants(
        self,
        output_yaml: bool = False,
        fields: list[str] | None = None,
        source_filter: str | None = None,
        min_references: int | None = None,
        max_references: int | None = None,
        **kwargs,
    ) -> str:
        """
        Implementation of the analyze_constants tool.
        Analyzes constants and finds their references across the codebase.

        Args:
            output_yaml: Whether to output the result as a YAML file
            fields: List of fields to include in output. Defaults to all fields.
            source_filter: Filter by source file name.
            min_references: Minimum number of references required.
            max_references: Maximum number of references allowed.
            **kwargs: Ignored (for forward compatibility).

        Returns:
            JSON string with analysis report or error message
        """
        if self.logger:
            self.logger.info(
                f"analyze_constants called: output_yaml={output_yaml}, fields={fields}, "
                f"source_filter={source_filter}, min_references={min_references}, "
                f"max_references={max_references}, kwargs={kwargs}"
            )

        # Use all fields if not specified
        if fields is None:
            fields = self.ALL_FIELDS

        try:
            constants_files = self._find_constants_files()
            if self.logger:
                self.logger.info(f"Found constants files: {constants_files}")

            if not constants_files:
                return self._json_error("No constants files found in working directory")

            # Get all Python files for reference searching
            python_files = self._find_python_files()
            if self.logger:
                self.logger.info(f"Found {len(python_files)} Python files for reference searching")

            # Build base namespace from constants.py first
            base_namespace = {}
            base_constants_path = os.path.join(self.working_dir, "constants.py")

            if os.path.exists(base_constants_path):
                try:
                    with open(base_constants_path, encoding="utf-8") as f:
                        content = f.read()
                    exec(content, base_namespace)
                except Exception:
                    pass

            # Parse all constants files
            constants_report = []
            for file_path in constants_files:
                source_name = os.path.basename(file_path)
                if self.logger:
                    self.logger.info(f"Processing constants file: {source_name}")

                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                except (OSError, UnicodeDecodeError) as e:
                    if self.logger:
                        self.logger.warning(f"Failed to read {source_name}: {e}")
                    continue

                parser = ConstantsParser(content)
                # Use base namespace for resolving object-specific constants
                if file_path != base_constants_path:
                    variables = parser.parse_and_resolve(base_namespace=base_namespace)
                else:
                    variables = parser.parse_and_resolve()

                if self.logger:
                    self.logger.info(f"Parsed {len(variables)} variables from {source_name}")

                # Skip this source file if source_filter is specified and doesn't match
                if source_filter and source_name != source_filter:
                    continue

                for name, resolved_value, expression in variables:
                    # Find references to this constant (needed for filtering even if not in output)
                    references = self._find_references(name, file_path, python_files)

                    # Filter by reference count
                    ref_count = len(references)
                    if min_references is not None and ref_count < min_references:
                        continue
                    if max_references is not None and ref_count > max_references:
                        continue

                    # Build constant entry with only requested fields
                    constant_entry = {}
                    if "name" in fields:
                        constant_entry["name"] = name
                    if "value" in fields:
                        constant_entry["value"] = resolved_value
                    if "expression" in fields:
                        constant_entry["expression"] = expression
                    if "source" in fields:
                        constant_entry["source"] = source_name
                    if "referenced" in fields:
                        constant_entry["referenced"] = references

                    constants_report.append(constant_entry)

            # Sort by source file, then by name (use empty string if field not present)
            constants_report.sort(key=lambda x: (x.get("source", ""), x.get("name", "")))

            result = {
                "success": True,
                "constants_files": [os.path.basename(f) for f in constants_files],
                "total_constants": len(constants_report),
                "constants": constants_report,
            }

            if self.logger:
                self.logger.info(f"Collected {len(constants_report)} constants total")

            if output_yaml:
                yaml_path = os.path.join(self.working_dir, "constants_report.yaml")
                if self.logger:
                    self.logger.info(f"Writing YAML report to {yaml_path}")
                with open(yaml_path, "w", encoding="utf-8") as f:
                    yaml.dump(result, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                return json.dumps(
                    {
                        "success": True,
                        "message": f"Constants report written to {yaml_path}",
                        "output_file": yaml_path,
                        "total_constants": len(constants_report),
                    },
                    indent=2,
                )

            return json.dumps(result, indent=2)

        except Exception as e:
            if self.logger:
                self.logger.exception(f"Error analyzing constants: {e}")
            return self._json_error(f"Error analyzing constants: {str(e)}")
