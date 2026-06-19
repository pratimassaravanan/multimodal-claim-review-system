"""Contract model validation tests."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from contracts.decision import SeverityDecision, VerdictDecision
from contracts.enums import (
    ClaimObject,
    ClaimStatus,
    ClaimedSeverityLanguage,
    DamageExtent,
    IssueFamily,
    IssueType,
    ObjectPart,
    RiskFlag,
    Severity,
)
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation
from contracts.primitives import ScoredField
from contracts.risk import FlagRuleHit, RiskContext
from tests.conftest import NOW, make_claim_context


def _scored(value, confidence="high"):
    return ScoredField(
        value=value,
        confidence=confidence,
        confidence_score=0.9,
        source_module="claim_observer",
        source_image_id=None,
    )


def test_claim_context_rejects_mismatched_image_counts():
    with pytest.raises(ValidationError):
        ClaimContext(
            row_id="user_001:case_001",
            user_id="user_001",
            claim_object=ClaimObject.CAR,
            user_claim="claim",
            image_paths=["a.jpg"],
            image_ids=["img_1", "img_2"],
            image_count=1,
            resolved_image_files=["a.jpg"],
            history_flags=["none"],
            past_claim_count=0,
            accept_claim=0,
            manual_review_claim=0,
            rejected_claim=0,
            last_90_days_claim_count=0,
            applicable_requirement_ids=["REQ_GENERAL_OBJECT_PART"],
            pipeline_version="0.1.0",
            observed_at=NOW,
        )


def test_claim_observation_validates_parts_for_object():
    with pytest.raises(ValidationError):
        ClaimObservation(
            row_id="user_001:case_001",
            alleged_parts=[ObjectPart.KEYBOARD],
            alleged_issue_types=[IssueType.DENT],
            alleged_issue_families=[IssueFamily.DENT_OR_SCRATCH],
            exclusions=[],
            identity_constraint_active=_scored(False),
            claimed_damage_alleged=_scored(True),
            claimed_severity_language=_scored(ClaimedSeverityLanguage.MEDIUM),
            multi_part_detected=False,
            injection_detected_in_chat=False,
            sanitized_claim_excerpt="dent on bumper",
            model_name="gemini-2.5-flash",
            prompt_version="claim-v1",
            observation_raw_hash="sha256:abc",
            observed_at=NOW,
            claim_object=ClaimObject.CAR,
        )


def test_verdict_decision_hr01():
    with pytest.raises(ValidationError):
        VerdictDecision(
            row_id="user_001:case_001",
            claim_status=ClaimStatus.SUPPORTED,
            claim_status_rule_id="CS-R07",
            issue_type=IssueType.DENT,
            object_part=ObjectPart.REAR_BUMPER,
            decided_at=NOW,
            evidence_standard_met=False,
            claim_object=ClaimObject.CAR,
        )


def test_severity_decision_hr03():
    with pytest.raises(ValidationError):
        SeverityDecision(
            row_id="user_001:case_001",
            severity=Severity.MEDIUM,
            severity_rule_id="SV-R05",
            visible_damage_extent_source=DamageExtent.MEDIUM,
            verdict_ref="ref",
            decided_at=NOW,
            claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        )


def test_risk_context_hr04():
    with pytest.raises(ValidationError):
        RiskContext(
            row_id="user_001:case_001",
            risk_flags=[RiskFlag.BLURRY_IMAGE],
            flag_rule_hits=[],
            manual_review_required=False,
            manual_review_rule_ids=[],
            history_flags_input=["user_history_risk"],
            evaluated_at=NOW,
        )


def test_risk_context_accepts_uhr_propagation():
    ctx = RiskContext(
        row_id="user_001:case_001",
        risk_flags=[RiskFlag.USER_HISTORY_RISK, RiskFlag.MANUAL_REVIEW_REQUIRED],
        flag_rule_hits=[
            FlagRuleHit(
                flag=RiskFlag.USER_HISTORY_RISK,
                rule_id="RF-1",
                trigger_image_ids=[],
                min_confidence_met=True,
            )
        ],
        manual_review_required=True,
        manual_review_rule_ids=["MRR-2"],
        history_flags_input=["user_history_risk"],
        evaluated_at=NOW,
    )
    assert RiskFlag.USER_HISTORY_RISK in ctx.risk_flags


def test_claim_context_from_helper():
    ctx = make_claim_context()
    assert ctx.image_count == 1
    assert ctx.claim_object is ClaimObject.CAR
