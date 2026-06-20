"""Tests for mock providers."""

from __future__ import annotations

from contracts.enums import ClaimStatus, IssueType, ObjectPart
from providers.mock.provider import MockProvider
from tests.conftest import NOW, make_claim_context


def test_mock_flash_returns_claim_observation():
    claim = make_claim_context()
    observation = MockProvider().flash.observe_claim(claim, observed_at=NOW)
    assert observation.row_id == claim.row_id
    assert observation.alleged_parts
    assert observation.alleged_issue_types
    assert observation.sanitized_claim_excerpt
    assert observation.model_name.startswith("mock-")


def test_mock_flash_detects_hinglish():
    claim = make_claim_context(
        claim_object=make_claim_context().claim_object,
    )
    claim = claim.model_copy(
        update={
            "user_claim": "Customer: Parking lot mein meri car ko scrape lag gaya.",
        }
    )
    observation = MockProvider().flash.observe_claim(claim, observed_at=NOW)
    assert observation.detected_languages == ["hi"]


def test_mock_flash_does_not_emit_verdict_fields():
    claim = make_claim_context()
    observation = MockProvider().flash.observe_claim(claim, observed_at=NOW)
    dumped = observation.model_dump()
    for forbidden in (
        "claim_status",
        "evidence_standard_met",
        "severity",
        "risk_flags",
        "supported",
        "contradicted",
        "not_enough_information",
    ):
        assert forbidden not in dumped


def test_mock_pro_returns_image_evidence(tmp_path):
    image_path = tmp_path / "img_1.jpg"
    image_path.write_bytes(b"fake-image")
    claim = make_claim_context()
    claim = claim.model_copy(
        update={
            "image_paths": [str(image_path)],
            "resolved_image_files": [str(image_path)],
        }
    )
    evidence = MockProvider().pro.observe_image(
        claim,
        image_id="img_1",
        image_path=str(image_path),
        observed_at=NOW,
    )
    assert evidence.image_id == "img_1"
    assert evidence.file_readable is True
    assert evidence.visible_part.value in ObjectPart
    assert evidence.visible_issue_type.value in IssueType


def test_mock_pro_does_not_emit_verdict_fields(tmp_path):
    image_path = tmp_path / "img_1.jpg"
    image_path.write_bytes(b"fake-image")
    claim = make_claim_context()
    claim = claim.model_copy(
        update={
            "image_paths": [str(image_path)],
            "resolved_image_files": [str(image_path)],
        }
    )
    evidence = MockProvider().pro.observe_image(
        claim,
        image_id="img_1",
        image_path=str(image_path),
        observed_at=NOW,
    )
    dumped = evidence.model_dump()
    assert ClaimStatus.SUPPORTED.value not in str(dumped)
    assert "claim_status" not in dumped
    assert "risk_flags" not in dumped
