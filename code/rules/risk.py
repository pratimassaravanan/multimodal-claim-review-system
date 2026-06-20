"""Risk flag matrix — decision_matrix §6 plus MRR-1..MRR-6."""

from __future__ import annotations

from datetime import datetime

from contracts.decision import VerdictDecision
from contracts.enums import ClaimStatus, HistoryFlag, IssueType, RiskFlag
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.reconciliation import ConsistencyContext, ValidationContext
from contracts.resolution import ClaimResolutionContext
from contracts.risk import FlagRuleHit, RiskContext
from rules.confidence import confidence_at_least
from rules.image_helpers import select_reference_image
from rules.types import RiskStageResult, RuleExecutionRecord, TraceField

MRR_RULE_IDS = ("MRR-1", "MRR-2", "MRR-3", "MRR-4", "MRR-5", "MRR-6")

IMAGE_QUALITY_FLAGS: tuple[tuple[RiskFlag, str, str], ...] = (
    (RiskFlag.BLURRY_IMAGE, "blurry_image", "is_blurry"),
    (RiskFlag.CROPPED_OR_OBSTRUCTED, "cropped_or_obstructed", "is_cropped_or_obstructed"),
    (RiskFlag.LOW_LIGHT_OR_GLARE, "low_light_or_glare", "is_low_light_or_glare"),
)

AUTHENTICITY_FLAGS: tuple[tuple[RiskFlag, str, str, str], ...] = (
    (RiskFlag.NON_ORIGINAL_IMAGE, "non_original_image", "is_non_original_image", "high"),
    (RiskFlag.POSSIBLE_MANIPULATION, "possible_manipulation", "is_possibly_manipulated", "high"),
    (RiskFlag.TEXT_INSTRUCTION_PRESENT, "text_instruction_present", "has_instruction_text", "medium"),
)


def _record(rule_id: str, outcome: bool, justification: str, *pairs: tuple[str, str]) -> RuleExecutionRecord:
    return RuleExecutionRecord(
        rule_id=rule_id,
        outcome=outcome,
        justification=justification,
        trace_fields=[TraceField(key=k, value=v) for k, v in pairs],
    )


def _image_field_true(image: ImageEvidence, field_name: str, minimum: str = "medium") -> bool:
    field = getattr(image, field_name)
    return field.value and confidence_at_least(field.confidence, minimum)


def _triggering_images(images: list[ImageEvidence], field_name: str, minimum: str = "medium") -> list[str]:
    return [
        image.image_id
        for image in images
        if _image_field_true(image, field_name, minimum)
    ]


def _reference_shows_no_damage(
    images: list[ImageEvidence],
    best_ids: list[str],
) -> bool:
    ref = select_reference_image(images, best_ids)
    if ref is None:
        return False
    return ref.visible_issue_type.value is IssueType.NONE and confidence_at_least(
        ref.visible_issue_type.confidence, "medium"
    )


