from depthmap.config import Settings
from depthmap.providers.anthropic_provider import AnthropicProvider
from depthmap.providers.base import LLMProvider, ProviderError, ProviderRefusal
from depthmap.providers.fake import FakeProvider

__all__ = [
    "AnthropicProvider",
    "FakeProvider",
    "LLMProvider",
    "ProviderError",
    "ProviderRefusal",
    "get_provider",
]


def get_provider(settings: Settings) -> LLMProvider:
    if settings.provider == "fake":
        return FakeProvider()
    key = settings.anthropic_api_key
    return AnthropicProvider(
        model=settings.model,
        api_key=key.get_secret_value() if key else None,
        timeout=settings.timeout,
    )
