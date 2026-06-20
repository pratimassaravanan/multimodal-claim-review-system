"""Claim status matrix — decision_matrix §3 (CS-R01..CS-R08)."""

from __future__ import annotations

from datetime import datetime

from contracts.decision import VerdictDecision
from contracts.enums import (
    ClaimObject,
    ClaimStatus,
    ClaimedSeverityLanguage,
    ContradictionSubtype,
    DamageExtent,
    IssueType,
    ObjectPart,
)
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.reconciliation import ConsistencyContext, TrustAssessmentContext, ValidationContext
from contracts.resolution import ClaimResolutionContext
from ontology.issue_families import map_issue_type_to_family
from rules.confidence import confidence_at_least
from rules.types import RuleExecutionRecord, TraceField, VerdictStageResult

EXTENT_RANK: dict[DamageExtent, int] = {
    DamageExtent.NONE: 0,
    DamageExtent.LOW: 1,
    DamageExtent.MEDIUM: 2,
    DamageExtent.HIGH: 3,
    DamageExtent.UNKNOWN: 0,
}

CS_RULE_IDS = (
    "CS-R01",
    "CS-R02",
    "CS-R03",
    "CS-R04",
    "CS-R05",
    "CS-R06",
    "CS-R07",
    "CS-R08",
)


def _record(
    rule_id: str,
    outcome: bool,
    justification: str,
    *pairs: tuple[str, str],
) -> RuleExecutionRecord:
    return RuleExecutionRecord(
        rule_id=rule_id,
        outcome=outcome,
        justification=justification,
        trace_fields=[TraceField(key=k, value=v) for k, v in pairs],
    )


def _best_images(images: list[ImageEvidence], best_ids: list[str]) -> list[ImageEvidence]:
    if not best_ids:
        return list(images)
    id_set = set(best_ids)
    return [img for img in images if img.image_id in id_set]


def _select_reference_image(images: list[ImageEvidence], best_ids: list[str]) -> ImageEvidence | None:
    candidates = _best_images(images, best_ids)
    if not candidates:
        return images[0] if images else None
    return max(
        candidates,
        key=lambda img: (
            confidence_at_least(img.claimed_primary_part_visible.confidence, "high"),
            confidence_at_least(img.claimed_primary_part_visible.confidence, "medium"),
            img.image_id,
        ),
    )


def _extent_at_least_low(extent: DamageExtent) -> bool:
    return EXTENT_RANK[extent] >= EXTENT_RANK[DamageExtent.LOW]


def _any_image_damage_at_least_low(images: list[ImageEvidence]) -> bool:
    return any(
        _extent_at_least_low(img.visible_damage_extent.value)
        and confidence_at_least(img.visible_damage_extent.confidence, "medium")
        for img in images
    )


def _issue_type_matches_family(
    issue_type: IssueType,
    primary_family,
    claim_object: ClaimObject,
    visible_part: ObjectPart,
) -> bool:
    return map_issue_type_to_family(issue_type, claim_object, visible_part) == primary_family


def _cs_r02_match(consistency: ConsistencyContext, images: list[ImageEvidence]) -> bool:
    return consistency.wrong_object_set and _any_image_damage_at_least_low(images)


def _cs_r03_match(
    predicates,
    resolution: ClaimResolutionContext,
    images: list[ImageEvidence],
    best_ids: list[str],
) -> tuple[bool, ImageEvidence | None]:
    if not predicates.part_clear:
        return False, None
    for image in _best_images(images, best_ids):
        if (
            image.claimed_primary_part_visible.value
            and confidence_at_least(image.claimed_primary_part_visible.confidence, "medium")
            and image.visible_issue_type.value is IssueType.NONE
            and confidence_at_least(image.visible_issue_type.confidence, "medium")
        ):
            return True, image
    return False, None


