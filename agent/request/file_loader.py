"""
File loader utility.

This module provides a FileLoader class for loading file content
with optional required file validation.
"""

from pathlib import Path
from typing import Optional

from .request_element import RequestElement


class FileLoader(RequestElement):
    """Loads file content from a specified path."""

    def __init__(self, file_path: str, required: bool, description: Optional[str] = None):
        """
        Initialize the file loader.

        Args:
            file_path: Path to the file to load
            required: If True, get_content will raise an exception when file doesn't exist
            description: Optional description for this file loader
        """
        super().__init__(description)
        self.file_path = Path(file_path)
        self.required = required

    def get_content(self) -> str:
        """
        Load and return the file content.

        Returns:
            The file content as a string, or empty string if file doesn't exist
            and required is False.

        Raises:
            FileNotFoundError: If the file doesn't exist and required is True.
        """
        if not self.file_path.exists():
            if self.required:
                raise FileNotFoundError(f"Required file not found: {self.file_path}")
            return ""

        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()
