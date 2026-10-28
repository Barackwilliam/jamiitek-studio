"""A provider for any service exposing the OpenAI chat completions API.

Google Gemini, Groq and several other services offer this API, so one
adapter covers them; the base URL, key and model come from settings. Only
the standard library is used.
"""

import json
import logging
import socket
import time
import urllib.error
import urllib.request

from . import (
    ProviderAuthError,
    ProviderBadResponse,
    ProviderRateLimited,
    ProviderUnavailable,
    TextGenerationProvider,
    TextGenerationResult,
)

logger = logging.getLogger(__name__)

MAX_RESPONSE_BYTES = 2_000_000


class OpenAICompatibleProvider(TextGenerationProvider):
    def __init__(self, *, name, base_url, api_key, model, timeout=60.0, json_mode=True,
                 retries=1, retry_delay=2.0, opener=None, sleep=time.sleep):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.json_mode = json_mode
        self.retries = retries
        self.retry_delay = retry_delay
        self.opener = opener or urllib.request.build_opener()
        self.sleep = sleep

    def _payload(self, request):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_output_tokens,
        }
        if request.json_output and self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _post(self, payload):
        http_request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with self.opener.open(http_request, timeout=self.timeout) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ProviderBadResponse("response too large")
        return body

    def generate(self, request):
        payload = self._payload(request)
        attempt = 0
        while True:
            try:
                body = self._post(payload)
                break
            except urllib.error.HTTPError as exc:
                status = exc.code
                # Never log the request: it carries the API key header.
                logger.warning("%s returned HTTP %s", self.name, status)
                if status in (401, 403):
                    raise ProviderAuthError(f"HTTP {status}") from exc
                if status == 429:
                    raise ProviderRateLimited(f"HTTP {status}") from exc
                if status >= 500 and attempt < self.retries:
                    attempt += 1
                    self.sleep(self.retry_delay)
                    continue
                if status >= 500:
                    raise ProviderUnavailable(f"HTTP {status}") from exc
                raise ProviderBadResponse(f"HTTP {status}") from exc
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
                logger.warning("%s request failed: %s", self.name, type(exc).__name__)
                if attempt < self.retries:
                    attempt += 1
                    self.sleep(self.retry_delay)
                    continue
                raise ProviderUnavailable(type(exc).__name__) from exc

        try:
            data = json.loads(body)
            choice = data["choices"][0]
            text = choice["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderBadResponse("unexpected response shape") from exc
        if not isinstance(text, str) or not text.strip():
            raise ProviderBadResponse("empty response")
        if choice.get("finish_reason") == "length":
            raise ProviderBadResponse("response cut off at the length limit")

        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return TextGenerationResult(
            text=text,
            provider=self.name,
            model=str(data.get("model") or self.model),
            usage={k: v for k, v in usage.items() if isinstance(v, int)},
        )
