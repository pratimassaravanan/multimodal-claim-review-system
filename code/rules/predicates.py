"""Reusable derived predicates from decision_matrix §0.5.

Each predicate:
- has a stable ``predicate_id`` (PRED-*)
- is independently testable
- returns traceable ``outputs`` for DecisionTrace snapshots
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel, Field

from contracts.enums import ClaimObject, IssueFamily
from contracts.intake import ClaimContext
from contracts.observation import ImageEvidence
from contracts.primitives import ConfidenceLevel
from contracts.resolution import ClaimResolutionContext

CONFIDENCE_RANK: dict[ConfidenceLevel, int] = {"low": 1, "medium": 2, "high": 3}


class PredicatesSnapshot(BaseModel):
    """Aggregate of all §0.5 predicates for downstream rule matrices."""

    image_count: int = Field(ge=0)
    any_file_unreadable: bool
    best_part_confidence: ConfidenceLevel
    best_part_image_ids: list[str]
    part_clear: bool
    part_visible_low_only: bool
    no_part_visible: bool
    identity_conflict: bool
    wrong_object_set: bool
    any_non_original_high: bool
    contents_claim: bool
    contents_area_clear: bool
    all_images_unusable: bool

    model_config = {"frozen": True}


@dataclass(frozen=True)
class PredicateResult:
    predicate_id: str
    value: bool | int | str | list[str]
    outputs: dict[str, str]


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


def confidence_at_least(level: ConfidenceLevel, minimum: ConfidenceLevel) -> bool:
    return CONFIDENCE_RANK[level] >= CONFIDENCE_RANK[minimum]


def _confidence_at_least(level: ConfidenceLevel, minimum: ConfidenceLevel) -> bool:
    return confidence_at_least(level, minimum)


def _part_confidence(image: ImageEvidence) -> ConfidenceLevel:
    return image.claimed_primary_part_visible.confidence


def compute_image_count(images: list[ImageEvidence]) -> PredicateResult:
    count = len(images)
    return PredicateResult(
        predicate_id="PRED-IMAGE-COUNT",
        value=count,
        outputs={"image_count": str(count)},
    )


def compute_any_file_unreadable(images: list[ImageEvidence]) -> PredicateResult:
    unreadable = [img.image_id for img in images if not img.file_readable]
    value = len(unreadable) > 0
    return PredicateResult(
        predicate_id="PRED-ANY-FILE-UNREADABLE",
        value=value,
        outputs={
            "any_file_unreadable": str(value).lower(),
            "unreadable_image_ids": ",".join(unreadable) if unreadable else "none",
        },
    )


def compute_best_part_confidence(images: list[ImageEvidence]) -> PredicateResult:
    if not images:
        best: ConfidenceLevel = "low"
    else:
        best = max((_part_confidence(img) for img in images), key=lambda c: CONFIDENCE_RANK[c])
    return PredicateResult(
        predicate_id="PRED-BEST-PART-CONFIDENCE",
        value=best,
        outputs={"best_part_confidence": best},
    )


def compute_best_part_image_set(images: list[ImageEvidence]) -> PredicateResult:
    best_result = compute_best_part_confidence(images)
    best = best_result.value
    assert isinstance(best, str)
    image_ids = [
        img.image_id
        for img in images
        if _part_confidence(img) == best and _confidence_at_least(_part_confidence(img), "medium")
    ]
    return PredicateResult(
        predicate_id="PRED-BEST-PART-IMAGE-SET",
        value=image_ids,
        outputs={
            "best_part_confidence": best,
            "best_part_image_ids": ",".join(image_ids) if image_ids else "none",
        },
    )


def compute_part_clear(images: list[ImageEvidence]) -> PredicateResult:
    matching = [
        img.image_id
        for img in images
        if img.claimed_primary_part_visible.value
        and _confidence_at_least(img.claimed_primary_part_visible.confidence, "medium")
    ]
    value = len(matching) > 0
    return PredicateResult(
        predicate_id="PRED-PART-CLEAR",
        value=value,
        outputs={
            "part_clear": str(value).lower(),
            "qualifying_image_ids": ",".join(matching) if matching else "none",
        },
    )


def compute_part_visible_low_only(images: list[ImageEvidence]) -> PredicateResult:
    any_visible = any(img.claimed_primary_part_visible.value for img in images)
    best = compute_best_part_confidence(images).value
    assert isinstance(best, str)
    value = any_visible and best == "low"
    return PredicateResult(
        predicate_id="PRED-PART-VISIBLE-LOW-ONLY",
        value=value,
        outputs={
            "part_visible_low_only": str(value).lower(),
            "best_part_confidence": best,
        },
    )


def compute_no_part_visible(images: list[ImageEvidence]) -> PredicateResult:
    value = all(
        (not img.claimed_primary_part_visible.value)
        or (_part_confidence(img) == "low")
        for img in images
    ) if images else True
    return PredicateResult(
        predicate_id="PRED-NO-PART-VISIBLE",
        value=value,
        outputs={"no_part_visible": str(value).lower()},
    )


def _parse_identity_features(features: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for token in features:
        if ":" in token:
            key, val = token.split(":", 1)
            parsed[key.strip()] = val.strip()
    return parsed


def _images_conflict_on_identity(a: ImageEvidence, b: ImageEvidence) -> tuple[bool, list[str]]:
    if not (
        a.depicts_claim_object.value
        and b.depicts_claim_object.value
        and _confidence_at_least(a.depicts_claim_object.confidence, "medium")
        and _confidence_at_least(b.depicts_claim_object.confidence, "medium")
    ):
        return False, []

    fa = _parse_identity_features(a.vehicle_identity_features)
    fb = _parse_identity_features(b.vehicle_identity_features)
    conflicts: list[str] = []
    for key in set(fa) & set(fb):
        if fa[key] != fb[key]:
            conflicts.append(f"{key}:{fa[key]} vs {key}:{fb[key]}")
    if not conflicts:
        return False, []
    high_on_both = (
        _confidence_at_least(a.depicts_claim_object.confidence, "high")
        and _confidence_at_least(b.depicts_claim_object.confidence, "high")
    )
    return high_on_both, conflicts


def compute_identity_conflict(claim_object: ClaimObject, images: list[ImageEvidence]) -> PredicateResult:
    if claim_object is not ClaimObject.CAR or len(images) < 2:
        return PredicateResult(
            predicate_id="PRED-IDENTITY-CONFLICT",
            value=False,
            outputs={"identity_conflict": "false", "reason": "not_applicable"},
        )

    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            conflict, details = _images_conflict_on_identity(images[i], images[j])
            if conflict:
                return PredicateResult(
                    predicate_id="PRED-IDENTITY-CONFLICT",
                    value=True,
                    outputs={
                        "identity_conflict": "true",
                        "image_id_a": images[i].image_id,
                        "image_id_b": images[j].image_id,
                        "conflicting_features": ";".join(details),
                    },
                )

    return PredicateResult(
        predicate_id="PRED-IDENTITY-CONFLICT",
        value=False,
        outputs={"identity_conflict": "false"},
    )


def compute_wrong_object_set(images: list[ImageEvidence]) -> PredicateResult:
    medium_plus = [
        img
        for img in images
        if _confidence_at_least(img.depicts_claim_object.confidence, "medium")
    ]
    if not medium_plus:
        value = False
    else:
        value = all(not img.depicts_claim_object.value for img in medium_plus)
    return PredicateResult(
        predicate_id="PRED-WRONG-OBJECT-SET",
        value=value,
        outputs={
            "wrong_object_set": str(value).lower(),
            "medium_plus_image_count": str(len(medium_plus)),
        },
    )


def compute_any_non_original_high(images: list[ImageEvidence]) -> PredicateResult:
    hits = [
        img.image_id
        for img in images
        if img.is_non_original_image.value
        and _confidence_at_least(img.is_non_original_image.confidence, "high")
    ]
    value = len(hits) > 0
    return PredicateResult(
        predicate_id="PRED-ANY-NON-ORIGINAL-HIGH",
        value=value,
        outputs={
            "any_non_original_high": str(value).lower(),
            "image_ids": ",".join(hits) if hits else "none",
        },
    )


def compute_contents_claim(resolution: ClaimResolutionContext) -> PredicateResult:
    value = resolution.primary_issue_family is IssueFamily.CONTENTS_OR_ITEM
    return PredicateResult(
        predicate_id="PRED-CONTENTS-CLAIM",
        value=value,
        outputs={
            "contents_claim": str(value).lower(),
            "primary_issue_family": resolution.primary_issue_family.value,
        },
    )


def compute_contents_area_clear(images: list[ImageEvidence]) -> PredicateResult:
    qualifying = [
        img.image_id
        for img in images
        if img.package_is_opened.value
        and img.contents_area_visible.value
        and _confidence_at_least(img.package_is_opened.confidence, "medium")
        and _confidence_at_least(img.contents_area_visible.confidence, "medium")
    ]
    value = len(qualifying) > 0
    return PredicateResult(
        predicate_id="PRED-CONTENTS-AREA-CLEAR",
        value=value,
        outputs={
            "contents_area_clear": str(value).lower(),
            "qualifying_image_ids": ",".join(qualifying) if qualifying else "none",
        },
    )


def compute_all_images_unusable(images: list[ImageEvidence]) -> PredicateResult:
    value = bool(images) and all(not img.usable_for_automated_review for img in images)
    return PredicateResult(
        predicate_id="PRED-ALL-IMAGES-UNUSABLE",
        value=value,
        outputs={"all_images_unusable": str(value).lower()},
    )


_PREDICATE_REGISTRY: dict[str, Callable[..., PredicateResult]] = {
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
) -> PredicateResult:
    """Evaluate a single predicate by ID."""
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

    fn = _PREDICATE_REGISTRY[predicate_id]
    return fn(images)


def compute_all_predicates(
    claim: ClaimContext,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
) -> tuple[PredicatesSnapshot, list[PredicateResult]]:
    """Compute all §0.5 predicates and return snapshot + traceable results."""
    results: list[PredicateResult] = [
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

    best_conf = results[2].value
    assert isinstance(best_conf, str)
    best_ids = results[3].value
    assert isinstance(best_ids, list)

    snapshot = PredicatesSnapshot(
        image_count=len(images),
        any_file_unreadable=bool(results[1].value),
        best_part_confidence=best_conf,  # type: ignore[arg-type]
        best_part_image_ids=best_ids,
        part_clear=bool(results[4].value),
        part_visible_low_only=bool(results[5].value),
        no_part_visible=bool(results[6].value),
        identity_conflict=bool(results[7].value),
        wrong_object_set=bool(results[8].value),
        any_non_original_high=bool(results[9].value),
        contents_claim=bool(results[10].value),
        contents_area_clear=bool(results[11].value),
        all_images_unusable=bool(results[12].value),
    )
    return snapshot, results
