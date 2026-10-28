import io
import json
import urllib.error

from django.test import SimpleTestCase, override_settings

from integrations.ai import (
    ProviderAuthError,
    ProviderBadResponse,
    ProviderNotConfigured,
    ProviderRateLimited,
    ProviderSetupError,
    ProviderUnavailable,
    TextGenerationRequest,
)
from integrations.ai.openai_compatible import OpenAICompatibleProvider
from integrations.ai.registry import get_text_provider, text_provider_is_configured

SECRET_KEY = "sk-test-secret-123"


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class FakeOpener:
    """Returns queued outcomes: bytes/dict bodies or exceptions."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, dict):
            outcome = json.dumps(outcome).encode()
        return FakeResponse(outcome)


def completion(content='{"ok": true}', finish_reason="stop"):
    return {"model": "test-model-001",
            "choices": [{"message": {"content": content}, "finish_reason": finish_reason}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "note": "ignored"}}


def http_error(status, body=b""):
    return urllib.error.HTTPError("https://ai.example/v1/chat/completions", status, "error", {},
                                  io.BytesIO(body))


def provider(opener, **kwargs):
    return OpenAICompatibleProvider(
        name="Test AI", base_url="https://ai.example/v1/", api_key=SECRET_KEY, model="test-model",
        opener=opener, sleep=lambda s: None, **kwargs)


REQUEST = TextGenerationRequest(system_prompt="system", user_prompt="user")


class OpenAICompatibleProviderTests(SimpleTestCase):
    def test_successful_request(self):
        opener = FakeOpener(completion())

        result = provider(opener).generate(REQUEST)

        self.assertEqual(result.text, '{"ok": true}')
        self.assertEqual(result.model, "test-model-001")
        self.assertEqual(result.usage, {"prompt_tokens": 100, "completion_tokens": 20})
        request, timeout = opener.requests[0]
        self.assertEqual(request.full_url, "https://ai.example/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), f"Bearer {SECRET_KEY}")
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "system"})
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(timeout, 60.0)

    def test_json_mode_can_be_disabled(self):
        opener = FakeOpener(completion())
        provider(opener, json_mode=False).generate(REQUEST)
        self.assertNotIn("response_format", json.loads(opener.requests[0][0].data))

    def test_error_statuses_map_to_errors(self):
        for status, error in [(401, ProviderAuthError), (403, ProviderAuthError),
                              (429, ProviderRateLimited), (400, ProviderBadResponse),
                              (404, ProviderSetupError)]:
            with self.subTest(status=status), self.assertLogs("integrations.ai", "WARNING"):
                opener = FakeOpener(http_error(status), completion())
                with self.assertRaises(error):
                    provider(opener).generate(REQUEST)
                self.assertEqual(len(opener.requests), 1, "must not retry")

    def test_provider_error_text_is_logged_without_the_key(self):
        body = ('{"error": {"message": "models/old-model is not found for API version v1beta, '
                'key ' + SECRET_KEY + '"}}').encode()
        opener = FakeOpener(http_error(404, body))
        with self.assertLogs("integrations.ai", "WARNING") as logs, self.assertRaises(ProviderSetupError):
            provider(opener).generate(REQUEST)
        output = "\n".join(logs.output)
        self.assertIn("models/old-model is not found", output)
        self.assertNotIn(SECRET_KEY, output)

    def test_server_error_is_retried_once(self):
        opener = FakeOpener(http_error(503), completion())
        with self.assertLogs("integrations.ai", "WARNING"):
            result = provider(opener).generate(REQUEST)
        self.assertEqual(result.text, '{"ok": true}')

        opener = FakeOpener(http_error(500), http_error(502))
        with self.assertLogs("integrations.ai", "WARNING"), self.assertRaises(ProviderUnavailable):
            provider(opener).generate(REQUEST)

    def test_network_failure_and_timeout(self):
        opener = FakeOpener(urllib.error.URLError("no route"), TimeoutError())
        with self.assertLogs("integrations.ai", "WARNING"), self.assertRaises(ProviderUnavailable):
            provider(opener).generate(REQUEST)
        self.assertEqual(len(opener.requests), 2)

    def test_api_key_never_appears_in_logs(self):
        opener = FakeOpener(http_error(401))
        with self.assertLogs("integrations.ai", "WARNING") as logs, self.assertRaises(ProviderAuthError):
            provider(opener).generate(REQUEST)
        self.assertNotIn(SECRET_KEY, "\n".join(logs.output))

    def test_unusable_responses(self):
        for body in [b"not json", {"choices": []}, completion(content=""),
                     completion(content=None), completion(finish_reason="length"),
                     b"x" * 2_000_001]:
            with self.subTest(body=str(body)[:40]), self.assertRaises(ProviderBadResponse):
                provider(FakeOpener(body)).generate(REQUEST)

    def test_user_message_is_safe(self):
        self.assertNotIn("HTTP", ProviderRateLimited("HTTP 429").message)
        self.assertIn("saved", ProviderRateLimited().message)


class RegistryTests(SimpleTestCase):
    @override_settings(AI_TEXT_BASE_URL="", AI_TEXT_API_KEY="", AI_TEXT_MODEL="")
    def test_not_configured(self):
        self.assertFalse(text_provider_is_configured())
        with self.assertRaises(ProviderNotConfigured):
            get_text_provider()

    @override_settings(AI_TEXT_BASE_URL="https://ai.example/v1", AI_TEXT_API_KEY="k",
                       AI_TEXT_MODEL="m", AI_TEXT_PROVIDER_NAME="Example AI")
    def test_configured(self):
        result = get_text_provider()
        self.assertEqual((result.name, result.model), ("Example AI", "m"))