def _cs_r04_match(
    predicates,
    resolution: ClaimResolutionContext,
    images: list[ImageEvidence],
    best_ids: list[str],
) -> tuple[bool, ImageEvidence | None]:
    if not predicates.part_clear:
        return False, None
    ref = _select_reference_image(images, best_ids)
    if ref is None:
        return False, None
    if (
        confidence_at_least(ref.visible_part.confidence, "medium")
        and ref.visible_part.value != resolution.primary_object_part
    ):
        return True, ref
    return False, None


def _cs_r05_match(
    predicates,
    resolution: ClaimResolutionContext,
    images: list[ImageEvidence],
    best_ids: list[str],
    claim_object: ClaimObject,
) -> tuple[bool, ImageEvidence | None]:
    if not predicates.part_clear:
        return False, None
    ref = _select_reference_image(images, best_ids)
    if ref is None:
        return False, None
    if not confidence_at_least(ref.visible_issue_type.confidence, "medium"):
        return False, None
    if _issue_type_matches_family(
        ref.visible_issue_type.value,
        resolution.primary_issue_family,
        claim_object,
        ref.visible_part.value,
    ):
        return False, None
    return True, ref


def _cs_r06_match(
    predicates,
    observation: ClaimObservation,
    images: list[ImageEvidence],
    best_ids: list[str],
) -> tuple[bool, ImageEvidence | None]:
    if not predicates.part_clear:
        return False, None
    severity = observation.claimed_severity_language.value
    if severity not in (ClaimedSeverityLanguage.HIGH, ClaimedSeverityLanguage.EXAGGERATED):
        return False, None
    ref = _select_reference_image(images, best_ids)
    if ref is None:
        return False, None
    if (
        ref.visible_damage_extent.value is DamageExtent.LOW
        and confidence_at_least(ref.visible_damage_extent.confidence, "medium")
    ):
        return True, ref
    return False, None


def _cs_r07_match(
    predicates,
    resolution: ClaimResolutionContext,
    images: list[ImageEvidence],
    best_ids: list[str],
    claim_object: ClaimObject,
    *,
    contradiction_matched: bool,
) -> tuple[bool, ImageEvidence | None]:
    if contradiction_matched or not predicates.part_clear:
        return False, None
    ref = _select_reference_image(images, best_ids)
    if ref is None:
        return False, None
    if not (
        confidence_at_least(ref.visible_issue_type.confidence, "medium")
        and confidence_at_least(ref.visible_part.confidence, "medium")
        and ref.visible_part.value == resolution.primary_object_part
        and _issue_type_matches_family(
            ref.visible_issue_type.value,
            resolution.primary_issue_family,
            claim_object,
            ref.visible_part.value,
        )
    ):
        return False, None
    return True, ref


def _assign_nei_fields(
    resolution: ClaimResolutionContext,
    images: list[ImageEvidence],
    best_ids: list[str],
) -> tuple[IssueType, ObjectPart]:
    ref = _select_reference_image(images, best_ids)
    part = ObjectPart.UNKNOWN
    if ref and confidence_at_least(ref.claimed_primary_part_visible.confidence, "medium"):
        if ref.claimed_primary_part_visible.value:
            part = resolution.primary_object_part
        elif confidence_at_least(ref.visible_part.confidence, "medium"):
            part = ref.visible_part.value
    return IssueType.UNKNOWN, part


def _assign_contradicted_fields(
    rule_id: str,
    consistency: ConsistencyContext,
    ref: ImageEvidence | None,
) -> tuple[IssueType, ObjectPart, ContradictionSubtype]:
    if rule_id == "CS-R02" or consistency.wrong_object_set:
        return IssueType.UNKNOWN, ObjectPart.UNKNOWN, ContradictionSubtype.WRONG_OBJECT
    if ref is None:
        return IssueType.UNKNOWN, ObjectPart.UNKNOWN, ContradictionSubtype.ABSENT_DAMAGE
    issue = ref.visible_issue_type.value
    part = ref.visible_part.value
    if issue is IssueType.NONE:
        issue = IssueType.NONE
    subtype = {
        "CS-R03": ContradictionSubtype.ABSENT_DAMAGE,
        "CS-R04": ContradictionSubtype.WRONG_PART,
        "CS-R05": ContradictionSubtype.ISSUE_FAMILY_MISMATCH,
        "CS-R06": ContradictionSubtype.SEVERITY_EXAGGERATION,
    }.get(rule_id, ContradictionSubtype.ABSENT_DAMAGE)
    return issue, part, subtype


