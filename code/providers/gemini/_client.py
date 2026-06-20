"""Low-level Gemini REST client with retries and timeout."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import ssl
from pathlib import Path
from typing import Any
from urllib import error, request

from providers.common import retry_with_backoff, with_timeout
from providers.exceptions import ProviderError, ProviderResponseError

DEFAULT_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 3


def _gemini_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


_GEMINI_SSL_CONTEXT = _gemini_ssl_context()


class GeminiClient:
    """Minimal Gemini generateContent client using stdlib HTTP."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_base: str = DEFAULT_GEMINI_API_BASE,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self.api_key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
        if not self.api_key:
            raise ProviderError("GOOGLE_API_KEY is required for GeminiClient")
        self.api_base = api_base.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def generate_json(
        self,
        *,
        model: str,
        system_instruction: str,
        user_text: str,
        image_path: str | None = None,
    ) -> str:
        def _call() -> str:
            return with_timeout(
                lambda: self._post_generate_content(
                    model=model,
                    system_instruction=system_instruction,
                    user_text=user_text,
                    image_path=image_path,
                ),
                timeout_seconds=self.timeout_seconds,
            )

        return retry_with_backoff(_call, max_attempts=self.max_retries)

    def _post_generate_content(
        self,
        *,
        model: str,
        system_instruction: str,
        user_text: str,
        image_path: str | None,
    ) -> str:
        parts: list[dict[str, Any]] = [{"text": user_text}]
        if image_path is not None:
            path = Path(image_path)
            if not path.is_file():
                raise ProviderError(f"Image file not found: {image_path}")
            mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            parts.append({"inline_data": {"mime_type": mime_type, "data": encoded}})

        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0,
            },
        }
        url = f"{self.api_base}/models/{model}:generateContent?key={self.api_key}"
        req = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(
                req, timeout=self.timeout_seconds, context=_GEMINI_SSL_CONTEXT
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Gemini HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc

        try:
            return body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(f"Unexpected Gemini response shape: {body}") from exc
