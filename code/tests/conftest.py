"""Shared test fixtures."""

from __future__ import annotations

from datetime import datetime, timezone

from contracts.enums import (
    ClaimObject,
    ClaimedSeverityLanguage,
    DamageExtent,
    HistoryFlag,
    IdentitySide,
    IssueFamily,
    IssueType,
    ObjectPart,
    ResolutionMethod,
)
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.primitives import ScoredField
from contracts.resolution import ClaimResolutionContext, EvidenceContext

NOW = datetime(2026, 6, 19, 21, 0, 0, tzinfo=timezone.utc)


def scored(value, confidence: str = "high", **kwargs):
    return ScoredField(
        value=value,
        confidence=confidence,
        source_module="image_observer",
        **kwargs,
    )


def make_claim_context(
    *,
    claim_object: ClaimObject = ClaimObject.CAR,
    image_ids: list[str] | None = None,
) -> ClaimContext:
    image_ids = image_ids or ["img_1"]
    paths = [f"images/sample/case_001/{i}.jpg" for i in image_ids]
    return ClaimContext(
        row_id="user_001:case_001",
        user_id="user_001",
        claim_object=claim_object,
        user_claim="Customer reports rear bumper dent.",
        image_paths=paths,
        image_ids=image_ids,
        image_count=len(image_ids),
        resolved_image_files=paths,
        history_flags=[HistoryFlag.NONE],
        history_summary=None,
        past_claim_count=0,
        accept_claim=0,
        manual_review_claim=0,
        rejected_claim=0,
        last_90_days_claim_count=0,
        applicable_requirement_ids=["REQ_GENERAL_OBJECT_PART", "REQ_REVIEW_TRUST"],
        pipeline_version="0.1.0",
        observed_at=NOW,
    )


def make_image_evidence(
    *,
    image_id: str = "img_1",
    row_id: str = "user_001:case_001",
    claim_object: ClaimObject = ClaimObject.CAR,
    part_visible: bool = True,
    part_confidence: str = "high",
    depicts_object: bool = True,
    depicts_confidence: str = "high",
    usable: bool = True,
    file_readable: bool = True,
    vehicle_identity_features: list[str] | None = None,
    package_opened: bool = False,
    contents_visible: bool = False,
    non_original: bool = False,
    non_original_confidence: str = "low",
    visible_part: ObjectPart | None = None,
    visible_issue_type: IssueType | None = None,
    issue_confidence: str | None = None,
    visible_damage_extent: DamageExtent | None = None,
    extent_confidence: str | None = None,
    cropped_or_obstructed: bool = False,
    cropped_confidence: str = "low",
) -> ImageEvidence:
    if not file_readable:
        depicts_confidence = "low"
        part_confidence = "low"
        field_confidence = "low"
    else:
        field_confidence = "high"
    part = visible_part or (ObjectPart.REAR_BUMPER if claim_object is ClaimObject.CAR else ObjectPart.BOX)
    issue = visible_issue_type or IssueType.DENT
    issue_conf = issue_confidence or field_confidence
    extent = visible_damage_extent or DamageExtent.MEDIUM
    extent_conf = extent_confidence or field_confidence
    return ImageEvidence(
        row_id=row_id,
        image_id=image_id,
        image_path=f"images/sample/case_001/{image_id}.jpg",
        file_readable=file_readable,
        usable_for_automated_review=usable,
        depicts_claim_object=scored(depicts_object, depicts_confidence),
        visible_part=scored(part, field_confidence),
        claimed_primary_part_visible=scored(part_visible, part_confidence),
        visible_issue_type=scored(issue, issue_conf),
        visible_damage_extent=scored(extent, extent_conf),
        is_blurry=scored(False),
        is_cropped_or_obstructed=scored(cropped_or_obstructed, cropped_confidence),
        is_low_light_or_glare=scored(False),
        is_wrong_angle_for_claimed_part=scored(False),
        is_non_original_image=scored(non_original, non_original_confidence),
        is_possibly_manipulated=scored(False),
        has_instruction_text=scored(False),
        package_is_opened=scored(package_opened, "medium" if package_opened else "low"),
        contents_area_visible=scored(contents_visible, "medium" if contents_visible else "low"),
        vehicle_identity_features=vehicle_identity_features or [],
        model_name="test",
        prompt_version="test-v1",
        observed_at=NOW,
        claim_object=claim_object,
    )


