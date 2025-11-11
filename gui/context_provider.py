"""
Context provider for ForShape AI GUI.

This module provides context for AI interactions by loading:
- System message from shapes/README.md
- User context from FORSHAPE.md (if present)
"""

import os
from typing import Optional, Tuple


class ContextProvider:
    """Provides context messages for AI interactions."""

    def __init__(self, shapes_dir: Optional[str] = None, working_dir: Optional[str] = None):
        """
        Initialize the context provider.

        Args:
            shapes_dir: Path to shapes directory (defaults to ../shapes relative to this file)
            working_dir: Working directory to search for FORSHAPE.md (defaults to current working directory)
        """
        if shapes_dir is None:
            # Get the directory of this file and go up one level to find shapes
            current_dir = os.path.dirname(os.path.abspath(__file__))
            shapes_dir = os.path.join(os.path.dirname(current_dir), "shapes")

        if working_dir is None:
            working_dir = os.getcwd()

        self.shapes_dir = shapes_dir
        self.working_dir = working_dir
        self.readme_path = os.path.join(self.shapes_dir, "README.md")
        self.forshape_path = os.path.join(self.working_dir, "FORSHAPE.md")

    def load_system_message(self) -> str:
        """
        Load the system message from shapes/README.md.

        Returns:
            System message content, or default message if file not found
        """
        try:
            if os.path.exists(self.readme_path):
                with open(self.readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return f"You are an AI assistant helping users create and manipulate 3D shapes using provided Python APIs. Below is the complete API documentation:\n\n{content}\n\nAvoid inserting dangerous Python code into the generated Python script."
            else:
                return "You are an AI assistant helping users create and manipulate 3D shapes using provided Python APIs. Avoid inserting dangerous Python code into the generated Python script."
        except Exception as e:
            print(f"Warning: Could not load README.md: {e}")
            return "You are an AI assistant helping users create and manipulate 3D shapes using provided Python APIs. Avoid inserting dangerous Python code into the generated Python script."

    def load_forshape_context(self) -> Optional[str]:
        """
        Load user context from FORSHAPE.md in the working directory.

        Returns:
            FORSHAPE.md content if file exists, None otherwise
        """
        try:
            if os.path.exists(self.forshape_path):
                with open(self.forshape_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content
            return None
        except Exception as e:
            print(f"Warning: Could not load FORSHAPE.md: {e}")
            return None

    def get_context(self) -> Tuple[str, Optional[str]]:
        """
        Get both system message and user context.

        Returns:
            Tuple of (system_message, forshape_context)
            - system_message: Always returns a string (from README.md or default)
            - forshape_context: None if FORSHAPE.md doesn't exist
        """
        system_message = self.load_system_message()
        forshape_context = self.load_forshape_context()
        return system_message, forshape_context

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
