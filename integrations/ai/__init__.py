"""Text generation providers.

Application code depends only on `TextGenerationProvider` and the errors
below; which provider is used is configuration (DEC-011, DEC-021).
"""

from dataclasses import dataclass, field


def gettext_noop(message):
    """Mark a message for translation without importing Django (see makemessages)."""
    return message


class ProviderError(Exception):
    """Base error. `message` is safe to show users; details stay in the logs."""

    code = "provider_error"
    message = gettext_noop("The AI service could not complete the request. Please try again later.")

    def __init__(self, detail=""):
        super().__init__(detail or self.message)
        self.detail = detail


class ProviderNotConfigured(ProviderError):
    code = "not_configured"
    message = gettext_noop("AI text generation is not set up on this installation yet.")


class ProviderAuthError(ProviderError):
    code = "auth_error"
    message = gettext_noop("The AI service rejected our access key. "
                           "The administrator needs to check the configuration.")


class ProviderSetupError(ProviderError):
    code = "setup_error"
    message = gettext_noop("The AI service did not recognise the model name or address. "
                           "The administrator needs to check AI_TEXT_MODEL and AI_TEXT_BASE_URL.")


class ProviderRateLimited(ProviderError):
    code = "rate_limited"
    message = gettext_noop("The free AI quota has been reached for now. Your work is saved; "
                           "please try again later.")


class ProviderUnavailable(ProviderError):
    code = "unavailable"
    message = gettext_noop("The AI service is not responding right now. "
                           "Your work is saved; please try again later.")


class ProviderBadResponse(ProviderError):
    code = "bad_response"
    message = gettext_noop("The AI service returned an answer we could not use. Please try again.")


@dataclass(frozen=True)
class TextGenerationRequest:
    system_prompt: str
    user_prompt: str
    temperature: float = 0.7
    # Room for the answer plus any "thinking" tokens newer models count here.
    max_output_tokens: int = 4096
    json_output: bool = True


@dataclass(frozen=True)
class TextGenerationResult:
    text: str
    provider: str
    model: str
    usage: dict = field(default_factory=dict)


class TextGenerationProvider:
    name = ""
    model = ""

    def generate(self, request):
        """Return a TextGenerationResult or raise a ProviderError."""
        raise NotImplementedError
