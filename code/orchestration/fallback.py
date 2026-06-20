"""Fallback artifacts when model providers fail."""

from __future__ import annotations

from datetime import datetime

from contracts.decision import ClaimDecision, SeverityDecision, SupportingImageDecision, VerdictDecision
from contracts.enums import ClaimStatus, DamageExtent, IssueType, ObjectPart, Severity
from contracts.intake import ClaimContext
from contracts.observation import ImageEvidence
from contracts.primitives import ScoredField
from providers.mock.provider import MockFlashProvider
from rules.image_helpers import verdict_ref


def fallback_claim_observation(claim: ClaimContext, *, observed_at: datetime):
    return MockFlashProvider().observe_claim(claim, observed_at=observed_at)


def fallback_image_evidence(
    claim: ClaimContext,
    *,
    image_id: str,
    image_path: str,
    observed_at: datetime,
    observation_pass: int = 1,
) -> ImageEvidence:
    return ImageEvidence(
        row_id=claim.row_id,
        image_id=image_id,
        image_path=image_path,
        file_readable=False,
        usable_for_automated_review=False,
        depicts_claim_object=ScoredField(
            value=False,
            confidence="low",
            source_module="image_observer",
            source_image_id=image_id,
        ),
        visible_part=ScoredField(
            value=ObjectPart.UNKNOWN,
            confidence="low",
            source_module="image_observer",
            source_image_id=image_id,
        ),
        claimed_primary_part_visible=ScoredField(
            value=False,
            confidence="low",
            source_module="image_observer",
            source_image_id=image_id,
        ),
        visible_issue_type=ScoredField(
            value=IssueType.UNKNOWN,
            confidence="low",
            source_module="image_observer",
            source_image_id=image_id,
        ),
        visible_damage_extent=ScoredField(
            value=DamageExtent.UNKNOWN,
            confidence="low",
            source_module="image_observer",
            source_image_id=image_id,
        ),
        is_blurry=ScoredField(value=False, confidence="low", source_module="image_observer", source_image_id=image_id),
        is_cropped_or_obstructed=ScoredField(
            value=False, confidence="low", source_module="image_observer", source_image_id=image_id
        ),
        is_low_light_or_glare=ScoredField(
            value=False, confidence="low", source_module="image_observer", source_image_id=image_id
        ),
        is_wrong_angle_for_claimed_part=ScoredField(
            value=False, confidence="low", source_module="image_observer", source_image_id=image_id
        ),
        is_non_original_image=ScoredField(
            value=False, confidence="low", source_module="image_observer", source_image_id=image_id
        ),
        is_possibly_manipulated=ScoredField(
            value=False, confidence="low", source_module="image_observer", source_image_id=image_id
        ),
        has_instruction_text=ScoredField(
            value=False, confidence="low", source_module="image_observer", source_image_id=image_id
        ),
        package_is_opened=ScoredField(
            value=False, confidence="low", source_module="image_observer", source_image_id=image_id
        ),
        contents_area_visible=ScoredField(
            value=False, confidence="low", source_module="image_observer", source_image_id=image_id
        ),
        vehicle_identity_features=[],
        model_name="fallback-image-observer",
        prompt_version="fallback-v1",
        observed_at=observed_at,
        observation_pass=observation_pass,  # type: ignore[arg-type]
        claim_object=claim.claim_object,
        allowed_image_ids=claim.image_ids,
    )


def apply_provider_failure_nei(
    decision: ClaimDecision,
    *,
    failures: list[str],
    evaluated_at: datetime,
) -> ClaimDecision:
    reason = "; ".join(failures)
    ref = verdict_ref(
        VerdictDecision(
            row_id=decision.row_id,
            claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
            claim_status_rule_id="CS-R01",
            issue_type=IssueType.UNKNOWN,
            object_part=ObjectPart.UNKNOWN,
            decided_at=evaluated_at,
        )
    )
    verdict = VerdictDecision(
        row_id=decision.row_id,
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        claim_status_rule_id="CS-R01",
        issue_type=IssueType.UNKNOWN,
        object_part=ObjectPart.UNKNOWN,
        decided_at=evaluated_at,
        evidence_standard_met=False,
    )
    severity = SeverityDecision(
        row_id=decision.row_id,
        severity=Severity.UNKNOWN,
        severity_rule_id="SV-R01",
        visible_damage_extent_source=DamageExtent.UNKNOWN,
        verdict_ref=ref,
        decided_at=evaluated_at,
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        issue_type=IssueType.UNKNOWN,
    )
    supporting = SupportingImageDecision(
        row_id=decision.row_id,
        supporting_image_ids=[],
        supporting_image_rule_id="SI-R02",
        excluded_image_ids=[],
        selection_rationale=f"Provider failure forced NEI: {reason}",
        verdict_ref=ref,
        decided_at=evaluated_at,
        allowed_image_ids=decision.supporting_decision.allowed_image_ids,
    )
    return ClaimDecision(
        row_id=decision.row_id,
        verdict=verdict,
        severity_decision=severity,
        supporting_decision=supporting,
        evidence_standard_met=False,
        evidence_standard_met_reason=f"Automated observation failed: {reason}",
        valid_image=decision.valid_image,
        claim_status_justification=f"Claim could not be evaluated because observation failed: {reason}",
        composed_at=evaluated_at,
    )
