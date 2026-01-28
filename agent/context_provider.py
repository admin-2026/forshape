"""
Context provider for ForShape AI GUI.

This module provides raw data for AI interactions by loading:
- API documentation from shapes/README.md
- Current FreeCAD document structure
- File paths for context files
"""

import os
import sys
from io import StringIO
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

    def get_document_structure(self) -> Optional[str]:
        """
        Get the current FreeCAD document structure using Context.print_document().

        Returns:
            String representation of the document structure, or None if unavailable
        """
        try:
            # Import Context class
            sys.path.insert(0, self.shapes_dir)
            from context import Context
            import FreeCAD as App

            # Check if there's an active document
            if App.ActiveDocument is None:
                return None

            # Capture the output of Context.print_document()
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                Context.print_document()
                output = sys.stdout.getvalue()
            finally:
                sys.stdout = old_stdout

            return output if output.strip() else None

        except Exception as e:
            print(f"Warning: Could not get document structure: {e}")
            return None

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
