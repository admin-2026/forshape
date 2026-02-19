"""
File diff tool for AI Agent.

This module provides a file diff tool that shows changes made during
the current session, similar to git diff output.
"""

import difflib
import json
from pathlib import Path
from typing import Callable

from ..edit_history import EditHistory
from .base import ToolBase


class FileDiffTools(ToolBase):
    """
    File diff tool using EditHistory.

    Provides a tool to show unified diffs of files changed in the current session.
    """

    def __init__(self, edit_history: EditHistory):
        self.edit_history = edit_history

    def get_definitions(self) -> list[dict]:
        """Get tool definitions in OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "diff_files",
                    "description": (
                        "Show a unified diff of all files changed in the current session, "
                        "similar to git diff. Returns the changes for each modified or created file."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
        ]

    def get_functions(self) -> dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "diff_files": self._tool_diff_files,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for the file diff tool."""
        return """
### File Diff Tools
1. **diff_files** - Show unified diffs of all files changed in the current session (like git diff)

### Diff Tool Examples

**Show all changes made in the current session:**
> Use diff_files
"""

    def _read_lines(self, path: Path | None) -> list[str]:
        """Read file as lines; returns empty list if path is None or file is missing."""
        if path is None or not path.exists():
            return []
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.readlines()
        except Exception:
            return []

    def _tool_diff_files(self) -> str:
        """
        Show unified diffs of files changed in the current session.

        Returns:
            JSON string with list of file diffs
        """
        try:
            file_changes = self.edit_history.get_file_changes()

            if not file_changes:
                return json.dumps({"success": True, "file_count": 0, "files": []}, indent=2)

            files = []
            for change in file_changes:
                file_path = change["file"]
                action = change["action"]
                original_path: Path | None = change["original_path"]
                current_path: Path = change["current_path"]

                original_lines = self._read_lines(original_path)
                current_lines = self._read_lines(current_path)

                diff_lines = list(
                    difflib.unified_diff(
                        original_lines,
                        current_lines,
                        fromfile=f"a/{file_path}",
                        tofile=f"b/{file_path}",
                    )
                )

                files.append(
                    {
                        "file": file_path,
                        "action": action,
                        "diff": "".join(diff_lines) if diff_lines else "(no textual changes)",
                    }
                )

            return json.dumps({"success": True, "file_count": len(files), "files": files}, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error generating diff: {str(e)}"}, indent=2)
