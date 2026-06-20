"""Tests for provider registry fallback."""

from __future__ import annotations

import pytest

from providers.exceptions import ProviderError
from providers.gemini.provider_registry import (
    create_providers,
    get_claim_observer,
    get_image_observer,
    require_gemini_provider,
    reset_provider_cache,
)
from providers.mock.provider import MockProvider


@pytest.fixture(autouse=True)
def clear_provider_cache(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    reset_provider_cache()
    yield
    reset_provider_cache()


def test_create_providers_uses_mock_without_api_key():
    providers = create_providers()
    assert isinstance(providers, MockProvider)


def test_create_providers_uses_gemini_with_api_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    reset_provider_cache()
    providers = create_providers()
    assert providers.__class__.__name__ == "GeminiProvider"


def test_get_observers_return_mock_by_default():
    assert get_claim_observer().__class__.__name__ == "MockFlashProvider"
    assert get_image_observer().__class__.__name__ == "MockProProvider"


def test_require_gemini_provider_raises_without_key():
    with pytest.raises(ProviderError):
        require_gemini_provider()


def test_require_gemini_provider_succeeds_with_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    reset_provider_cache()
    bundle = require_gemini_provider()
    assert bundle.flash.model_name == "gemini-2.5-flash"
    assert bundle.pro.model_name == "gemini-2.5-pro"
