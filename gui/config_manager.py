"""
Configuration management for ForShape AI.

This module handles directory setup, API key management, and application configuration.
"""

import os
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
        self.api_key_file = self.forshape_dir / "api-key"
        self.provider_config_file = self.forshape_dir / "provider-config"
        self.forshape_md_file = self.base_dir / "FORSHAPE.md"
        # libs is at project root, not in gui folder
        self.libs_dir = Path(__file__).parent.parent / "libs"

    def setup_directories(self):
        """Setup .forshape and .forshape/history directories if they don't exist."""
        if not self.forshape_dir.exists():
            self.forshape_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {self.forshape_dir}")

        if not self.history_dir.exists():
            self.history_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {self.history_dir}")

        # Create default FORSHAPE.md if it doesn't exist
        if not self.forshape_md_file.exists():
            self._create_default_forshape_md()
            print(f"Created instruction file: {self.forshape_md_file}")

    def get_api_key(self) -> Optional[str]:
        """
        Get OpenAI API key from file or environment.

        Returns:
            API key string if found, None otherwise
        """
        api_key = None

        # Try to read API key from file
        if self.api_key_file.exists():
            try:
                with open(self.api_key_file, 'r', encoding='utf-8') as f:
                    api_key = f.read().strip()
            except Exception as e:
                print(f"Error reading API key file: {e}")

        # Fall back to environment variable
        if not api_key:
            api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            self._print_api_key_warning()

        return api_key

    def _print_api_key_warning(self):
        """Print warning message when API key is not found."""
        print("\nWarning: No OpenAI API key found!")
        print(f"Please either:")
        print(f"  1. Save your API key to: {self.api_key_file}")
        print(f"  2. Set the OPENAI_API_KEY environment variable")
        print("\nThe application will run but AI features will not work.\n")

    def get_base_dir(self) -> Path:
        """Get the base directory."""
        return self.base_dir

    def get_forshape_dir(self) -> Path:
        """Get the .forshape directory."""
        return self.forshape_dir

    def get_history_dir(self) -> Path:
        """Get the history directory."""
        return self.history_dir

    def get_api_key_file(self) -> Path:
        """Get the API key file path."""
        return self.api_key_file

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
            Dict with 'provider' and 'api_key' keys
        """
        config = {
            "provider": "openai",  # Default provider
            "api_key": None
        }

        # Try to read provider config from file
        if self.provider_config_file.exists():
            try:
                with open(self.provider_config_file, 'r', encoding='utf-8') as f:
                    lines = f.read().strip().split('\n')
                    for line in lines:
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip().lower()
                            value = value.strip()
                            if key == "provider":
                                config["provider"] = value.lower()
                            elif key == "api_key":
                                config["api_key"] = value
            except Exception as e:
                print(f"Error reading provider config file: {e}")

        # If no API key in provider config, fall back to the legacy api-key file
        if not config["api_key"]:
            config["api_key"] = self.get_api_key()

        return config

    def set_provider_config(self, provider: str, api_key: Optional[str] = None):
        """
        Set the API provider configuration.

        Args:
            provider: Provider name ("openai", "fireworks", etc.)
            api_key: Optional API key (if None, existing key is preserved)
        """
        # Read existing config
        existing_config = self.get_provider_config()

        # Update provider
        existing_config["provider"] = provider.lower()

        # Update API key if provided
        if api_key:
            existing_config["api_key"] = api_key

        # Write config file
        try:
            with open(self.provider_config_file, 'w', encoding='utf-8') as f:
                f.write(f"provider={existing_config['provider']}\n")
                if existing_config["api_key"]:
                    f.write(f"api_key={existing_config['api_key']}\n")
            print(f"Provider configuration updated: {provider}")
        except Exception as e:
            print(f"Error writing provider config file: {e}")