def _assign_supported_fields(
    resolution: ClaimResolutionContext,
    ref: ImageEvidence,
) -> tuple[IssueType, ObjectPart]:
    return ref.visible_issue_type.value, resolution.primary_object_part


def evaluate_verdict(
    validation: ValidationContext,
    trust: TrustAssessmentContext,
    consistency: ConsistencyContext,
    resolution: ClaimResolutionContext,
    *,
    images: list[ImageEvidence],
    claim_observation: ClaimObservation,
    claim_object: ClaimObject,
    evaluated_at: datetime,
) -> VerdictStageResult:
    """Evaluate claim_status per decision_matrix §3 using reconciliation contexts."""
    _ = trust
    predicates = validation.predicates
    best_ids = consistency.best_part_image_ids or predicates.best_part_image_ids
    records: list[RuleExecutionRecord] = []

    if not validation.evidence_standard_met:
        records.append(
            _record(
                "CS-R01",
                True,
                "Evidence standard not met; claim status is not_enough_information.",
                ("evidence_standard_met", "false"),
            )
        )
        issue_type, object_part = _assign_nei_fields(resolution, images, best_ids)
        verdict = VerdictDecision(
            row_id=validation.row_id,
            claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
            claim_status_rule_id="CS-R01",
            issue_type=issue_type,
            object_part=object_part,
            contradiction_subtype=None,
            decided_at=evaluated_at,
            claim_object=claim_object,
            evidence_standard_met=False,
        )
        return VerdictStageResult(verdict=verdict, rule_records=records)

    records.append(
        _record(
            "CS-R01",
            False,
            "Evidence standard met; CS-R01 does not apply.",
            ("evidence_standard_met", "true"),
        )
    )

    cs_r02 = _cs_r02_match(consistency, images)
    records.append(
        _record(
            "CS-R02",
            cs_r02,
            "Wrong object set with visible damage." if cs_r02 else "CS-R02 condition not met.",
            ("wrong_object_set", str(consistency.wrong_object_set).lower()),
        )
    )
    if cs_r02:
        issue_type, object_part, subtype = _assign_contradicted_fields("CS-R02", consistency, images[0])
        verdict = VerdictDecision(
            row_id=validation.row_id,
            claim_status=ClaimStatus.CONTRADICTED,
            claim_status_rule_id="CS-R02",
            issue_type=issue_type,
            object_part=object_part,
            contradiction_subtype=subtype,
            decided_at=evaluated_at,
            claim_object=claim_object,
            evidence_standard_met=True,
        )
        return VerdictStageResult(verdict=verdict, rule_records=records)

    cs_r03, ref03 = _cs_r03_match(predicates, resolution, images, best_ids)
    records.append(
        _record(
            "CS-R03",
            cs_r03,
            "Claimed part visible but no damage seen." if cs_r03 else "CS-R03 condition not met.",
            ("part_clear", str(predicates.part_clear).lower()),
        )
    )
    if cs_r03:
        issue_type, object_part, subtype = _assign_contradicted_fields("CS-R03", consistency, ref03)
        verdict = VerdictDecision(
            row_id=validation.row_id,
            claim_status=ClaimStatus.CONTRADICTED,
            claim_status_rule_id="CS-R03",
            issue_type=issue_type,
            object_part=object_part,
            contradiction_subtype=subtype,
            decided_at=evaluated_at,
            claim_object=claim_object,
            evidence_standard_met=True,
        )
        return VerdictStageResult(verdict=verdict, rule_records=records)

    cs_r04, ref04 = _cs_r04_match(predicates, resolution, images, best_ids)
    records.append(
        _record(
            "CS-R04",
            cs_r04,
            "Visible part differs from claimed primary part." if cs_r04 else "CS-R04 condition not met.",
        )
    )
    if cs_r04:
        issue_type, object_part, subtype = _assign_contradicted_fields("CS-R04", consistency, ref04)
        verdict = VerdictDecision(
            row_id=validation.row_id,
            claim_status=ClaimStatus.CONTRADICTED,
            claim_status_rule_id="CS-R04",
            issue_type=issue_type,
            object_part=object_part,
            contradiction_subtype=subtype,
            decided_at=evaluated_at,
            claim_object=claim_object,
            evidence_standard_met=True,
        )
        return VerdictStageResult(verdict=verdict, rule_records=records)

    cs_r05, ref05 = _cs_r05_match(predicates, resolution, images, best_ids, claim_object)
    records.append(
        _record(
            "CS-R05",
            cs_r05,
            "Visible issue family differs from claimed family." if cs_r05 else "CS-R05 condition not met.",
        )
    )
    if cs_r05:
        issue_type, object_part, subtype = _assign_contradicted_fields("CS-R05", consistency, ref05)
        verdict = VerdictDecision(
            row_id=validation.row_id,
            claim_status=ClaimStatus.CONTRADICTED,
            claim_status_rule_id="CS-R05",
            issue_type=issue_type,
            object_part=object_part,
            contradiction_subtype=subtype,
            decided_at=evaluated_at,
            claim_object=claim_object,
            evidence_standard_met=True,
        )
        return VerdictStageResult(verdict=verdict, rule_records=records)

    cs_r06, ref06 = _cs_r06_match(predicates, claim_observation, images, best_ids)
    records.append(
        _record(
            "CS-R06",
            cs_r06,
            "Claimed severity exceeds visible damage extent." if cs_r06 else "CS-R06 condition not met.",
        )
    )
    if cs_r06:
        issue_type, object_part, subtype = _assign_contradicted_fields("CS-R06", consistency, ref06)
        verdict = VerdictDecision(
            row_id=validation.row_id,
            claim_status=ClaimStatus.CONTRADICTED,
            claim_status_rule_id="CS-R06",
            issue_type=issue_type,
            object_part=object_part,
            contradiction_subtype=subtype,
            decided_at=evaluated_at,
            claim_object=claim_object,
            evidence_standard_met=True,
        )
        return VerdictStageResult(verdict=verdict, rule_records=records)

    cs_r07, ref07 = _cs_r07_match(
        predicates,
        resolution,
        images,
        best_ids,
        claim_object,
        contradiction_matched=False,
    )
    records.append(
        _record(
            "CS-R07",
            cs_r07,
            "Visible evidence supports claimed part and issue family." if cs_r07 else "CS-R07 condition not met.",
        )
    )
    if cs_r07 and ref07 is not None:
        issue_type, object_part = _assign_supported_fields(resolution, ref07)
        verdict = VerdictDecision(
            row_id=validation.row_id,
            claim_status=ClaimStatus.SUPPORTED,
            claim_status_rule_id="CS-R07",
            issue_type=issue_type,
            object_part=object_part,
            contradiction_subtype=None,
            decided_at=evaluated_at,
            claim_object=claim_object,
            evidence_standard_met=True,
        )
        return VerdictStageResult(verdict=verdict, rule_records=records)

    records.append(
        _record(
            "CS-R08",
            True,
            "Evidence standard met but no supported or contradicted rule matched.",
            ("claim_status", "not_enough_information"),
        )
    )
    issue_type, object_part = _assign_nei_fields(resolution, images, best_ids)
    verdict = VerdictDecision(
        row_id=validation.row_id,
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        claim_status_rule_id="CS-R08",
        issue_type=issue_type,
        object_part=object_part,
        contradiction_subtype=None,
        decided_at=evaluated_at,
        claim_object=claim_object,
        evidence_standard_met=True,
    )
    return VerdictStageResult(verdict=verdict, rule_records=records)
