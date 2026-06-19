"""Shared test fixtures."""

from __future__ import annotations

from datetime import datetime, timezone

from contracts.enums import ClaimObject, DamageExtent, HistoryFlag, IssueFamily, IssueType, ObjectPart, ResolutionMethod
from contracts.intake import ClaimContext
from contracts.observation import ImageEvidence
from contracts.primitives import ScoredField
from contracts.resolution import ClaimResolutionContext

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
) -> ImageEvidence:
    if not file_readable:
        depicts_confidence = "low"
        part_confidence = "low"
        field_confidence = "low"
    else:
        field_confidence = "high"
    return ImageEvidence(
        row_id=row_id,
        image_id=image_id,
        image_path=f"images/sample/case_001/{image_id}.jpg",
        file_readable=file_readable,
        usable_for_automated_review=usable,
        depicts_claim_object=scored(depicts_object, depicts_confidence),
        visible_part=scored(
            ObjectPart.REAR_BUMPER if claim_object is ClaimObject.CAR else ObjectPart.BOX,
            field_confidence,
        ),
        claimed_primary_part_visible=scored(part_visible, part_confidence),
        visible_issue_type=scored(IssueType.DENT, field_confidence),
        visible_damage_extent=scored(DamageExtent.MEDIUM, field_confidence),
        is_blurry=scored(False),
        is_cropped_or_obstructed=scored(False),
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
        resolution_rule_ids=["RES-R01"],
        part_visibility_scores={primary_object_part: 3},
        resolved_at=NOW,
        claim_object=claim_object,
    )
