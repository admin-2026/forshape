"""
Configuration management for ForShape AI.

This module handles directory setup, application configuration, and provides
context for AI interactions including paths to documentation and project files.
"""

import os
from pathlib import Path
from typing import Optional


class ConfigurationManager:
    """Manages configuration, directories, and context for ForShape AI."""

    # Folder name for ForShape internal files
    FORSHAPE_FOLDER_NAME = ".forshape"

    def __init__(self, shapes_dir: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            shapes_dir: Path to shapes directory (defaults to ../shapes relative to install dir)
        """
        self.install_dir = Path(__file__).parent.parent
        self.provider_config_file = self.install_dir / "provider-config.json"
        # libs is at project root, not in gui folder
        self.libs_dir = self.install_dir / "libs"

        # Setup shapes directory and project directory
        if shapes_dir is None:
            self.shapes_dir = self.install_dir / "shapes"
        else:
            self.shapes_dir = Path(shapes_dir)

        self.project_dir = self.shapes_dir.parent
        self.readme_path = self.shapes_dir / "README.md"

        # Initialize working directory paths
        self.working_dir = os.getcwd()
        self._setup_paths(self.working_dir)

    def _setup_paths(self, working_directory: str):
        """
        Setup all directory paths based on the working directory.

        Args:
            working_directory: The working directory path
        """
        self.working_dir = working_directory
        self.base_dir = Path(working_directory)
        self.forshape_dir = self.base_dir / self.FORSHAPE_FOLDER_NAME
        self.history_dir = self.forshape_dir / "history"
        self.edits_dir = self.forshape_dir / "edits"
        self.api_dumps_dir = self.forshape_dir / "api_dumps"
        self.history_dumps_dir = self.forshape_dir / "history_dumps"
        self.forshape_md_file = self.base_dir / "FORSHAPE.md"

    def setup_directories(self) -> list[str]:
        """
        Setup .forshape and .forshape/history directories if they don't exist.

        Returns:
            List of messages describing what was created
        """
        created_items = []

        if not self.forshape_dir.exists():
            self.forshape_dir.mkdir(parents=True, exist_ok=True)
            created_items.append(f"📁 Created directory: `{self.forshape_dir}`")

        if not self.history_dir.exists():
            self.history_dir.mkdir(parents=True, exist_ok=True)
            created_items.append(f"📁 Created directory: `{self.history_dir}`")

        if not self.edits_dir.exists():
            self.edits_dir.mkdir(parents=True, exist_ok=True)
            created_items.append(f"📁 Created directory: `{self.edits_dir}`")

        # Create default FORSHAPE.md if it doesn't exist
        if not self.forshape_md_file.exists():
            self._create_default_forshape_md()
            created_items.append(f"📄 Created file: `{self.forshape_md_file}`")

        return created_items

    def get_base_dir(self) -> Path:
        """Get the base directory."""
        return self.base_dir

    def get_forshape_dir(self) -> Path:
        """Get the .forshape directory."""
        return self.forshape_dir

    def get_history_dir(self) -> Path:
        """Get the history directory."""
        return self.history_dir

    def get_edits_dir(self) -> Path:
        """Get the edits directory."""
        return self.edits_dir

    def get_libs_dir(self) -> Path:
        """Get the local libs directory."""
        return self.libs_dir

    def get_api_dumps_dir(self) -> Path:
        """Get the API dumps directory."""
        return self.api_dumps_dir

    def get_history_dumps_dir(self) -> Path:
        """Get the history dumps directory."""
        return self.history_dumps_dir

    def get_forshape_md_file(self) -> Path:
        """Get the FORSHAPE.md file path."""
        return self.forshape_md_file

    def get_forshape_folder_name(self) -> str:
        """Get the ForShape folder name (e.g., '.forshape')."""
        return self.FORSHAPE_FOLDER_NAME

    def has_forshape_md(self) -> bool:
        """Check if FORSHAPE.md exists."""
        return self.forshape_md_file.exists()

    def has_forshape(self) -> bool:
        """Check if FORSHAPE.md exists (alias for has_forshape_md)."""
        return self.forshape_md_file.exists()

    def get_readme_path(self) -> Path:
        """Get the path to the API documentation README.md file."""
        return self.readme_path

    def get_forshape_path(self) -> Path:
        """Get the path to FORSHAPE.md (alias for get_forshape_md_file)."""
        return self.forshape_md_file

    def get_review_path(self) -> Path:
        """Get the path to REVIEW.md (user-provided review instructions)."""
        return self.base_dir / "REVIEW.md"

    def get_project_dir(self) -> Path:
        """Get the ForShape project directory (parent of shapes dir)."""
        return self.project_dir

    def _create_default_forshape_md(self):
        """Create a default FORSHAPE.md template file."""
        default_content = """
# Add any additional notes or context that would help the AI understand your project better.
"""
        try:
            with open(self.forshape_md_file, "w", encoding="utf-8") as f:
                f.write(default_content)
        except Exception as e:
            print(f"Error creating default FORSHAPE.md: {e}")

    def update_working_directory(self, new_directory: str):
        """
        Update the working directory and recalculate all configuration paths.

        Args:
            new_directory: The new working directory path
        """
        self._setup_paths(new_directory)
