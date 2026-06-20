"""Supporting image selection — decision_matrix §5 (SI-R01..SI-R07)."""

from __future__ import annotations

from datetime import datetime

from contracts.decision import SupportingImageDecision, VerdictDecision
from contracts.enums import ClaimObject, ClaimStatus, IssueType
from contracts.observation import ImageEvidence
from contracts.reconciliation import ConsistencyContext, ValidationContext
from contracts.resolution import ClaimResolutionContext
from ontology.issue_families import map_issue_type_to_family
from rules.confidence import confidence_at_least
from rules.image_helpers import apply_exclusions, best_images, select_reference_image, verdict_ref
from rules.types import RuleExecutionRecord, SupportingImageStageResult, TraceField

SI_RULE_IDS = (
    "SI-R01",
    "SI-R02",
    "SI-R03",
    "SI-R04",
    "SI-R05",
    "SI-R06",
    "SI-R07",
)


def _record(rule_id: str, outcome: bool, justification: str, *pairs: tuple[str, str]) -> RuleExecutionRecord:
    return RuleExecutionRecord(
        rule_id=rule_id,
        outcome=outcome,
        justification=justification,
        trace_fields=[TraceField(key=k, value=v) for k, v in pairs],
    )


def _images_showing_claimed_issue(
    images: list[ImageEvidence],
    best_ids: list[str],
    resolution: ClaimResolutionContext,
    claim_object: ClaimObject,
) -> list[ImageEvidence]:
    matches: list[ImageEvidence] = []
    for image in best_images(images, best_ids):
        if not image.claimed_primary_part_visible.value:
            continue
        if not confidence_at_least(image.visible_issue_type.confidence, "medium"):
            continue
        if image.visible_issue_type.value is IssueType.NONE:
            continue
        if map_issue_type_to_family(
            image.visible_issue_type.value,
            claim_object,
            image.visible_part.value,
        ) != resolution.primary_issue_family:
            continue
        matches.append(image)
    return matches


def _pick_minimal_issue_image(candidates: list[ImageEvidence]) -> list[str]:
    if not candidates:
        return []
    chosen = max(
        candidates,
        key=lambda img: (
            confidence_at_least(img.visible_issue_type.confidence, "high"),
            confidence_at_least(img.claimed_primary_part_visible.confidence, "high"),
            confidence_at_least(img.visible_issue_type.confidence, "medium"),
            img.image_id,
        ),
    )
    return [chosen.image_id]


def _wrong_object_image_id(images: list[ImageEvidence]) -> str | None:
    for image in images:
        if not image.depicts_claim_object.value and confidence_at_least(
            image.depicts_claim_object.confidence, "medium"
        ):
            return image.image_id
    return images[0].image_id if images else None


def _part_visible_image_ids(images: list[ImageEvidence]) -> list[str]:
    ids: list[str] = []
    for image in images:
        if image.claimed_primary_part_visible.value and confidence_at_least(
            image.claimed_primary_part_visible.confidence, "medium"
        ):
            ids.append(image.image_id)
    return sorted(ids)


def _finalize_selection(
    *,
    row_id: str,
    verdict: VerdictDecision,
    rule_id: str,
    candidate_ids: list[str],
    images: list[ImageEvidence],
    identity_conflict_case: bool,
    rationale: str,
    evaluated_at: datetime,
    allowed_image_ids: list[str],
) -> SupportingImageDecision:
    selected, excluded, exclusion_reasons = apply_exclusions(
        candidate_ids,
        images,
        identity_conflict_case=identity_conflict_case,
    )
    if exclusion_reasons:
        rationale = f"{rationale}; {'; '.join(exclusion_reasons)}"
    return SupportingImageDecision(
        row_id=row_id,
        supporting_image_ids=selected,
        supporting_image_rule_id=rule_id,
        excluded_image_ids=excluded,
        selection_rationale=rationale,
        verdict_ref=verdict_ref(verdict),
        decided_at=evaluated_at,
        allowed_image_ids=allowed_image_ids,
    )


