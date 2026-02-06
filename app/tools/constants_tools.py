"""
Constants analysis tools for AI Agent.

This module provides tools for analyzing constants defined in Python files,
finding their definitions and references across the codebase.
"""

import glob
import json
import os
import re
from typing import Callable

import yaml

from agent.tools.base import ToolBase
from app.variables.constants_parser import ConstantsParser


class ConstantsTools(ToolBase):
    """
    Constants analysis tools - injected into ToolManager.

    Provides: analyze_constants
    """

    def __init__(self, working_dir: str):
        """
        Initialize constants tools.

        Args:
            working_dir: Working directory for finding constants files
        """
        self.working_dir = working_dir

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
                            "include_unreferenced": {
                                "type": "boolean",
                                "description": "Whether to include constants that are not referenced by any file. Defaults to true.",
                                "default": True,
                            },
                            "output_yaml": {
                                "type": "boolean",
                                "description": "Whether to output the result as a YAML file in the working directory. Defaults to false.",
                                "default": False,
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
            dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "venv", ".venv", "node_modules"}]
            for filename in files:
                if filename.endswith(".py"):
                    python_files.append(os.path.join(root, filename))
        return python_files

    def _find_references(self, constant_name: str, source_file: str, python_files: list[str]) -> list[str]:
        """Find files that reference a constant.

        Args:
            constant_name: Name of the constant to search for
            source_file: Path to the file where the constant is defined (excluded from results)
            python_files: List of Python files to search in

        Returns:
            List of file paths that reference the constant
        """
        references = []
        # Pattern to match the constant name as a whole word
        pattern = re.compile(rf"\b{re.escape(constant_name)}\b")

        source_file_normalized = os.path.normpath(source_file)

        for file_path in python_files:
            # Skip the source file
            if os.path.normpath(file_path) == source_file_normalized:
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                if pattern.search(content):
                    # Return relative path for cleaner output
                    rel_path = os.path.relpath(file_path, self.working_dir)
                    references.append(rel_path)
            except (OSError, UnicodeDecodeError):
                # Skip files that can't be read
                continue

        return references

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _tool_analyze_constants(self, include_unreferenced: bool = True, output_yaml: bool = False) -> str:
        """
        Implementation of the analyze_constants tool.
        Analyzes constants and finds their references across the codebase.

        Args:
            include_unreferenced: Whether to include constants not referenced by any file
            output_yaml: Whether to output the result as a YAML file

        Returns:
            JSON string with analysis report or error message
        """
        try:
            constants_files = self._find_constants_files()

            if not constants_files:
                return self._json_error("No constants files found in working directory")

            # Get all Python files for reference searching
            python_files = self._find_python_files()

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

                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                except (OSError, UnicodeDecodeError):
                    continue

                parser = ConstantsParser(content)
                # Use base namespace for resolving object-specific constants
                if file_path != base_constants_path:
                    variables = parser.parse_and_resolve(base_namespace=base_namespace)
                else:
                    variables = parser.parse_and_resolve()

                for name, resolved_value, expression in variables:
                    # Find references to this constant
                    references = self._find_references(name, file_path, python_files)

                    # Skip unreferenced constants if requested
                    if not include_unreferenced and not references:
                        continue

                    constants_report.append(
                        {
                            "name": name,
                            "value": resolved_value,
                            "expression": expression,
                            "source": source_name,
                            "referenced": references,
                        }
                    )

            # Sort by source file, then by name
            constants_report.sort(key=lambda x: (x["source"], x["name"]))

            result = {
                "success": True,
                "constants_files": [os.path.basename(f) for f in constants_files],
                "total_constants": len(constants_report),
                "constants": constants_report,
            }

            if output_yaml:
                yaml_path = os.path.join(self.working_dir, "constants_report.yaml")
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
            return self._json_error(f"Error analyzing constants: {str(e)}")
