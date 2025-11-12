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

    def load_system_message(self, include_agent_tools: bool = False) -> str:
        """
        Load the system message from shapes/README.md.

        Args:
            include_agent_tools: If True, includes instructions about file management tools

        Returns:
            System message content, or default message if file not found
        """
        try:
            if os.path.exists(self.readme_path):
                with open(self.readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                base_message = f"You are an AI assistant helping users create and manipulate 3D shapes using provided Python APIs. Below is the complete API documentation:\n\n{content}\n\nAvoid inserting dangerous Python code into the generated Python script."
            else:
                base_message = "You are an AI assistant helping users create and manipulate 3D shapes using provided Python APIs. Avoid inserting dangerous Python code into the generated Python script."

            # Add agent tool instructions if requested
            if include_agent_tools:
                agent_instructions = """

## File Management Capabilities

You have access to file management tools that allow you to:

1. **list_files** - List files and directories in any folder
2. **read_file** - Read the contents of any file
3. **edit_file** - Edit files by replacing content

### Working with Generated Scripts

When users ask you to generate or modify Python scripts for shapes:
1. You can use your tools to **directly update the generated script files**
2. You can read existing scripts to understand what's already been created
3. You can edit scripts to fix issues, add features, or improve code
4. Scripts are typically stored in the working directory or shapes folder

### Best Practices

- When a user reports an error in a generated script, **read the script first** to understand the issue
- After generating new code, you can **directly write or edit the script file** instead of just showing code
- Use **list_files** to explore the project structure when needed
- Always verify changes by reading the file after editing

### Example Workflows

**User says: "Add a red sphere to the scene"**
→ Generate the code and either tell the user to save it, OR directly edit their current script file

**User says: "The script has an error on line 15"**
→ Read the script file, identify the issue, edit the file to fix it, confirm the fix

**User says: "What scripts have I created?"**
→ List files in the working directory to show them their generated scripts

Use these tools proactively to provide a better user experience!"""
                base_message += agent_instructions

            return base_message
        except Exception as e:
            print(f"Warning: Could not load README.md: {e}")
            base_msg = "You are an AI assistant helping users create and manipulate 3D shapes using provided Python APIs. Avoid inserting dangerous Python code into the generated Python script."
            if include_agent_tools:
                base_msg += "\n\nYou have access to file management tools (list_files, read_file, edit_file) to help users manage their generated scripts."
            return base_msg

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

    def get_context(self, include_agent_tools: bool = False) -> Tuple[str, Optional[str]]:
        """
        Get both system message and user context.

        Args:
            include_agent_tools: If True, includes file management tool instructions

        Returns:
            Tuple of (system_message, forshape_context)
            - system_message: Always returns a string (from README.md or default)
            - forshape_context: None if FORSHAPE.md doesn't exist
        """
        system_message = self.load_system_message(include_agent_tools=include_agent_tools)
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
