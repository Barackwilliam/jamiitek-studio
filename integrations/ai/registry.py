from django.conf import settings

from . import ProviderNotConfigured
from .openai_compatible import OpenAICompatibleProvider


def text_provider_is_configured():
    return bool(settings.AI_TEXT_BASE_URL and settings.AI_TEXT_API_KEY and settings.AI_TEXT_MODEL)


def get_text_provider():
    """Return the configured text provider, or raise ProviderNotConfigured."""
    if not text_provider_is_configured():
        raise ProviderNotConfigured()
    return OpenAICompatibleProvider(
        name=settings.AI_TEXT_PROVIDER_NAME,
        base_url=settings.AI_TEXT_BASE_URL,
        api_key=settings.AI_TEXT_API_KEY,
        model=settings.AI_TEXT_MODEL,
        timeout=settings.AI_TEXT_TIMEOUT,
        json_mode=settings.AI_TEXT_JSON_MODE,
        reasoning_effort=settings.AI_TEXT_REASONING_EFFORT,
    )
