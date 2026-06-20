"""Tests for shared provider utilities."""

from __future__ import annotations

import pytest

from providers.common import (
    assert_no_forbidden_fields,
    parse_json_response,
    retry_with_backoff,
    strip_forbidden_fields,
    validate_json_schema,
)
from providers.exceptions import ForbiddenProviderOutputError, ProviderError, ProviderSchemaValidationError
from providers.gemini._schema import load_provider_schema


def test_parse_json_response_strips_markdown_fence():
    payload = parse_json_response('```json\n{"detected_languages":["en"]}\n```')
    assert payload["detected_languages"] == ["en"]


def test_assert_no_forbidden_fields_raises():
    with pytest.raises(ForbiddenProviderOutputError):
        assert_no_forbidden_fields({"claim_status": "supported"})


def test_strip_forbidden_fields():
    cleaned = strip_forbidden_fields(
        {"sanitized_claim_excerpt": "dent", "claim_status": "supported", "nested": {"severity": "high"}}
    )
    assert "claim_status" not in cleaned
    assert "severity" not in cleaned["nested"]


def test_validate_flash_schema():
    schema = load_provider_schema("flash_output.schema.json")
    validate_json_schema(
        {
            "detected_languages": ["en"],
            "sanitized_claim_excerpt": "Customer reports a dent.",
            "alleged_parts": ["rear_bumper"],
            "alleged_issue_types": ["dent"],
            "exclusions": [],
            "identity_constraint_active": {"value": False, "confidence": "high"},
            "claimed_damage_alleged": {"value": True, "confidence": "high"},
            "claimed_severity_language": {"value": "medium", "confidence": "medium"},
            "injection_detected_in_chat": False,
        },
        schema,
    )


def test_validate_flash_schema_rejects_extra_field():
    schema = load_provider_schema("flash_output.schema.json")
    with pytest.raises(ProviderSchemaValidationError):
        validate_json_schema({"claim_status": "supported"}, schema)


def test_retry_with_backoff_eventually_succeeds():
    attempts = {"count": 0}

    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ProviderError("temporary")
        return "ok"

    assert retry_with_backoff(flaky, max_attempts=3, base_delay_seconds=0) == "ok"
    assert attempts["count"] == 3
