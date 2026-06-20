"""Tests for compose.py — ClaimDecision assembly."""

from __future__ import annotations

from contracts.enums import ClaimStatus, IssueType, Severity
from contracts.enums import RuleHitStage
from rules.compose import COMPOSE_RULE_IDS
from rules.rule_trace import records_to_rule_hits
from tests.conftest import make_claim_context, make_claim_observation, make_image_evidence, make_resolution
from tests.rules.stage_helpers import record_outcome, run_compose


def test_compose_populates_claim_decision():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence(part_visible=True, part_confidence="high")]
    result = run_compose(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    decision = result.decision
    assert decision.row_id == claim.row_id
    assert decision.verdict.claim_status is ClaimStatus.SUPPORTED
    assert decision.severity_decision.severity is Severity.MEDIUM
    assert decision.supporting_decision.supporting_image_ids == ["img_1"]
    assert decision.evidence_standard_met is True
    assert decision.evidence_standard_met_reason
    assert decision.valid_image is True
    assert decision.claim_status_justification
    assert decision.composed_at


def test_compose_emits_all_rule_records():
    result = run_compose(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(part_visible=True, part_confidence="high")],
        resolution=make_resolution(),
    )
    emitted = {record.rule_id for record in result.rule_records}
    assert set(COMPOSE_RULE_IDS).issubset(emitted)
    assert record_outcome(result, "CMP-COMPOSE") is True


def test_compose_records_convert_to_rule_hits():
    result = run_compose(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(part_visible=True, part_confidence="high")],
        resolution=make_resolution(),
    )
    hits = records_to_rule_hits(result.rule_records, stage=RuleHitStage.COMPOSE)
    assert len(hits) == len(result.rule_records)
    assert hits[0].stage is RuleHitStage.COMPOSE


def test_compose_hr03_nei_unknown_severity():
    from contracts.enums import DamageExtent
    from contracts.decision import VerdictDecision, SeverityDecision
    from tests.conftest import NOW

    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence(file_readable=False)]
    verdict = VerdictDecision(
        row_id=claim.row_id,
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        claim_status_rule_id="CS-R01",
        issue_type=IssueType.UNKNOWN,
        object_part=observation.alleged_parts[0],
        decided_at=NOW,
    )
    severity = SeverityDecision(
        row_id=claim.row_id,
        severity=Severity.UNKNOWN,
        severity_rule_id="SV-R01",
        visible_damage_extent_source=DamageExtent.UNKNOWN,
        verdict_ref=f"{claim.row_id}:verdict:{NOW.isoformat()}",
        decided_at=NOW,
    )
    result = run_compose(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
        verdict=verdict,
        severity=severity,
    )
    assert record_outcome(result, "CMP-HR03") is True
    assert result.decision.severity is Severity.UNKNOWN
