"""Provider registry with Gemini/Mock fallback."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from providers.exceptions import ProviderError
from providers.gemini.gemini_flash import GeminiFlashProvider
from providers.gemini.gemini_pro import GeminiProProvider
from providers.mock.provider import MockFlashProvider, MockProProvider, MockProvider


@dataclass(frozen=True)
class GeminiProvider:
    flash: GeminiFlashProvider
    pro: GeminiProProvider


def _api_key_present() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY", "").strip())


def create_providers() -> GeminiProvider | MockProvider:
    """Return Gemini providers when GOOGLE_API_KEY is set, otherwise MockProvider."""
    if _api_key_present():
        return GeminiProvider(flash=GeminiFlashProvider(), pro=GeminiProProvider())
    return MockProvider()


@lru_cache(maxsize=1)
def get_provider_bundle() -> GeminiProvider | MockProvider:
    return create_providers()


def get_claim_observer() -> GeminiFlashProvider | MockFlashProvider:
    bundle = get_provider_bundle()
    return bundle.flash


def get_image_observer() -> GeminiProProvider | MockProProvider:
    bundle = get_provider_bundle()
    return bundle.pro


def reset_provider_cache() -> None:
    get_provider_bundle.cache_clear()


def require_gemini_provider() -> GeminiProvider:
    bundle = get_provider_bundle()
    if not isinstance(bundle, GeminiProvider):
        raise ProviderError("GOOGLE_API_KEY is not configured; GeminiProvider unavailable")
    return bundle
