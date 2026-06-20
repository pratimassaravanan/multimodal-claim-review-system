"""Dedicated positive/negative coverage for ESM-R* Rule IDs (§1.1)."""

from __future__ import annotations

from contracts.enums import ClaimObject, IdentitySide, IssueFamily, ObjectPart
from rules.consistency import build_consistency_context
from rules.sufficiency import evaluate_sufficiency
from tests.conftest import NOW, make_claim_context, make_claim_observation, make_evidence_context, make_image_evidence, make_resolution


def _evaluate(evidence, resolution):
    consistency = build_consistency_context(evidence, resolution, evaluated_at=NOW).consistency
    return evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=NOW)


def _record_outcome(result, rule_id: str) -> bool | None:
    for record in result.rule_records:
        if record.rule_id == rule_id:
            return record.outcome
    return None


def test_esm_r02_positive():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    images = [
        make_image_evidence(image_id="img_1", vehicle_identity_features=["color:red"], depicts_confidence="high"),
        make_image_evidence(image_id="img_2", vehicle_identity_features=["color:blue"], depicts_confidence="high"),
    ]
    evidence = make_evidence_context(claim=claim, images=images)
    result = _evaluate(evidence, make_resolution())
    assert result.validation.triggered_rule_id == "ESM-R02"
    assert _record_outcome(result, "ESM-R02") is True


def test_esm_r02_negative():
    evidence = make_evidence_context(images=[make_image_evidence()])
    result = _evaluate(evidence, make_resolution())
    assert _record_outcome(result, "ESM-R02") is False


def test_esm_r03_negative_when_part_visible():
    evidence = make_evidence_context(images=[make_image_evidence(part_visible=True, part_confidence="high")])
    result = _evaluate(evidence, make_resolution())
    assert _record_outcome(result, "ESM-R03") is False


def test_esm_r04_positive():
    resolution = make_resolution(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CONTENTS_OR_ITEM,
        primary_object_part=ObjectPart.CONTENTS,
    )
    claim = make_claim_context(claim_object=ClaimObject.PACKAGE)
    evidence = make_evidence_context(
        claim=claim,
        images=[make_image_evidence(claim_object=ClaimObject.PACKAGE)],
        observation=make_claim_observation(claim_object=ClaimObject.PACKAGE),
    )
    result = _evaluate(evidence, resolution)
    assert result.validation.triggered_rule_id == "ESM-R04"
    assert _record_outcome(result, "ESM-R04") is True


def test_esm_r04_negative():
    resolution = make_resolution(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CONTENTS_OR_ITEM,
        primary_object_part=ObjectPart.CONTENTS,
    )
    claim = make_claim_context(claim_object=ClaimObject.PACKAGE)
    evidence = make_evidence_context(
        claim=claim,
        images=[
            make_image_evidence(
                claim_object=ClaimObject.PACKAGE,
                package_opened=True,
                contents_visible=True,
            )
        ],
        observation=make_claim_observation(claim_object=ClaimObject.PACKAGE),
    )
    result = _evaluate(evidence, resolution)
    assert _record_outcome(result, "ESM-R04") is False


def test_esm_r05_positive_trigger_unreachable():
    """ESM-R05 preempted by ESM-R03 when part_visible_low_only (see docs/esm_r06_analysis.md)."""
    evidence = make_evidence_context(
        images=[make_image_evidence(part_visible=True, part_confidence="low")],
    )
    result = _evaluate(evidence, make_resolution())
    assert result.validation.triggered_rule_id == "ESM-R03"
    assert _record_outcome(result, "ESM-R05") is None


def test_esm_r05_negative():
    evidence = make_evidence_context(
        images=[make_image_evidence(part_visible=True, part_confidence="high")],
    )
    result = _evaluate(evidence, make_resolution())
    assert _record_outcome(result, "ESM-R05") is False


def test_esm_r06_negative_when_part_clear():
    evidence = make_evidence_context(images=[make_image_evidence(part_visible=True, part_confidence="high")])
    result = _evaluate(evidence, make_resolution())
    assert _record_outcome(result, "ESM-R06") is False


def test_esm_r06_positive_trigger_unreachable():
    """Dead rule: ESM-R06 cannot become triggered_rule_id (see docs/esm_r06_analysis.md)."""
    evidence = make_evidence_context(images=[make_image_evidence(part_visible=False, part_confidence="low")])
    result = _evaluate(evidence, make_resolution())
    assert result.validation.triggered_rule_id == "ESM-R03"
    assert _record_outcome(result, "ESM-R06") is None


def test_esm_r07_positive():
    claim = make_claim_context()
    observation = make_claim_observation(
        identity_constraint_active=True,
        identity_side=IdentitySide.LEFT,
    )
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            vehicle_identity_features=["side:driver"],
        )
    ]
    evidence = make_evidence_context(claim=claim, observation=observation, images=images)
    result = _evaluate(evidence, make_resolution())
    assert result.validation.triggered_rule_id == "ESM-R07"
    assert _record_outcome(result, "ESM-R07") is True


def test_esm_r07_negative():
    claim = make_claim_context()
    observation = make_claim_observation(
        identity_constraint_active=True,
        identity_side=IdentitySide.LEFT,
    )
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            vehicle_identity_features=["side:left"],
        )
    ]
    evidence = make_evidence_context(claim=claim, observation=observation, images=images)
    result = _evaluate(evidence, make_resolution())
    assert _record_outcome(result, "ESM-R07") is False


def test_esm_r08_negative_when_higher_priority_matches():
    evidence = make_evidence_context(images=[make_image_evidence(file_readable=False)])
    result = _evaluate(evidence, make_resolution())
    assert result.validation.triggered_rule_id == "ESM-R01"
    assert _record_outcome(result, "ESM-R08") is None
