"""Tests for Gemini Flash provider with mocked HTTP client."""

from __future__ import annotations

import json

import pytest

from providers.exceptions import ForbiddenProviderOutputError
from providers.gemini._client import GeminiClient
from providers.gemini.gemini_flash import GeminiFlashProvider
from tests.conftest import NOW, make_claim_context


def _flash_payload(**overrides):
    payload = {
        "detected_languages": ["en"],
        "sanitized_claim_excerpt": "Customer reports a rear bumper dent.",
        "alleged_parts": ["rear_bumper"],
        "alleged_issue_types": ["dent"],
        "exclusions": [],
        "identity_constraint_active": {"value": False, "confidence": "high"},
        "claimed_damage_alleged": {"value": True, "confidence": "high"},
        "claimed_severity_language": {"value": "medium", "confidence": "medium"},
        "injection_detected_in_chat": False,
    }
    payload.update(overrides)
    return payload


class _StubGeminiClient(GeminiClient):
    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.api_key = "stub"
        self.api_base = "http://example"
        self.timeout_seconds = 1
        self.max_retries = 1

    def generate_json(self, **kwargs) -> str:
        return self._response_text


def test_gemini_flash_maps_to_claim_observation():
    claim = make_claim_context()
    provider = GeminiFlashProvider(client=_StubGeminiClient(json.dumps(_flash_payload())))
    observation = provider.observe_claim(claim, observed_at=NOW)
    assert observation.row_id == claim.row_id
    assert observation.alleged_parts[0].value == "rear_bumper"
    assert observation.alleged_issue_types[0].value == "dent"
    assert observation.model_name == "gemini-2.5-flash"


def test_gemini_flash_rejects_forbidden_fields():
    claim = make_claim_context()
    provider = GeminiFlashProvider(
        client=_StubGeminiClient(json.dumps(_flash_payload(claim_status="supported")))
    )
    with pytest.raises(ForbiddenProviderOutputError):
        provider.observe_claim(claim, observed_at=NOW)


def test_gemini_flash_validates_schema():
    claim = make_claim_context()
    provider = GeminiFlashProvider(client=_StubGeminiClient(json.dumps({"detected_languages": ["en"]})))
    with pytest.raises(Exception):
        provider.observe_claim(claim, observed_at=NOW)
