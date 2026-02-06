"""
Python compile tools for AI Agent.

This module provides Python code compilation tools
to check Python files for syntax errors.
"""

import json
import py_compile
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from ..edit_history import EditHistory
from .base import ToolBase

if TYPE_CHECKING:
    from log import Logger


class PythonCompileTools(ToolBase):
    """
    Python compilation tools using py_compile.

    Provides tools to compile Python files and check for syntax errors.
    """

    def __init__(
        self,
        working_dir: str,
        edit_history: Optional[EditHistory] = None,
        logger: Optional["Logger"] = None,
    ):
        """
        Initialize Python compile tools.

        Args:
            working_dir: Working directory for file operations
            edit_history: Optional EditHistory instance for getting changed files
            logger: Optional Logger instance for logging
        """
        self.working_dir = Path(working_dir)
        self.edit_history = edit_history
        self.logger = logger

    def get_definitions(self) -> list[dict]:
        """Get tool definitions in OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "compile_python",
                    "description": "Compile Python files to check for syntax errors. Accepts file paths, glob patterns, or uses EditHistory to get changed files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of Python file paths or glob patterns (e.g., ['main.py', 'src/*.py', '**/*.py']). If not provided and use_edit_history is true, uses changed files from EditHistory.",
                            },
                            "use_edit_history": {
                                "type": "boolean",
                                "description": "If true and no files are provided, compile files from EditHistory's changed files list. Defaults to false.",
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
            "compile_python": self._tool_compile_python,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for Python compile tools."""
        return """
### Python Compile Tools
1. **compile_python** - Compile Python files to check for syntax errors

### Compile Tool Examples

**Compile specific files:**
> Use compile_python with files=["main.py", "utils.py"]

**Compile files matching a glob pattern:**
> Use compile_python with files=["src/**/*.py"]

**Compile all changed files from edit history:**
> Use compile_python with use_edit_history=true
"""

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _json_success(
        self,
        files_compiled: int,
        errors: list[dict],
        files: list[str],
    ) -> str:
        """Create a JSON success response."""
        response = {
            "success": len(errors) == 0,
            "files_compiled": files_compiled,
            "error_count": len(errors),
            "errors": errors,
            "files": files,
        }
        return json.dumps(response, indent=2)

    def _resolve_files(
        self,
        files: Optional[list[str]] = None,
        use_edit_history: bool = False,
    ) -> tuple[list[Path], Optional[str]]:
        """
        Resolve file paths from various input sources.

        Args:
            files: List of file paths or glob patterns
            use_edit_history: Whether to use EditHistory for changed files

        Returns:
            Tuple of (list of resolved file paths, error message or None)
        """
        resolved_files: list[Path] = []

        if files:
            for pattern in files:
                pattern_path = Path(pattern)

                # If pattern is absolute, use it directly
                if pattern_path.is_absolute():
                    if pattern_path.exists() and pattern_path.is_file():
                        resolved_files.append(pattern_path)
                    else:
                        # Try as glob pattern
                        for match in Path(pattern_path.anchor).glob(str(pattern_path.relative_to(pattern_path.anchor))):
                            if match.suffix == ".py" and match.is_file():
                                resolved_files.append(match)
                else:
                    # Relative path - try as direct file first
                    direct_path = self.working_dir / pattern
                    if direct_path.exists() and direct_path.is_file():
                        resolved_files.append(direct_path)
                    else:
                        # Try as glob pattern
                        for match in self.working_dir.glob(pattern):
                            if match.suffix == ".py" and match.is_file():
                                resolved_files.append(match)

        elif use_edit_history:
            if self.edit_history is None:
                return [], "EditHistory is not available"

            changed_files = self.edit_history.get_changed_files()
            for file_path in changed_files:
                full_path = self.working_dir / file_path
                if full_path.exists() and full_path.suffix == ".py":
                    resolved_files.append(full_path)

            if not resolved_files:
                return [], "No Python files found in EditHistory"

        else:
            return [], "No files specified. Provide 'files' or set 'use_edit_history' to true."

        # Remove duplicates while preserving order
        seen: set[Path] = set()
        unique_files: list[Path] = []
        for f in resolved_files:
            resolved = f.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique_files.append(resolved)

        return unique_files, None

    def _tool_compile_python(
        self,
        files: Optional[list[str]] = None,
        use_edit_history: bool = False,
    ) -> str:
        """
        Implementation of the compile_python tool.
        Compiles Python files to check for syntax errors.

        Args:
            files: List of file paths or glob patterns
            use_edit_history: If true, compile files from EditHistory

        Returns:
            JSON string with compilation results or error message
        """
        try:
            # Resolve files
            resolved_files, error = self._resolve_files(files, use_edit_history)
            if error:
                return self._json_error(error)

            if not resolved_files:
                return self._json_error("No Python files found to compile")

            # Compile each file
            errors: list[dict] = []
            compiled_files: list[str] = []

            for file_path in resolved_files:
                # Log resolved files
                if self.logger:
                    self.logger.info(f"compile tool compiling: {file_path}")
                try:
                    # Compile the file (don't create .pyc files)
                    py_compile.compile(str(file_path), doraise=True)
                    compiled_files.append(str(file_path))
                except py_compile.PyCompileError as e:
                    # Log compilation failure
                    if self.logger:
                        self.logger.warning(f"Compilation failed for {file_path}: {e.msg}")
                    # Extract error details
                    error_info = {
                        "file": str(file_path),
                        "message": str(e.msg) if e.msg else "Syntax error",
                    }
                    # Try to extract line number from the exception
                    if hasattr(e, "exc_value") and e.exc_value:
                        exc = e.exc_value
                        if hasattr(exc, "lineno"):
                            error_info["line"] = exc.lineno
                        if hasattr(exc, "offset"):
                            error_info["column"] = exc.offset
                        if hasattr(exc, "text") and exc.text:
                            error_info["text"] = exc.text.rstrip()
                    errors.append(error_info)
                    compiled_files.append(str(file_path))

            return self._json_success(
                files_compiled=len(compiled_files),
                errors=errors,
                files=compiled_files,
            )

        except Exception as e:
            return self._json_error(f"Error during compilation: {str(e)}")

    def compile_files(
        self,
        files: Optional[list[str]] = None,
    ) -> dict:
        """
        Compile Python files and return results as a dictionary.

        This method can be called directly from Python code, not just as an AI tool.

        Args:
            files: List of file paths or glob patterns. If None and edit_history
                   was provided at construction, uses changed files from EditHistory.

        Returns:
            Dictionary with compilation results
        """
        use_edit_history = files is None and self.edit_history is not None
        result = self._tool_compile_python(files=files, use_edit_history=use_edit_history)
        return json.loads(result)
