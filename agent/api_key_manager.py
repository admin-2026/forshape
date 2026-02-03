"""
API Key management for ForShape AI.

This module handles secure storage and retrieval of API keys using the system keyring.
"""

from typing import Optional

# Keyring service name for storing API keys
KEYRING_SERVICE = "ForShape_AI"

# Known AI providers
KNOWN_PROVIDERS = ["openai", "fireworks", "anthropic"]


class ApiKeyManager:
    """Manages API keys using the system keyring for secure storage."""

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get the API key for a specific provider from the system keyring.

        Args:
            provider: Provider name ("openai", "fireworks", etc.)

        Returns:
            The API key if found, None otherwise
        """
        try:
            import keyring

            return keyring.get_password(KEYRING_SERVICE, provider.lower())
        except Exception as e:
            print(f"Error reading {provider} key from keyring: {e}")
            return None

    def set_api_key(self, provider: str, api_key: str):
        """
        Store an API key for a specific provider in the system keyring.

        Args:
            provider: Provider name ("openai", "fireworks", etc.)
            api_key: The API key to store
        """
        try:
            import keyring

            keyring.set_password(KEYRING_SERVICE, provider.lower(), api_key)
            print(f"Provider API key updated: {provider}")
        except Exception as e:
            print(f"Error updating keyring for {provider}: {e}")

    def delete_api_key(self, provider: str):
        """
        Delete an API key for a specific provider from the system keyring.

        Args:
            provider: Provider name ("openai", "fireworks", etc.)
        """
        try:
            import keyring

            keyring.delete_password(KEYRING_SERVICE, provider.lower())
            print(f"Provider API key removed: {provider}")
        except Exception as e:
            # Check if it's a PasswordDeleteError (key didn't exist)
            if "PasswordDeleteError" in type(e).__name__:
                pass
            else:
                print(f"Error deleting keyring entry for {provider}: {e}")

    def get_all_api_keys(self) -> dict:
        """
        Get all API keys for known providers.

        Returns:
            Dict mapping provider names to API keys
        """
        providers = {}
        for provider in KNOWN_PROVIDERS:
            api_key = self.get_api_key(provider)
            if api_key:
                providers[provider] = api_key
        return providers