def evaluate_risk(
    claim: ClaimContext,
    observation: ClaimObservation,
    verdict: VerdictDecision,
    images: list[ImageEvidence],
    validation: ValidationContext,
    consistency: ConsistencyContext,
    resolution: ClaimResolutionContext,
    *,
    evaluated_at: datetime,
) -> RiskStageResult:
    """Assess row-level risk flags without modifying claim_status."""
    records: list[RuleExecutionRecord] = []
    predicates = validation.predicates
    best_ids = consistency.best_part_image_ids or predicates.best_part_image_ids
    hits: list[FlagRuleHit] = []
    flags: set[RiskFlag] = set()

    for flag, rule_id, field_name in IMAGE_QUALITY_FLAGS:
        if rule_id == "wrong_angle":
            continue
        trigger_ids = _triggering_images(images, field_name)
        matched = len(trigger_ids) > 0
        records.append(
            _record(
                rule_id,
                matched,
                f"{flag.value} triggered by image quality signal." if matched else f"No {flag.value}.",
                ("trigger_image_ids", ";".join(trigger_ids) or "none"),
            )
        )
        if matched:
            flags.add(flag)
            hits.append(
                FlagRuleHit(
                    flag=flag,
                    rule_id=rule_id,
                    trigger_image_ids=trigger_ids,
                    min_confidence_met=True,
                )
            )

    wrong_angle_ids = [
        image.image_id
        for image in images
        if _image_field_true(image, "is_wrong_angle_for_claimed_part")
        and not image.claimed_primary_part_visible.value
    ]
    wrong_angle = len(wrong_angle_ids) > 0
    records.append(
        _record(
            "wrong_angle",
            wrong_angle,
            "Wrong angle with claimed primary part not visible."
            if wrong_angle
            else "No wrong-angle risk.",
            ("trigger_image_ids", ";".join(wrong_angle_ids) or "none"),
        )
    )
    if wrong_angle:
        flags.add(RiskFlag.WRONG_ANGLE)
        hits.append(
            FlagRuleHit(
                flag=RiskFlag.WRONG_ANGLE,
                rule_id="wrong_angle",
                trigger_image_ids=wrong_angle_ids,
                min_confidence_met=True,
            )
        )

    wrong_object = consistency.wrong_object_set or predicates.identity_conflict
    records.append(
        _record(
            "wrong_object",
            wrong_object,
            "Wrong object set or identity conflict detected."
            if wrong_object
            else "Claim object consistent across images.",
            ("wrong_object_set", str(consistency.wrong_object_set).lower()),
            ("identity_conflict", str(predicates.identity_conflict).lower()),
        )
    )
    if wrong_object:
        flags.add(RiskFlag.WRONG_OBJECT)
        hits.append(
            FlagRuleHit(
                flag=RiskFlag.WRONG_OBJECT,
                rule_id="wrong_object",
                trigger_image_ids=[],
                min_confidence_met=True,
            )
        )

    ref = select_reference_image(images, best_ids)
    wrong_part = bool(
        predicates.part_clear
        and ref is not None
        and confidence_at_least(ref.visible_part.confidence, "medium")
        and ref.visible_part.value != resolution.primary_object_part
    )
    records.append(
        _record(
            "wrong_object_part",
            wrong_part,
            "Visible part differs from resolved primary part."
            if wrong_part
            else "Visible part aligns with primary part or part not clear.",
            ("visible_part", ref.visible_part.value if ref else "none"),
            ("primary_object_part", resolution.primary_object_part.value),
        )
    )
    if wrong_part:
        flags.add(RiskFlag.WRONG_OBJECT_PART)
        hits.append(
            FlagRuleHit(
                flag=RiskFlag.WRONG_OBJECT_PART,
                rule_id="wrong_object_part",
                trigger_image_ids=[ref.image_id] if ref else [],
                min_confidence_met=True,
            )
        )

    damage_not_visible = (
        observation.claimed_damage_alleged.value
        and (
            predicates.no_part_visible
            or (predicates.part_clear and _reference_shows_no_damage(images, best_ids))
        )
    )
    records.append(
        _record(
            "damage_not_visible",
            damage_not_visible,
            "Claimed damage not visible on submitted images."
            if damage_not_visible
            else "Damage visibility risk not triggered.",
            ("no_part_visible", str(predicates.no_part_visible).lower()),
            ("part_clear", str(predicates.part_clear).lower()),
        )
    )
    if damage_not_visible:
        flags.add(RiskFlag.DAMAGE_NOT_VISIBLE)
        hits.append(
            FlagRuleHit(
                flag=RiskFlag.DAMAGE_NOT_VISIBLE,
                rule_id="damage_not_visible",
                trigger_image_ids=[ref.image_id] if ref else [],
                min_confidence_met=True,
            )
        )

    claim_mismatch = verdict.claim_status is ClaimStatus.CONTRADICTED and (
        verdict.claim_status_rule_id in {"CS-R04", "CS-R05", "CS-R06"}
        or RiskFlag.WRONG_OBJECT in flags
    )
    records.append(
        _record(
            "claim_mismatch",
            claim_mismatch,
            "Contradicted claim with mismatching evidence."
            if claim_mismatch
            else "Claim mismatch flag not triggered.",
            ("claim_status_rule_id", verdict.claim_status_rule_id),
        )
    )
    if claim_mismatch:
        flags.add(RiskFlag.CLAIM_MISMATCH)
        hits.append(
            FlagRuleHit(
                flag=RiskFlag.CLAIM_MISMATCH,
                rule_id="claim_mismatch",
                trigger_image_ids=[],
                min_confidence_met=True,
            )
        )

    for flag, rule_id, field_name, minimum in AUTHENTICITY_FLAGS:
        trigger_ids = _triggering_images(images, field_name, minimum)
        matched = len(trigger_ids) > 0
        records.append(
            _record(
                rule_id,
                matched,
                f"{flag.value} detected." if matched else f"No {flag.value}.",
                ("trigger_image_ids", ";".join(trigger_ids) or "none"),
            )
        )
        if matched:
            flags.add(flag)
            hits.append(
                FlagRuleHit(
                    flag=flag,
                    rule_id=rule_id,
                    trigger_image_ids=trigger_ids,
                    min_confidence_met=True,
                )
            )

    history_flags_input = list(claim.history_flags)
    uhr = HistoryFlag.USER_HISTORY_RISK in claim.history_flags
    records.append(
        _record(
            "user_history_risk",
            uhr,
            "History contains user_history_risk." if uhr else "No user history risk flag.",
            ("history_flags", ";".join(flag.value for flag in claim.history_flags)),
        )
    )
    if uhr:
        flags.add(RiskFlag.USER_HISTORY_RISK)
        hits.append(
            FlagRuleHit(
                flag=RiskFlag.USER_HISTORY_RISK,
                rule_id="user_history_risk",
                trigger_image_ids=[],
                min_confidence_met=True,
            )
        )

    mrr_matches: dict[str, bool] = {
        "MRR-1": HistoryFlag.MANUAL_REVIEW_REQUIRED in claim.history_flags,
        "MRR-2": HistoryFlag.USER_HISTORY_RISK in claim.history_flags,
        "MRR-3": predicates.identity_conflict,
        "MRR-4": RiskFlag.CLAIM_MISMATCH in flags,
        "MRR-5": RiskFlag.NON_ORIGINAL_IMAGE in flags,
        "MRR-6": verdict.claim_status is ClaimStatus.NOT_ENOUGH_INFORMATION and predicates.contents_claim,
    }
    manual_review_rule_ids: list[str] = []
    for rule_id, matched in mrr_matches.items():
        records.append(
            _record(
                rule_id,
                matched,
                f"{rule_id} manual review trigger matched." if matched else f"{rule_id} not matched.",
            )
        )
        if matched:
            manual_review_rule_ids.append(rule_id)

    manual_review_required = len(manual_review_rule_ids) > 0
    records.append(
        _record(
            "manual_review_required",
            manual_review_required,
            "Composite manual review required." if manual_review_required else "Manual review not required.",
            ("manual_review_rule_ids", ";".join(manual_review_rule_ids) or "none"),
        )
    )
    if manual_review_required:
        flags.add(RiskFlag.MANUAL_REVIEW_REQUIRED)
        hits.append(
            FlagRuleHit(
                flag=RiskFlag.MANUAL_REVIEW_REQUIRED,
                rule_id="manual_review_required",
                trigger_image_ids=[],
                min_confidence_met=True,
            )
        )

    sorted_flags = sorted(flags, key=lambda flag: flag.value)
    if not sorted_flags:
        sorted_flags = [RiskFlag.NONE]
        hits = []

    risk = RiskContext(
        row_id=claim.row_id,
        risk_flags=sorted_flags,
        flag_rule_hits=hits,
        manual_review_required=manual_review_required,
        manual_review_rule_ids=manual_review_rule_ids,
        history_flags_input=history_flags_input,
        evaluated_at=evaluated_at,
    )
    return RiskStageResult(risk=risk, rule_records=records)
