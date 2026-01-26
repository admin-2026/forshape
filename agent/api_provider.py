"""
API Provider abstraction layer.

This module provides a base class for API providers and a generic OpenAI-compatible
provider implementation that works with any OpenAI-compatible API service.
All provider configuration is driven by provider-config.json.
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


class OpenAICompatibleProvider(APIProvider):
    """
    Generic OpenAI-compatible API provider implementation.

    This provider works with any API that follows the OpenAI API interface,
    including OpenAI, Fireworks, DeepSeek, and other compatible services.
    All configuration is driven by the provider-config.json file.
    """

    def __init__(self, api_key: Optional[str], provider_name: str = "OpenAI", **kwargs):
        """
        Initialize the OpenAI-compatible provider.

        Args:
            api_key: API key for authentication
            provider_name: Display name of the provider (e.g., "OpenAI", "Fireworks")
            **kwargs: Additional configuration (e.g., base_url, organization)
        """
        super().__init__(api_key, **kwargs)
        self.provider_name = provider_name
        self.client = self._initialize_client()

    def _initialize_client(self):
        """
        Initialize the OpenAI-compatible client.

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
            # Build client configuration
            client_kwargs = {"api_key": self.api_key}

            # Add base_url if provided (required for non-OpenAI providers)
            if "base_url" in self.config and self.config["base_url"]:
                client_kwargs["base_url"] = self.config["base_url"]

            # Add organization if provided (OpenAI-specific)
            if "organization" in self.config:
                client_kwargs["organization"] = self.config["organization"]

            return OpenAI(**client_kwargs)
        except Exception as e:
            print(f"Error initializing {self.provider_name} client: {e}")
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
        Create a chat completion using the OpenAI-compatible API.

        Args:
            model: Model identifier
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            tool_choice: Tool choice strategy
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatCompletion object
        """
        if not self.client:
            raise RuntimeError(f"{self.provider_name} client not initialized")

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
        Check if the provider is available.

        Returns:
            True if client is initialized, False otherwise
        """
        return self.client is not None

    def get_provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            Provider name string
        """
        return self.provider_name


# Factory function to create API providers
def create_api_provider(provider_name: str, api_key: Optional[str], **kwargs) -> APIProvider:
    """
    Create an API provider instance.

    This is now a simple wrapper that creates an OpenAI-compatible provider
    with the given configuration. All providers are assumed to be OpenAI-compatible.

    Args:
        provider_name: Name of the provider (for display purposes)
        api_key: API key for authentication
        **kwargs: Additional provider-specific configuration (e.g., base_url from config)

    Returns:
        APIProvider instance (OpenAICompatibleProvider)
    """
    # All providers use the OpenAI-compatible interface
    # The provider name is passed for display/logging purposes
    return OpenAICompatibleProvider(api_key, provider_name=provider_name.title(), **kwargs)


def create_api_provider_from_config(provider_config, api_key: Optional[str]) -> APIProvider:
    """
    Create an API provider instance from a ProviderConfig object.

    This function is fully config-driven and selects the appropriate provider class
    based on the provider_class field in the configuration.

    Args:
        provider_config: ProviderConfig object with provider configuration
        api_key: API key for authentication

    Returns:
        APIProvider instance

    Raises:
        ValueError: If provider_class is not supported

    Note:
        To add a new provider, simply add it to provider-config.json with:
        - provider_class: "openai_compatible" for OpenAI-compatible APIs
        - (future) provider_class: "anthropic_native" for Anthropic's API
        - (future) provider_class: "google_gemini" for Google's Gemini API
        No code changes needed for new OpenAI-compatible providers!
    """
    # Build kwargs from config
    kwargs = {}
    if provider_config.base_url:
        kwargs["base_url"] = provider_config.base_url

    # Select provider class based on config
    provider_class_type = provider_config.provider_class

    if provider_class_type == "openai_compatible":
        return OpenAICompatibleProvider(
            api_key,
            provider_name=provider_config.display_name,
            **kwargs
        )
    # Future provider classes can be added here:
    # elif provider_class_type == "anthropic_native":
    #     return AnthropicNativeProvider(api_key, provider_name=provider_config.display_name, **kwargs)
    # elif provider_class_type == "google_gemini":
    #     return GoogleGeminiProvider(api_key, provider_name=provider_config.display_name, **kwargs)
    else:
        raise ValueError(
            f"Unsupported provider class: {provider_class_type}. "
            f"Supported classes: openai_compatible"
        )
