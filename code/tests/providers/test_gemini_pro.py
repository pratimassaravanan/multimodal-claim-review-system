"""Tests for Gemini Pro provider with mocked HTTP client."""

from __future__ import annotations

import json

import pytest

from contracts.enums import DamageExtent

from providers.exceptions import ForbiddenProviderOutputError
from providers.gemini._client import GeminiClient
from providers.gemini.gemini_pro import GeminiProProvider
from tests.conftest import NOW, make_claim_context


def _pro_payload(**overrides):
    payload = {
        "file_readable": True,
        "usable_for_automated_review": True,
        "depicts_claim_object": {"value": True, "confidence": "high"},
        "visible_part": {"value": "rear_bumper", "confidence": "high"},
        "claimed_primary_part_visible": {"value": True, "confidence": "high"},
        "visible_issue_type": {"value": "dent", "confidence": "high"},
        "visible_damage_extent": {"value": "medium", "confidence": "high"},
        "is_blurry": {"value": False, "confidence": "low"},
        "is_cropped_or_obstructed": {"value": False, "confidence": "low"},
        "is_low_light_or_glare": {"value": False, "confidence": "low"},
        "is_wrong_angle_for_claimed_part": {"value": False, "confidence": "low"},
        "is_non_original_image": {"value": False, "confidence": "low"},
        "is_possibly_manipulated": {"value": False, "confidence": "low"},
        "has_instruction_text": {"value": False, "confidence": "low"},
        "package_is_opened": {"value": False, "confidence": "low"},
        "contents_area_visible": {"value": False, "confidence": "low"},
        "vehicle_identity_features": [],
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


def test_gemini_pro_maps_to_image_evidence(tmp_path):
    image_path = tmp_path / "img_1.jpg"
    image_path.write_bytes(b"fake-image")
    claim = make_claim_context()
    claim = claim.model_copy(
        update={
            "image_paths": [str(image_path)],
            "resolved_image_files": [str(image_path)],
        }
    )
    provider = GeminiProProvider(client=_StubGeminiClient(json.dumps(_pro_payload())))
    evidence = provider.observe_image(
        claim,
        image_id="img_1",
        image_path=str(image_path),
        observed_at=NOW,
    )
    assert evidence.image_id == "img_1"
    assert evidence.visible_damage_extent.value is DamageExtent.MEDIUM
    assert evidence.model_name == "gemini-2.5-pro"


def test_gemini_pro_rejects_forbidden_fields(tmp_path):
    image_path = tmp_path / "img_1.jpg"
    image_path.write_bytes(b"fake-image")
    claim = make_claim_context()
    claim = claim.model_copy(
        update={
            "image_paths": [str(image_path)],
            "resolved_image_files": [str(image_path)],
        }
    )
    provider = GeminiProProvider(
        client=_StubGeminiClient(json.dumps(_pro_payload(not_enough_information=True)))
    )
    with pytest.raises(ForbiddenProviderOutputError):
        provider.observe_image(
            claim,
            image_id="img_1",
            image_path=str(image_path),
            observed_at=NOW,
        )


def test_gemini_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(Exception):
        GeminiClient()