def make_resolution(
    *,
    claim_object: ClaimObject = ClaimObject.CAR,
    primary_issue_family: IssueFamily = IssueFamily.DENT_OR_SCRATCH,
    primary_object_part: ObjectPart = ObjectPart.REAR_BUMPER,
) -> ClaimResolutionContext:
    return ClaimResolutionContext(
        row_id="user_001:case_001",
        claim_observation_ref="obs-1",
        multi_part_claim=False,
        primary_object_part=primary_object_part,
        primary_issue_family=primary_issue_family,
        secondary_object_parts=[],
        resolution_method=ResolutionMethod.SINGLE_PART,
        resolution_rule_ids=["MP-2"],
        part_visibility_scores={primary_object_part: 3},
        resolved_at=NOW,
        claim_object=claim_object,
    )


def make_claim_observation(
    *,
    claim_object: ClaimObject = ClaimObject.CAR,
    alleged_parts: list[ObjectPart] | None = None,
    alleged_issue_types: list[IssueType] | None = None,
    identity_constraint_active: bool = False,
    identity_side: IdentitySide | None = None,
    identity_color: str | None = None,
    last_customer_message_excerpt: str | None = None,
    claimed_severity_language: ClaimedSeverityLanguage = ClaimedSeverityLanguage.MEDIUM,
) -> ClaimObservation:
    if alleged_parts is None:
        if claim_object is ClaimObject.PACKAGE:
            alleged_parts = [ObjectPart.CONTENTS]
        elif claim_object is ClaimObject.LAPTOP:
            alleged_parts = [ObjectPart.SCREEN]
        else:
            alleged_parts = [ObjectPart.REAR_BUMPER]
    if alleged_issue_types is None:
        if claim_object is ClaimObject.PACKAGE:
            alleged_issue_types = [IssueType.MISSING_PART]
        else:
            alleged_issue_types = [IssueType.DENT]
    if claim_object is ClaimObject.PACKAGE:
        families = [IssueFamily.CONTENTS_OR_ITEM]
    elif claim_object is ClaimObject.LAPTOP:
        families = [IssueFamily.SCREEN_KEYBOARD_TRACKPAD]
    else:
        families = [IssueFamily.DENT_OR_SCRATCH]
    return ClaimObservation(
        row_id="user_001:case_001",
        alleged_parts=alleged_parts,
        alleged_issue_types=alleged_issue_types,
        alleged_issue_families=families,
        exclusions=[],
        identity_constraint_active=scored(identity_constraint_active, "high" if identity_constraint_active else "low"),
        identity_side=scored(identity_side, "high") if identity_side is not None else None,
        identity_color=scored(identity_color, "high") if identity_color else None,
        claimed_damage_alleged=scored(True),
        claimed_severity_language=scored(claimed_severity_language),
        multi_part_detected=len(alleged_parts) > 1,
        injection_detected_in_chat=False,
        sanitized_claim_excerpt="Customer reports damage.",
        model_name="test",
        prompt_version="test-v1",
        observation_raw_hash="obs-hash-1",
        observed_at=NOW,
        last_customer_message_excerpt=last_customer_message_excerpt,
        claim_object=claim_object,
    )


def make_evidence_context(
    *,
    claim: ClaimContext | None = None,
    observation: ClaimObservation | None = None,
    images: list[ImageEvidence] | None = None,
) -> EvidenceContext:
    claim = claim or make_claim_context()
    observation = observation or make_claim_observation(claim_object=claim.claim_object)
    images = images or [make_image_evidence(claim_object=claim.claim_object)]
    return EvidenceContext(
        claim=claim,
        claim_observation=observation,
        images=images,
        observation_complete=True,
        aggregated_at=NOW,
    )
