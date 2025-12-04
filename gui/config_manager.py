"""
Configuration management for ForShape AI.

This module handles directory setup and application configuration.
"""

import os
import json
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .context_provider import ContextProvider


class ConfigurationManager:
    """Manages configuration and directories for ForShape AI."""

    def __init__(self, context_provider: "ContextProvider"):
        """
        Initialize the configuration manager.

        Args:
            context_provider: ContextProvider instance to get working directory from
        """
        self.context_provider = context_provider
        self.base_dir = Path(context_provider.working_dir)
        self.forshape_dir = self.base_dir / ".forshape"
        self.history_dir = self.forshape_dir / "history"
        self.install_dir = Path(__file__).parent.parent
        # Note: provider-config.json is reserved for future provider configuration (NOT for API keys)
        # API keys are managed separately via ApiKeyManager
        self.provider_config_file = self.install_dir / "provider-config.json"
        self.forshape_md_file = self.base_dir / "FORSHAPE.md"
        # libs is at project root, not in gui folder
        self.libs_dir = self.install_dir / "libs"

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

    def get_libs_dir(self) -> Path:
        """Get the local libs directory."""
        return self.libs_dir

    def get_forshape_md_file(self) -> Path:
        """Get the FORSHAPE.md file path."""
        return self.forshape_md_file

    def has_forshape_md(self) -> bool:
        """Check if FORSHAPE.md exists."""
        return self.forshape_md_file.exists()

    def _create_default_forshape_md(self):
        """Create a default FORSHAPE.md template file."""
        default_content = """
# Add any additional notes or context that would help the AI understand your project better.
"""
        try:
            with open(self.forshape_md_file, 'w', encoding='utf-8') as f:
                f.write(default_content)
        except Exception as e:
            print(f"Error creating default FORSHAPE.md: {e}")

    def update_working_directory(self, new_directory: str):
        """
        Update the working directory and recalculate all configuration paths.

        Args:
            new_directory: The new working directory path
        """
        self.base_dir = Path(new_directory)
        self.forshape_dir = self.base_dir / ".forshape"
        self.history_dir = self.forshape_dir / "history"
        self.forshape_md_file = self.base_dir / "FORSHAPE.md"
