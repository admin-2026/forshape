"""
Provider configuration loader.

This module loads and parses the provider-config.json file that defines
available API providers and their models.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class ProviderConfig:
    """Represents a single provider configuration."""

    def __init__(self, data: Dict):
        """
        Initialize provider config from dictionary.

        Args:
            data: Provider configuration dictionary
        """
        self.name = data.get("name", "")
        self.display_name = data.get("display_name", self.name.capitalize())
        self.provider_class = data.get("provider_class", "openai_compatible")
        self.base_url = data.get("base_url")
        self.default_model = data.get("default_model")
        self.models = [ModelConfig(m) for m in data.get("models", [])]

    def get_model_by_name(self, model_name: str) -> Optional['ModelConfig']:
        """
        Get a model config by its name.

        Args:
            model_name: Model name to search for

        Returns:
            ModelConfig if found, None otherwise
        """
        for model in self.models:
            if model.name == model_name:
                return model
        return None


class ModelConfig:
    """Represents a single model configuration."""

    def __init__(self, data: Dict):
        """
        Initialize model config from dictionary.

        Args:
            data: Model configuration dictionary
        """
        self.name = data.get("name", "")
        self.display_name = data.get("display_name", self.name)


class ProviderConfigLoader:
    """Loader for provider configuration from JSON file."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the provider config loader.

        Args:
            config_path: Optional path to provider-config.json.
                        If not provided, uses default location at project root.
        """
        if config_path is None:
            # Default to provider-config.json at project root (same directory as forshape.py)
            install_dir = Path(__file__).parent.parent
            config_path = install_dir / "provider-config.json"

        self.config_path = config_path
        self.providers: List[ProviderConfig] = []
        self._load_config()

    def _load_config(self):
        """Load and parse the provider configuration file."""
        if not self.config_path.exists():
            print(f"Warning: Provider config not found at {self.config_path}")
            # Use empty config if file doesn't exist
            self.providers = []
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Parse provider configurations
            providers_data = data.get("providers", [])
            self.providers = [ProviderConfig(p) for p in providers_data]

        except json.JSONDecodeError as e:
            print(f"Error parsing provider config: {e}")
            self.providers = []
        except Exception as e:
            print(f"Error loading provider config: {e}")
            self.providers = []

    def get_providers(self) -> List[ProviderConfig]:
        """
        Get all provider configurations.

        Returns:
            List of ProviderConfig objects
        """
        return self.providers

    def get_provider(self, provider_name: str) -> Optional[ProviderConfig]:
        """
        Get a specific provider configuration by name.

        Args:
            provider_name: Name of the provider to get

        Returns:
            ProviderConfig if found, None otherwise
        """
        for provider in self.providers:
            if provider.name == provider_name:
                return provider
        return None

    def get_all_models(self) -> Dict[str, List[ModelConfig]]:
        """
        Get all models organized by provider.

        Returns:
            Dict mapping provider names to lists of ModelConfig objects
        """
        result = {}
        for provider in self.providers:
            result[provider.name] = provider.models
        return result

    def get_default_provider(self) -> Optional[ProviderConfig]:
        """
        Get the default provider (first provider in the list).

        Returns:
            First ProviderConfig if any exist, None otherwise
        """
        return self.providers[0] if self.providers else None
