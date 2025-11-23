"""
API Provider abstraction layer.

This module provides a base class for API providers and concrete implementations
for OpenAI and Fireworks API providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class APIProvider(ABC):
    """
    Abstract base class for AI API providers.

    This class defines the interface that all API providers must implement
    to work with the AI agent system.
    """

    def __init__(self, api_key: Optional[str], **kwargs):
        """
        Initialize the API provider.

        Args:
            api_key: API key for authentication
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    def create_completion(
        self,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Any:
        """
        Create a chat completion.

        Args:
            model: Model identifier
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            tool_choice: Tool choice strategy ("auto", "none", or specific tool)
            **kwargs: Additional provider-specific parameters

        Returns:
            API response object
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and ready to use.

        Returns:
            True if provider is initialized and ready, False otherwise
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the provider.

        Returns:
            Provider name string
        """
        pass


class OpenAIProvider(APIProvider):
    """OpenAI API provider implementation."""

    def __init__(self, api_key: Optional[str], **kwargs):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key
            **kwargs: Additional configuration (e.g., base_url, organization)
        """
        super().__init__(api_key, **kwargs)
        self.client = self._initialize_client()

    def _initialize_client(self):
        """
        Initialize the OpenAI client.

        Returns:
            OpenAI client instance or None if initialization fails
        """
        if not self.api_key:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            print("Error: OpenAI library not available")
            return None

        try:
            # Extract OpenAI-specific config
            client_kwargs = {"api_key": self.api_key}
            if "base_url" in self.config:
                client_kwargs["base_url"] = self.config["base_url"]
            if "organization" in self.config:
                client_kwargs["organization"] = self.config["organization"]

            return OpenAI(**client_kwargs)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            return None

    def create_completion(
        self,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Any:
        """
        Create a chat completion using OpenAI API.

        Args:
            model: Model identifier (e.g., "gpt-4", "gpt-3.5-turbo")
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            tool_choice: Tool choice strategy
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            OpenAI ChatCompletion object
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        params = {
            "model": model,
            "messages": messages,
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        # Add any additional parameters
        params.update(kwargs)

        return self.client.chat.completions.create(**params)

    def is_available(self) -> bool:
        """
        Check if OpenAI provider is available.

        Returns:
            True if client is initialized, False otherwise
        """
        return self.client is not None

    def get_provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            "OpenAI"
        """
        return "OpenAI"


class FireworksProvider(APIProvider):
    """Fireworks AI API provider implementation."""

    def __init__(self, api_key: Optional[str], **kwargs):
        """
        Initialize the Fireworks provider.

        Args:
            api_key: Fireworks API key
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.client = self._initialize_client()

    def _initialize_client(self):
        """
        Initialize the Fireworks client (using OpenAI-compatible interface).

        Returns:
            OpenAI client instance configured for Fireworks or None if initialization fails
        """
        if not self.api_key:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            print("Error: OpenAI library not available (required for Fireworks compatibility)")
            return None

        try:
            # Fireworks API is OpenAI-compatible, just use a different base URL
            return OpenAI(
                api_key=self.api_key,
                base_url="https://api.fireworks.ai/inference/v1"
            )
        except Exception as e:
            print(f"Error initializing Fireworks client: {e}")
            return None

    def create_completion(
        self,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Any:
        """
        Create a chat completion using Fireworks API.

        Args:
            model: Model identifier (e.g., "accounts/fireworks/models/llama-v3p1-8b-instruct")
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            tool_choice: Tool choice strategy
            **kwargs: Additional Fireworks-specific parameters

        Returns:
            ChatCompletion object (OpenAI-compatible)
        """
        if not self.client:
            raise RuntimeError("Fireworks client not initialized")

        params = {
            "model": model,
            "messages": messages,
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        # Add any additional parameters
        params.update(kwargs)

        return self.client.chat.completions.create(**params)

    def is_available(self) -> bool:
        """
        Check if Fireworks provider is available.

        Returns:
            True if client is initialized, False otherwise
        """
        return self.client is not None

    def get_provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            "Fireworks"
        """
        return "Fireworks"


# Factory function to create API providers
def create_api_provider(provider_name: str, api_key: Optional[str], **kwargs) -> APIProvider:
    """
    Create an API provider instance.

    Args:
        provider_name: Name of the provider ("openai" or "fireworks")
        api_key: API key for authentication
        **kwargs: Additional provider-specific configuration

    Returns:
        APIProvider instance

    Raises:
        ValueError: If provider_name is not supported
    """
    provider_name = provider_name.lower()

    if provider_name == "openai":
        return OpenAIProvider(api_key, **kwargs)
    elif provider_name == "fireworks":
        return FireworksProvider(api_key, **kwargs)
    else:
        raise ValueError(f"Unsupported API provider: {provider_name}")
