"""Tests for rules.sufficiency — ESM-R01..ESM-R08."""

from __future__ import annotations

import pytest

from rules.consistency import build_consistency_context
from rules.sufficiency import evaluate_sufficiency
from tests.conftest import NOW, make_evidence_context, make_image_evidence, make_resolution


@pytest.mark.parametrize(
    ("rule_id", "setup"),
    [
        ("ESM-R01", {"file_readable": False}),
        ("ESM-R03", {"part_visible": False, "part_confidence": "low"}),
    ],
)
def test_esm_rules_positive(rule_id: str, setup: dict):
    evidence = make_evidence_context(
        images=[make_image_evidence(**setup)],
    )
    resolution = make_resolution()
    consistency = build_consistency_context(evidence, resolution, evaluated_at=NOW).consistency
    result = evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=NOW)
    assert result.validation.evidence_standard_met is False
    assert result.validation.triggered_rule_id == rule_id
    matched = [record for record in result.rule_records if record.rule_id == rule_id and record.outcome]
    assert matched


def test_esm_r08_default_positive():
    evidence = make_evidence_context(images=[make_image_evidence(part_visible=True, part_confidence="high")])
    resolution = make_resolution()
    consistency = build_consistency_context(evidence, resolution, evaluated_at=NOW).consistency
    result = evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=NOW)
    assert result.validation.evidence_standard_met is True
    assert result.validation.triggered_rule_id == "ESM-R08"


def test_esm_r06_negative_when_part_clear():
    evidence = make_evidence_context(images=[make_image_evidence(part_visible=True, part_confidence="high")])
    resolution = make_resolution()
    consistency = build_consistency_context(evidence, resolution, evaluated_at=NOW).consistency
    result = evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=NOW)
    esm_r06 = next(record for record in result.rule_records if record.rule_id == "ESM-R06")
    assert esm_r06.outcome is False


def test_esm_r01_negative_when_readable():
    evidence = make_evidence_context(images=[make_image_evidence(file_readable=True)])
    resolution = make_resolution()
    consistency = build_consistency_context(evidence, resolution, evaluated_at=NOW).consistency
    result = evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=NOW)
    esm_r01 = next(record for record in result.rule_records if record.rule_id == "ESM-R01")
    assert esm_r01.outcome is False
