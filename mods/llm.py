from typing import Dict, Tuple, Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
import logging
import os

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from .utils.logging_config import LoggingConfig

"""
The dictionary is for storing the initialized providers.
The key is the provider name, and the value is a dictionary
where the key is a tuple of (provider_name, api_key, model)
and the value is the provider instance.
"""
INIT_PROVIDERS: Dict[str, Dict[Tuple[str, str, str], BaseChatModel]] = {
    "openai"  : {},
    "claude"  : {},
    "groq"    : {},
    "ollama"  : {},
    "google"  : {},
}

def get_provider_from_cache(provider_name: str, key: Tuple[str, str, str]) -> Optional[BaseChatModel]:
    """
    Retrieves a provider instance from the cache if it exists.
    """
    return INIT_PROVIDERS.get(provider_name, {}).get(key)

def set_provider_in_cache(provider_name: str, key: Tuple[str, str, str], provider: BaseChatModel):
    """
    Stores a provider instance in the cache.
    """
    if provider_name not in INIT_PROVIDERS:
        INIT_PROVIDERS[provider_name] = {}
    INIT_PROVIDERS[provider_name][key] = provider

class AIProviderError(Exception):
    """
    Custom exception for AI provider-related errors.

    Attributes:
        message (str): The error message.
        provider (str): The name of the provider that caused the error.
        model (Optional[str]): The model name, if applicable.
        error (Optional[str]): The original error message, if any.
    """

    def __init__(self, message: str, provider: str, model: Optional[str] = None, error: Optional[str] = None):
        self.message  = message
        self.provider = provider
        self.model    = model
        self.error    = error
        super().__init__(self.message)

class AIRouter:
    """
    A synchronous wrapper around LangChain to manage multiple AI providers. 
    This class provides a simple interface to access different AI providers via LangChain's chat model classes. It caches provider instances to avoid redundant initialization.

    This class provides a simple interface to access different AI providers
    via LangChain's chat model classes. It caches provider instances to avoid
    redundant initialization.
    
    Enhanced with support for memory relevance analysis and contextual scoring
    to improve AI conversation quality through intelligent memory utilization.

    Supported providers:
        - "openai"
        - "claude" (or "anthropic")
        - "groq"
        - "ollama"
        - "google"

    Usage:
        router = AIRouter()
        provider = router.get_provider("openai", "your_api_key", "gpt-3.5-turbo")
        response = provider.invoke([HumanMessage(content="Hello")])
    """

    def __init__(self):
        """
        Initialize the AIRouter with a logger and provider cache.
        """
        self.logger = LoggingConfig.get_logger("ai_router")

    def get_provider(self, provider_name: str, api_key: str, model: str, **kwargs: Any) -> BaseChatModel:
        """
        Get or create a provider instance for the specified provider.

        Args:
            provider_name (str): Name of the AI provider (e.g., "openai", "claude").
            api_key (str): API key for the provider. For providers that do not require
                           an API key (e.g., "ollama"), this can be an empty string.
            model (str): Model name for the provider (e.g., "gpt-3.5-turbo").
            **kwargs: Additional keyword arguments to pass to the provider's constructor,
                      such as temperature, max_tokens, etc.

        Returns:
            BaseChatModel: A LangChain chat model instance for the specified provider.

        Raises:
            ValueError: If an unsupported provider is specified.
            AIProviderError: If provider creation fails for any reason.
        """
        key = (provider_name, api_key, model)

        cached_provider = get_provider_from_cache(provider_name, key)
        if cached_provider:
            self.logger.debug(f"Reusing existing {provider_name} provider for model {model}")
            return cached_provider

        self.logger.debug(f"Creating new {provider_name} provider for model {model}")
        try:
            if provider_name == "openai":
                # Check if Azure OpenAI configuration is provided
                azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                api_version = os.getenv("OPENAI_API_VERSION")

                if azure_endpoint and azure_endpoint.lower() != "none":
                    # Use Azure OpenAI configuration
                    self.logger.debug(f"Using Azure OpenAI endpoint: {azure_endpoint}")
                    provider = ChatOpenAI(
                        model=model,
                        api_key=api_key,
                        base_url=azure_endpoint,
                        api_version=api_version,
                        **kwargs
                    )
                else:
                    # Use regular OpenAI configuration
                    provider = ChatOpenAI(
                        model=model,
                        api_key=api_key,
                        **kwargs
                    )
            elif provider_name in ("claude", "anthropic"):
                provider = ChatAnthropic(
                    model=model,
                    api_key=api_key,
                    **kwargs
                )
            elif provider_name == "groq":
                provider = ChatGroq(
                    model=model,
                    api_key=api_key,
                    **kwargs
                )
            elif provider_name == "ollama":
                provider = ChatOllama(
                    model=model,
                    **kwargs
                )
            elif provider_name == "google":
                provider = ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=api_key,
                    **kwargs
                )
            else:
                raise ValueError(f"Unsupported provider: {provider_name}")

            set_provider_in_cache(provider_name, key, provider)
            return provider

        except Exception as e:
            raise AIProviderError(
                f"Failed to create {provider_name} provider",
                provider_name,
                model,
                error=str(e)
            )

__all__ = ["AIRouter", "AIProviderError"]