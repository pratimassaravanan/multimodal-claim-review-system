"""Reusable derived predicates from decision_matrix §0.5."""

from __future__ import annotations

from typing import Callable

from contracts.enums import ClaimObject, IssueFamily
from contracts.intake import ClaimContext
from contracts.observation import ImageEvidence
from contracts.primitives import ConfidenceLevel
from contracts.resolution import ClaimResolutionContext
from rules.confidence import CONFIDENCE_RANK, confidence_at_least
from rules.identity_helpers import images_conflict_on_identity
from rules.types import (
    PredicateTraceRecord,
    PredicatesEvaluationBundle,
    PredicatesSnapshot,
    TraceField,
)

PREDICATE_IDS = (
    "PRED-IMAGE-COUNT",
    "PRED-ANY-FILE-UNREADABLE",
    "PRED-BEST-PART-CONFIDENCE",
    "PRED-BEST-PART-IMAGE-SET",
    "PRED-PART-CLEAR",
    "PRED-PART-VISIBLE-LOW-ONLY",
    "PRED-NO-PART-VISIBLE",
    "PRED-IDENTITY-CONFLICT",
    "PRED-WRONG-OBJECT-SET",
    "PRED-ANY-NON-ORIGINAL-HIGH",
    "PRED-CONTENTS-CLAIM",
    "PRED-CONTENTS-AREA-CLEAR",
    "PRED-ALL-IMAGES-UNUSABLE",
)


def _part_confidence(image: ImageEvidence) -> ConfidenceLevel:
    return image.claimed_primary_part_visible.confidence


def _fields(*pairs: tuple[str, str]) -> list[TraceField]:
    return [TraceField(key=key, value=value) for key, value in pairs]


def _record(
    predicate_id: str,
    outcome: bool,
    value_text: str,
    justification: str,
    *pairs: tuple[str, str],
) -> PredicateTraceRecord:
    return PredicateTraceRecord(
        predicate_id=predicate_id,
        outcome=outcome,
        value_text=value_text,
        justification=justification,
        trace_fields=_fields(*pairs),
    )


def compute_image_count(images: list[ImageEvidence]) -> PredicateTraceRecord:
    count = len(images)
    return _record(
        "PRED-IMAGE-COUNT",
        True,
        str(count),
        f"Row contains {count} image(s).",
        ("image_count", str(count)),
    )


def compute_any_file_unreadable(images: list[ImageEvidence]) -> PredicateTraceRecord:
    unreadable = [img.image_id for img in images if not img.file_readable]
    value = len(unreadable) > 0
    return _record(
        "PRED-ANY-FILE-UNREADABLE",
        value,
        str(value).lower(),
        "At least one file is unreadable." if value else "All files are readable.",
        ("any_file_unreadable", str(value).lower()),
        ("unreadable_image_ids", ",".join(unreadable) if unreadable else "none"),
    )


def compute_best_part_confidence(images: list[ImageEvidence]) -> PredicateTraceRecord:
    if not images:
        best: ConfidenceLevel = "low"
    else:
        best = max((_part_confidence(img) for img in images), key=lambda c: CONFIDENCE_RANK[c])
    return _record(
        "PRED-BEST-PART-CONFIDENCE",
        True,
        best,
        f"Best claimed-primary-part confidence across images is {best}.",
        ("best_part_confidence", best),
    )


def compute_best_part_image_set(images: list[ImageEvidence]) -> PredicateTraceRecord:
    best = compute_best_part_confidence(images).value_text
    image_ids = [
        img.image_id
        for img in images
        if _part_confidence(img) == best and confidence_at_least(_part_confidence(img), "medium")
    ]
    return _record(
        "PRED-BEST-PART-IMAGE-SET",
        bool(image_ids),
        ",".join(image_ids) if image_ids else "none",
        "Images at best part confidence with medium or higher visibility.",
        ("best_part_confidence", best),
        ("best_part_image_ids", ",".join(image_ids) if image_ids else "none"),
    )


def compute_part_clear(images: list[ImageEvidence]) -> PredicateTraceRecord:
    matching = [
        img.image_id
        for img in images
        if img.claimed_primary_part_visible.value
        and confidence_at_least(img.claimed_primary_part_visible.confidence, "medium")
    ]
    value = len(matching) > 0
    return _record(
        "PRED-PART-CLEAR",
        value,
        str(value).lower(),
        "Claimed primary part visible at medium or higher." if value else "No clear part visibility.",
        ("part_clear", str(value).lower()),
        ("qualifying_image_ids", ",".join(matching) if matching else "none"),
    )


