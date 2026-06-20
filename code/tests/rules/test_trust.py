"""Tests for rules.trust — VI-R01..VI-R04."""

from __future__ import annotations

import pytest

from rules.trust import evaluate_trust
from tests.conftest import NOW, make_evidence_context, make_image_evidence, make_resolution


@pytest.mark.parametrize(
    ("rule_id", "kwargs"),
    [
        ("VI-R01", {"usable": False}),
        ("VI-R02", {"non_original": True, "non_original_confidence": "high"}),
    ],
)
def test_vi_rules_positive(rule_id: str, kwargs: dict):
    evidence = make_evidence_context(images=[make_image_evidence(**kwargs)])
    result = evaluate_trust(evidence, make_resolution(), evaluated_at=NOW)
    assert result.trust.valid_image is False
    assert result.trust.triggered_rule_id == rule_id
    assert any(record.rule_id == rule_id and record.outcome for record in result.rule_records)


def test_vi_r04_default_positive():
    evidence = make_evidence_context(images=[make_image_evidence()])
    result = evaluate_trust(evidence, make_resolution(), evaluated_at=NOW)
    assert result.trust.valid_image is True
    assert result.trust.triggered_rule_id == "VI-R04"


def test_vi_r01_negative_when_usable():
    evidence = make_evidence_context(images=[make_image_evidence(usable=True)])
    result = evaluate_trust(evidence, make_resolution(), evaluated_at=NOW)
    vi_r01 = next(record for record in result.rule_records if record.rule_id == "VI-R01")
    assert vi_r01.outcome is False
