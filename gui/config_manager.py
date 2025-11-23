"""
Configuration management for ForShape AI.

This module handles directory setup, API key management, and application configuration.
"""

import os
import json
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .context_provider import ContextProvider


class ConfigurationManager:
    """Manages configuration, directories, and API keys for ForShape AI."""

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
        self.provider_config_file = self.forshape_dir / "provider-config.json"
        self.forshape_md_file = self.base_dir / "FORSHAPE.md"
        # libs is at project root, not in gui folder
        self.libs_dir = Path(__file__).parent.parent / "libs"

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

    def get_provider_config(self) -> dict:
        """
        Get the API provider configuration.

        Returns:
            Dict with 'providers' (dict mapping provider names to API keys)
        """
        config = {
            "providers": {}  # Dict of provider_name -> api_key
        }

        # Try to read provider config from file
        if self.provider_config_file.exists():
            try:
                with open(self.provider_config_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    data = json.loads(content)
                    config["providers"] = data.get("providers", {})
            except json.JSONDecodeError as e:
                print(f"Error parsing provider-config.json: {e}")
                print("Please ensure the file is valid JSON format.")
            except Exception as e:
                print(f"Error reading provider-config.json: {e}")
        else:
            print("\nWarning: No provider-config.json found!")
            print(f"Please create: {self.provider_config_file}")
            print("Example format:")
            print('{')
            print('  "providers": {')
            print('    "openai": "sk-proj-YOUR_KEY",')
            print('    "fireworks": "fw_YOUR_KEY"')
            print('  }')
            print('}')

        return config

    def set_provider_config(self, provider: str, api_key: Optional[str] = None):
        """
        Update the API provider configuration.

        Args:
            provider: Provider name ("openai", "fireworks", etc.) - only used if api_key is provided
            api_key: Optional API key for the specified provider (if None, no update is performed)
        """
        # Only update if an API key is provided
        if not api_key:
            return

        # Read existing config
        existing_config = self.get_provider_config()

        # Update provider-specific API key
        existing_config["providers"][provider.lower()] = api_key

        # Write config file as JSON
        try:
            config_data = {
                "providers": existing_config["providers"]
            }

            with open(self.provider_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)

            print(f"Provider API key updated: {provider}")
        except Exception as e:
            print(f"Error writing provider-config.json: {e}")

    def update_working_directory(self, new_directory: str):
        """
        Update the working directory and recalculate all configuration paths.

        Args:
            new_directory: The new working directory path
        """
        self.base_dir = Path(new_directory)
        self.forshape_dir = self.base_dir / ".forshape"
        self.history_dir = self.forshape_dir / "history"
        self.provider_config_file = self.forshape_dir / "provider-config.json"
        self.forshape_md_file = self.base_dir / "FORSHAPE.md"