def compute_part_visible_low_only(images: list[ImageEvidence]) -> PredicateTraceRecord:
    any_visible = any(img.claimed_primary_part_visible.value for img in images)
    best = compute_best_part_confidence(images).value_text
    value = any_visible and best == "low"
    return _record(
        "PRED-PART-VISIBLE-LOW-ONLY",
        value,
        str(value).lower(),
        "Part visible only at low confidence." if value else "Part not limited to low confidence only.",
        ("part_visible_low_only", str(value).lower()),
        ("best_part_confidence", best),
    )


def compute_no_part_visible(images: list[ImageEvidence]) -> PredicateTraceRecord:
    value = (
        all(
            (not img.claimed_primary_part_visible.value)
            or (_part_confidence(img) == "low")
            for img in images
        )
        if images
        else True
    )
    return _record(
        "PRED-NO-PART-VISIBLE",
        value,
        str(value).lower(),
        "No image shows the claimed part at medium or higher." if value else "Some image shows part visibility.",
        ("no_part_visible", str(value).lower()),
    )


def compute_identity_conflict(claim_object: ClaimObject, images: list[ImageEvidence]) -> PredicateTraceRecord:
    if claim_object is not ClaimObject.CAR or len(images) < 2:
        return _record(
            "PRED-IDENTITY-CONFLICT",
            False,
            "false",
            "Identity conflict predicate not applicable for this claim object or image count.",
            ("identity_conflict", "false"),
            ("reason", "not_applicable"),
        )

    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            conflict, details = images_conflict_on_identity(images[i], images[j])
            if conflict:
                return _record(
                    "PRED-IDENTITY-CONFLICT",
                    True,
                    "true",
                    "Conflicting vehicle identity features at high confidence.",
                    ("identity_conflict", "true"),
                    ("image_id_a", images[i].image_id),
                    ("image_id_b", images[j].image_id),
                    ("conflicting_features", ";".join(details)),
                )

    return _record(
        "PRED-IDENTITY-CONFLICT",
        False,
        "false",
        "No identity conflict detected across image pairs.",
        ("identity_conflict", "false"),
    )


def compute_wrong_object_set(images: list[ImageEvidence]) -> PredicateTraceRecord:
    medium_plus = [
        img for img in images if confidence_at_least(img.depicts_claim_object.confidence, "medium")
    ]
    value = bool(medium_plus) and all(not img.depicts_claim_object.value for img in medium_plus)
    return _record(
        "PRED-WRONG-OBJECT-SET",
        value,
        str(value).lower(),
        "All medium-plus images depict a non-claim object." if value else "Claim object depicted on at least one image.",
        ("wrong_object_set", str(value).lower()),
        ("medium_plus_image_count", str(len(medium_plus))),
    )


def compute_any_non_original_high(images: list[ImageEvidence]) -> PredicateTraceRecord:
    hits = [
        img.image_id
        for img in images
        if img.is_non_original_image.value
        and confidence_at_least(img.is_non_original_image.confidence, "high")
    ]
    value = len(hits) > 0
    return _record(
        "PRED-ANY-NON-ORIGINAL-HIGH",
        value,
        str(value).lower(),
        "Non-original image detected at high confidence." if value else "No high-confidence non-original image.",
        ("any_non_original_high", str(value).lower()),
        ("image_ids", ",".join(hits) if hits else "none"),
    )


def compute_contents_claim(resolution: ClaimResolutionContext) -> PredicateTraceRecord:
    value = resolution.primary_issue_family is IssueFamily.CONTENTS_OR_ITEM
    return _record(
        "PRED-CONTENTS-CLAIM",
        value,
        str(value).lower(),
        "Primary issue family is contents_or_item." if value else "Primary issue family is not contents_or_item.",
        ("contents_claim", str(value).lower()),
        ("primary_issue_family", resolution.primary_issue_family.value),
    )