def evaluate_supporting_images(
    verdict: VerdictDecision,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
    validation: ValidationContext,
    consistency: ConsistencyContext,
    *,
    claim_object: ClaimObject,
    evaluated_at: datetime,
) -> SupportingImageStageResult:
    """Select supporting images that substantiate the verdict."""
    records: list[RuleExecutionRecord] = []
    predicates = validation.predicates
    best_ids = consistency.best_part_image_ids or predicates.best_part_image_ids
    allowed_image_ids = [img.image_id for img in images]
    ref = verdict_ref(verdict)

    if verdict.claim_status is ClaimStatus.NOT_ENOUGH_INFORMATION:
        if predicates.identity_conflict:
            records.append(
                _record(
                    "SI-R01",
                    True,
                    "Identity conflict on NEI row; include all images to document conflict.",
                    ("identity_conflict", "true"),
                )
            )
            records.append(
                _record(
                    "SI-R02",
                    False,
                    "SI-R02 does not apply when identity conflict documents all images.",
                )
            )
            supporting = _finalize_selection(
                row_id=verdict.row_id,
                verdict=verdict,
                rule_id="SI-R01",
                candidate_ids=allowed_image_ids,
                images=images,
                identity_conflict_case=True,
                rationale="All row images included to document identity conflict",
                evaluated_at=evaluated_at,
                allowed_image_ids=allowed_image_ids,
            )
            return SupportingImageStageResult(supporting=supporting, rule_records=records)

        records.append(_record("SI-R01", False, "No identity conflict on NEI row."))
        records.append(
            _record(
                "SI-R02",
                True,
                "NEI without identity conflict yields no supporting images.",
                ("claim_status", verdict.claim_status.value),
            )
        )
        decision = SupportingImageDecision(
            row_id=verdict.row_id,
            supporting_image_ids=[],
            supporting_image_rule_id="SI-R02",
            excluded_image_ids=[],
            selection_rationale="Not enough information without identity conflict",
            verdict_ref=ref,
            decided_at=evaluated_at,
            allowed_image_ids=allowed_image_ids,
        )
        return SupportingImageStageResult(supporting=decision, rule_records=records)

    records.append(_record("SI-R01", False, "Claim status is not NEI."))
    records.append(_record("SI-R02", False, "Claim status is not NEI."))

    if verdict.claim_status is ClaimStatus.SUPPORTED:
        if len(images) == 1 and predicates.part_clear:
            matched = images[0].claimed_primary_part_visible.value and confidence_at_least(
                images[0].claimed_primary_part_visible.confidence, "medium"
            )
            records.append(
                _record(
                    "SI-R03",
                    matched,
                    "Single-image supported row with part clear on the image."
                    if matched
                    else "Single-image row but part not clear on image.",
                    ("image_count", "1"),
                    ("part_clear", str(predicates.part_clear).lower()),
                )
            )
            records.append(_record("SI-R04", False, "Multi-image rule not applicable."))
            if matched:
                supporting = _finalize_selection(
                    row_id=verdict.row_id,
                    verdict=verdict,
                    rule_id="SI-R03",
                    candidate_ids=[images[0].image_id],
                    images=images,
                    identity_conflict_case=False,
                    rationale="Single image shows claimed primary part clearly",
                    evaluated_at=evaluated_at,
                    allowed_image_ids=allowed_image_ids,
                )
                return SupportingImageStageResult(supporting=supporting, rule_records=records)

        issue_images = _images_showing_claimed_issue(images, best_ids, resolution, claim_object)
        candidate_ids = [image.image_id for image in issue_images]
        selected_ids, excluded_ids, exclusion_reasons = apply_exclusions(
            candidate_ids,
            images,
            identity_conflict_case=False,
        )
        picked = _pick_minimal_issue_image(
            [image for image in issue_images if image.image_id in selected_ids]
        )
        matched = len(picked) > 0
        records.append(
            _record(
                "SI-R03",
                False,
                "Multi-image or part-not-clear row; SI-R03 does not apply.",
                ("image_count", str(len(images))),
            )
        )
        records.append(
            _record(
                "SI-R04",
                matched,
                "Minimal best-set image shows claimed issue at medium or higher confidence."
                if matched
                else "No best-set image shows claimed issue clearly.",
                ("candidate_count", str(len(issue_images))),
                ("selected", ";".join(picked) or "none"),
            )
        )
        for rule_id in ("SI-R05", "SI-R06", "SI-R07"):
            records.append(_record(rule_id, False, f"{rule_id} applies only to contradicted claims."))

        supporting = _finalize_selection(
            row_id=verdict.row_id,
            verdict=verdict,
            rule_id="SI-R04",
            candidate_ids=picked,
            images=images,
            identity_conflict_case=False,
            rationale="Minimal image from best-part set showing claimed issue",
            evaluated_at=evaluated_at,
            allowed_image_ids=allowed_image_ids,
        )
        if excluded_ids and not supporting.excluded_image_ids:
            supporting = supporting.model_copy(
                update={
                    "excluded_image_ids": excluded_ids,
                    "selection_rationale": (
                        f"{supporting.selection_rationale}; {'; '.join(exclusion_reasons)}"
                        if exclusion_reasons
                        else supporting.selection_rationale
                    ),
                }
            )
        elif exclusion_reasons:
            supporting = supporting.model_copy(
                update={
                    "selection_rationale": f"{supporting.selection_rationale}; {'; '.join(exclusion_reasons)}",
                }
            )
        return SupportingImageStageResult(supporting=supporting, rule_records=records)

    # Contradicted
    records.append(_record("SI-R03", False, "Contradicted claim; SI-R03 does not apply."))
    records.append(_record("SI-R04", False, "Contradicted claim; SI-R04 does not apply."))

    if verdict.claim_status_rule_id == "CS-R02" or consistency.wrong_object_set:
        wrong_id = _wrong_object_image_id(images)
        records.append(
            _record(
                "SI-R06",
                wrong_id is not None,
                "Wrong-object contradiction uses image showing non-claim object.",
                ("selected", wrong_id or "none"),
            )
        )
        records.append(_record("SI-R05", False, "Wrong-object case handled by SI-R06."))
        records.append(_record("SI-R07", False, "Wrong-object case handled by SI-R06."))
        supporting = _finalize_selection(
            row_id=verdict.row_id,
            verdict=verdict,
            rule_id="SI-R06",
            candidate_ids=[wrong_id] if wrong_id else [],
            images=images,
            identity_conflict_case=False,
            rationale="Image shows object inconsistent with claim",
            evaluated_at=evaluated_at,
            allowed_image_ids=allowed_image_ids,
        )
        return SupportingImageStageResult(supporting=supporting, rule_records=records)

    records.append(_record("SI-R06", False, "Not a wrong-object contradiction."))

    part_visible_ids = _part_visible_image_ids(images)
    if verdict.claim_status_rule_id == "CS-R03" and len(part_visible_ids) >= 2:
        records.append(
            _record(
                "SI-R07",
                True,
                "Absent-damage contradiction with multiple angles showing claimed part.",
                ("selected", ";".join(part_visible_ids)),
            )
        )
        records.append(_record("SI-R05", False, "Multi-angle absent-damage handled by SI-R07."))
        supporting = _finalize_selection(
            row_id=verdict.row_id,
            verdict=verdict,
            rule_id="SI-R07",
            candidate_ids=part_visible_ids,
            images=images,
            identity_conflict_case=False,
            rationale="All images showing claimed part document intact seal or absent damage",
            evaluated_at=evaluated_at,
            allowed_image_ids=allowed_image_ids,
        )
        return SupportingImageStageResult(supporting=supporting, rule_records=records)

    records.append(
        _record(
            "SI-R07",
            False,
            "SI-R07 requires CS-R03 with two or more part-visible images.",
            ("part_visible_count", str(len(part_visible_ids))),
        )
    )

    ref_image = select_reference_image(images, best_ids)
    proof_id = ref_image.image_id if ref_image else (images[0].image_id if images else None)
    matched = proof_id is not None and verdict.claim_status_rule_id in {
        "CS-R03",
        "CS-R04",
        "CS-R05",
        "CS-R06",
    }
    records.append(
        _record(
            "SI-R05",
            matched,
            "Reference image proves part mismatch or absent damage contradiction."
            if matched
            else "SI-R05 conditions not met.",
            ("claim_status_rule_id", verdict.claim_status_rule_id),
            ("selected", proof_id or "none"),
        )
    )
    supporting = _finalize_selection(
        row_id=verdict.row_id,
        verdict=verdict,
        rule_id="SI-R05",
        candidate_ids=[proof_id] if proof_id and matched else [],
        images=images,
        identity_conflict_case=False,
        rationale="Image proves contradiction against claimed part or damage",
        evaluated_at=evaluated_at,
        allowed_image_ids=allowed_image_ids,
    )
    return SupportingImageStageResult(supporting=supporting, rule_records=records)
