"""Dedicated positive/negative coverage for VI-R* Rule IDs (§2.1)."""

from __future__ import annotations

from contracts.enums import ClaimObject, IssueFamily, ObjectPart
from rules.trust import evaluate_trust
from tests.conftest import NOW, make_claim_context, make_evidence_context, make_image_evidence, make_resolution


def _record_outcome(result, rule_id: str) -> bool | None:
    for record in result.rule_records:
        if record.rule_id == rule_id:
            return record.outcome
    return None


def test_vi_r02_negative():
    evidence = make_evidence_context(images=[make_image_evidence(non_original=False)])
    result = evaluate_trust(evidence, make_resolution(), evaluated_at=NOW)
    assert _record_outcome(result, "VI-R02") is False


def test_vi_r03_positive():
    resolution = make_resolution(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CONTENTS_OR_ITEM,
        primary_object_part=ObjectPart.CONTENTS,
    )
    evidence = make_evidence_context(
        claim=make_claim_context(claim_object=ClaimObject.PACKAGE),
        images=[
            make_image_evidence(
                claim_object=ClaimObject.PACKAGE,
                cropped_or_obstructed=True,
                cropped_confidence="high",
            )
        ],
    )
    result = evaluate_trust(evidence, resolution, evaluated_at=NOW)
    assert result.trust.triggered_rule_id == "VI-R03"
    assert _record_outcome(result, "VI-R03") is True


def test_vi_r03_negative():
    resolution = make_resolution(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CRUSHED_TORN_SEAL,
        primary_object_part=ObjectPart.BOX,
    )
    evidence = make_evidence_context(
        claim=make_claim_context(claim_object=ClaimObject.PACKAGE),
        images=[
            make_image_evidence(
                claim_object=ClaimObject.PACKAGE,
                cropped_or_obstructed=True,
                cropped_confidence="high",
            )
        ],
    )
    result = evaluate_trust(evidence, resolution, evaluated_at=NOW)
    assert _record_outcome(result, "VI-R03") is False


def test_vi_r04_negative_when_vi_r01_matches():
    evidence = make_evidence_context(images=[make_image_evidence(usable=False)])
    result = evaluate_trust(evidence, make_resolution(), evaluated_at=NOW)
    assert result.trust.triggered_rule_id == "VI-R01"
    assert _record_outcome(result, "VI-R04") is None