def compute_contents_area_clear(images: list[ImageEvidence]) -> PredicateTraceRecord:
    qualifying = [
        img.image_id
        for img in images
        if img.package_is_opened.value
        and img.contents_area_visible.value
        and confidence_at_least(img.package_is_opened.confidence, "medium")
        and confidence_at_least(img.contents_area_visible.confidence, "medium")
    ]
    value = len(qualifying) > 0
    return _record(
        "PRED-CONTENTS-AREA-CLEAR",
        value,
        str(value).lower(),
        "Opened package with visible contents area." if value else "Contents area not clearly visible.",
        ("contents_area_clear", str(value).lower()),
        ("qualifying_image_ids", ",".join(qualifying) if qualifying else "none"),
    )


def compute_all_images_unusable(images: list[ImageEvidence]) -> PredicateTraceRecord:
    value = bool(images) and all(not img.usable_for_automated_review for img in images)
    return _record(
        "PRED-ALL-IMAGES-UNUSABLE",
        value,
        str(value).lower(),
        "Every image is unusable for automated review." if value else "At least one image is usable.",
        ("all_images_unusable", str(value).lower()),
    )


_PREDICATE_REGISTRY: dict[str, Callable[..., PredicateTraceRecord]] = {
    "PRED-IMAGE-COUNT": compute_image_count,
    "PRED-ANY-FILE-UNREADABLE": compute_any_file_unreadable,
    "PRED-BEST-PART-CONFIDENCE": compute_best_part_confidence,
    "PRED-BEST-PART-IMAGE-SET": compute_best_part_image_set,
    "PRED-PART-CLEAR": compute_part_clear,
    "PRED-PART-VISIBLE-LOW-ONLY": compute_part_visible_low_only,
    "PRED-NO-PART-VISIBLE": compute_no_part_visible,
    "PRED-IDENTITY-CONFLICT": compute_identity_conflict,
    "PRED-WRONG-OBJECT-SET": compute_wrong_object_set,
    "PRED-ANY-NON-ORIGINAL-HIGH": compute_any_non_original_high,
    "PRED-CONTENTS-CLAIM": compute_contents_claim,
    "PRED-CONTENTS-AREA-CLEAR": compute_contents_area_clear,
    "PRED-ALL-IMAGES-UNUSABLE": compute_all_images_unusable,
}


def compute_predicate(
    predicate_id: str,
    *,
    claim: ClaimContext | None = None,
    images: list[ImageEvidence] | None = None,
    resolution: ClaimResolutionContext | None = None,
) -> PredicateTraceRecord:
    if predicate_id not in _PREDICATE_REGISTRY:
        raise KeyError(f"Unknown predicate_id: {predicate_id}")

    images = images or []
    if predicate_id == "PRED-IDENTITY-CONFLICT":
        if claim is None:
            raise ValueError("claim is required for PRED-IDENTITY-CONFLICT")
        return compute_identity_conflict(claim.claim_object, images)
    if predicate_id == "PRED-CONTENTS-CLAIM":
        if resolution is None:
            raise ValueError("resolution is required for PRED-CONTENTS-CLAIM")
        return compute_contents_claim(resolution)

    return _PREDICATE_REGISTRY[predicate_id](images)


def compute_all_predicates(
    claim: ClaimContext,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
) -> PredicatesEvaluationBundle:
    records = [
        compute_image_count(images),
        compute_any_file_unreadable(images),
        compute_best_part_confidence(images),
        compute_best_part_image_set(images),
        compute_part_clear(images),
        compute_part_visible_low_only(images),
        compute_no_part_visible(images),
        compute_identity_conflict(claim.claim_object, images),
        compute_wrong_object_set(images),
        compute_any_non_original_high(images),
        compute_contents_claim(resolution),
        compute_contents_area_clear(images),
        compute_all_images_unusable(images),
    ]

    snapshot = PredicatesSnapshot(
        image_count=len(images),
        any_file_unreadable=records[1].outcome,
        best_part_confidence=records[2].value_text,  # type: ignore[arg-type]
        best_part_image_ids=(
            records[3].value_text.split(",") if records[3].value_text != "none" else []
        ),
        part_clear=records[4].outcome,
        part_visible_low_only=records[5].outcome,
        no_part_visible=records[6].outcome,
        identity_conflict=records[7].outcome,
        wrong_object_set=records[8].outcome,
        any_non_original_high=records[9].outcome,
        contents_claim=records[10].outcome,
        contents_area_clear=records[11].outcome,
        all_images_unusable=records[12].outcome,
    )
    return PredicatesEvaluationBundle(snapshot=snapshot, records=records)
