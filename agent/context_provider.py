"""
Context provider for ForShape AI GUI.

This module provides raw data for AI interactions by loading:
- API documentation from shapes/README.md
- File paths for context files
"""

import os
from typing import Optional


class ContextProvider:
    """Provides raw data and file paths for AI request building."""

    def __init__(self, shapes_dir: Optional[str] = None):
        """
        Initialize the context provider.

        Args:
            shapes_dir: Path to shapes directory (defaults to ../shapes relative to this file)
        """
        if shapes_dir is None:
            # Get the directory of this file and go up one level to find shapes
            current_dir = os.path.dirname(os.path.abspath(__file__))
            shapes_dir = os.path.join(os.path.dirname(current_dir), "shapes")

        self.shapes_dir = shapes_dir
        self.working_dir = os.getcwd()
        self.project_dir = os.path.dirname(self.shapes_dir)  # Parent of shapes_dir
        self.readme_path = os.path.join(self.shapes_dir, "README.md")
        self.forshape_path = os.path.join(self.working_dir, "FORSHAPE.md")

    def has_forshape(self) -> bool:
        """
        Check if FORSHAPE.md exists in the working directory.

        Returns:
            True if FORSHAPE.md exists, False otherwise
        """
        return os.path.exists(self.forshape_path)

    def get_readme_path(self) -> str:
        """Get the path to the README.md file."""
        return self.readme_path

    def get_forshape_path(self) -> str:
        """Get the path to the FORSHAPE.md file."""
        return self.forshape_path

    def get_project_dir(self) -> str:
        """Get the path to the forshape project directory."""
        return self.project_dir
