"""Shared image selection helpers for severity and supporting rules."""

from __future__ import annotations

from contracts.decision import VerdictDecision
from contracts.enums import ClaimStatus, IssueType, ObjectPart
from contracts.observation import ImageEvidence
from contracts.resolution import ClaimResolutionContext
from rules.confidence import confidence_at_least


def verdict_ref(verdict: VerdictDecision) -> str:
    return f"{verdict.row_id}:verdict:{verdict.decided_at.isoformat()}"


def best_images(images: list[ImageEvidence], best_ids: list[str]) -> list[ImageEvidence]:
    if not best_ids:
        return list(images)
    id_set = set(best_ids)
    return [img for img in images if img.image_id in id_set]


def select_reference_image(
    images: list[ImageEvidence],
    best_ids: list[str],
) -> ImageEvidence | None:
    candidates = best_images(images, best_ids)
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


def image_qualifies_for_exclusion(
    image: ImageEvidence,
    *,
    identity_conflict_case: bool,
) -> tuple[bool, str | None]:
    if not image.claimed_primary_part_visible.value:
        return False, "claimed_primary_part_visible=false"
    if (
        not identity_conflict_case
        and not image.depicts_claim_object.value
        and confidence_at_least(image.depicts_claim_object.confidence, "medium")
    ):
        return False, "depicts_claim_object=false"
    return True, None


def apply_exclusions(
    candidate_ids: list[str],
    images: list[ImageEvidence],
    *,
    identity_conflict_case: bool,
) -> tuple[list[str], list[str], list[str]]:
    """Return selected ids, excluded ids, exclusion justifications."""
    by_id = {img.image_id: img for img in images}
    selected: list[str] = []
    excluded: list[str] = []
    reasons: list[str] = []

    for image_id in candidate_ids:
        image = by_id.get(image_id)
        if image is None:
            continue
        ok, reason = image_qualifies_for_exclusion(image, identity_conflict_case=identity_conflict_case)
        if not ok:
            excluded.append(image_id)
            if reason:
                reasons.append(f"{image_id}:{reason}")
            continue
        if image.is_blurry.value and confidence_at_least(image.is_blurry.confidence, "medium"):
            if len(candidate_ids) > 1:
                excluded.append(image_id)
                reasons.append(f"{image_id}:blurry_with_alternative")
                continue
        selected.append(image_id)

    return selected, excluded, reasons
