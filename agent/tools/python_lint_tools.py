"""
Python linting tools for AI Agent.

This module provides Python code linting tools
using ruff to check Python files under a directory.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable

from .base import ToolBase

# Hide console window on Windows when running from GUI
_SUBPROCESS_FLAGS = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}


class PythonLintTools(ToolBase):
    """
    Python linting tools using ruff.

    Provides tools to lint Python files under a directory.
    """

    def __init__(self, exclude_dirs: list[str] | None = None):
        self.exclude_dirs = exclude_dirs or []

    def get_definitions(self) -> list[dict]:
        """Get tool definitions in OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "lint_python",
                    "description": "Lint and optionally format Python files under a directory using ruff. Returns linting issues found in the code.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "The directory path containing Python files to lint. Can be absolute or relative path.",
                            },
                            "format": {
                                "type": "boolean",
                                "description": "Whether to also format the Python files using ruff. Defaults to true.",
                            },
                            "fix": {
                                "type": "boolean",
                                "description": "Whether to auto-fix linting issues that can be fixed automatically. Defaults to true.",
                            },
                            "ignore": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of lint error codes to ignore (e.g., ['F405', 'E501']).",
                            },
                        },
                        "required": ["directory"],
                    },
                },
            }
        ]

    def get_functions(self) -> dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "lint_python": self._tool_lint_python,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for Python lint tools."""
        return """
### Python Lint Tools
1. **lint_python** - Lint, auto-fix, and format Python files under a directory using ruff

### Lint Tool Examples

**Lint, auto-fix, and format all Python files in the current directory:**
> Use lint_python with directory="."

**Lint, auto-fix, and format Python files in a specific folder:**
> Use lint_python with directory="src/mypackage"

**Lint only without formatting or auto-fix:**
> Use lint_python with directory="src/mypackage", format=false, fix=false

**Lint while ignoring specific error codes:**
> Use lint_python with directory="src/mypackage", ignore=["F405", "E501"]
"""

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _json_success(
        self,
        issues: list[dict],
        directory: str,
        file_count: int,
        formatted: bool = False,
        fixed: bool = False,
    ) -> str:
        """Create a JSON success response."""
        response = {
            "success": True,
            "directory": directory,
            "files_checked": file_count,
            "formatted": formatted,
            "fixed": fixed,
            "issue_count": len(issues),
            "issues": issues,
        }
        return json.dumps(response, indent=2)

    def _tool_lint_python(
        self,
        directory: str,
        format: bool = True,
        fix: bool = True,
        ignore: list[str] | None = None,
    ) -> str:
        """
        Implementation of the lint_python tool.
        Lints and optionally formats/fixes Python files under a directory using ruff.

        Args:
            directory: The directory path to lint
            format: Whether to also format the files (default True)
            fix: Whether to auto-fix linting issues (default True)
            ignore: List of error codes to ignore (e.g., ["F405", "E501"])

        Returns:
            JSON string with lint results or error message
        """
        try:
            # Validate directory parameter
            if not directory or not isinstance(directory, str):
                return self._json_error("Directory must be a non-empty string")

            directory = directory.strip()
            if not directory:
                return self._json_error("Directory cannot be empty")

            # Convert to Path and validate
            dir_path = Path(directory)
            if not dir_path.exists():
                return self._json_error(f"Directory does not exist: {directory}")

            if not dir_path.is_dir():
                return self._json_error(f"Path is not a directory: {directory}")

            # Build exclude args for ruff
            exclude_args = []
            if self.exclude_dirs:
                exclude_args = ["--exclude", ",".join(self.exclude_dirs)]

            # Count Python files (excluding configured dirs)
            excluded = set(self.exclude_dirs)
            python_files = [
                f for f in dir_path.rglob("*.py") if not any(part in excluded for part in f.relative_to(dir_path).parts)
            ]
            file_count = len(python_files)

            if file_count == 0:
                return self._json_success([], directory, 0, formatted=False, fixed=False)

            # Run ruff format if enabled
            formatted = False
            if format:
                subprocess.run(
                    ["ruff", "format", *exclude_args, str(dir_path)],
                    capture_output=True,
                    text=True,
                    **_SUBPROCESS_FLAGS,
                )
                formatted = True

            # Build ruff check command with JSON output
            check_cmd = ["ruff", "check", "--output-format=json", *exclude_args]
            if fix:
                check_cmd.append("--fix")
            if ignore:
                check_cmd.extend(["--ignore", ",".join(ignore)])
            check_cmd.append(str(dir_path))

            # Run ruff check (with optional --fix) and get JSON output
            result = subprocess.run(check_cmd, capture_output=True, text=True, **_SUBPROCESS_FLAGS)
            fixed = fix

            # Parse ruff JSON output
            issues = []
            if result.stdout.strip():
                ruff_output = json.loads(result.stdout)
                for item in ruff_output:
                    issues.append(
                        {
                            "file": item.get("filename", ""),
                            "line": item.get("location", {}).get("row", 0),
                            "column": item.get("location", {}).get("column", 0),
                            "code": item.get("code", ""),
                            "message": item.get("message", ""),
                        }
                    )

            return self._json_success(issues, directory, file_count, formatted=formatted, fixed=fixed)

        except FileNotFoundError:
            return self._json_error("ruff is not installed. Install it with: pip install ruff")
        except json.JSONDecodeError as e:
            return self._json_error(f"Failed to parse ruff output: {str(e)}")
        except Exception as e:
            return self._json_error(f"Error running lint: {str(e)}")
