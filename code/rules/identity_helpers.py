"""Shared identity feature parsing for predicates, consistency, and sufficiency."""

from __future__ import annotations

from contracts.enums import IdentitySide
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.primitives import ConfidenceLevel
from contracts.reconciliation import ImagePairConflict
from rules.confidence import CONFIDENCE_RANK, confidence_at_least


def parse_identity_features(features: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for token in features:
        if ":" in token:
            key, val = token.split(":", 1)
            parsed[key.strip()] = val.strip()
    return parsed


def images_conflict_on_identity(a: ImageEvidence, b: ImageEvidence) -> tuple[bool, list[str]]:
    if not (
        a.depicts_claim_object.value
        and b.depicts_claim_object.value
        and confidence_at_least(a.depicts_claim_object.confidence, "medium")
        and confidence_at_least(b.depicts_claim_object.confidence, "medium")
    ):
        return False, []

    fa = parse_identity_features(a.vehicle_identity_features)
    fb = parse_identity_features(b.vehicle_identity_features)
    conflicts: list[str] = []
    for key in set(fa) & set(fb):
        if fa[key] != fb[key]:
            conflicts.append(f"{key}:{fa[key]} vs {key}:{fb[key]}")
    if not conflicts:
        return False, []
    high_on_both = (
        confidence_at_least(a.depicts_claim_object.confidence, "high")
        and confidence_at_least(b.depicts_claim_object.confidence, "high")
    )
    return high_on_both, conflicts


def collect_identity_conflict_pairs(
    images: list[ImageEvidence],
) -> list[ImagePairConflict]:
    pairs: list[ImagePairConflict] = []
    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            conflict, details = images_conflict_on_identity(images[i], images[j])
            if conflict:
                confidence: ConfidenceLevel = "high"
                pairs.append(
                    ImagePairConflict(
                        image_id_a=images[i].image_id,
                        image_id_b=images[j].image_id,
                        conflicting_features=details,
                        confidence=confidence,
                    )
                )
    return pairs


def identity_constraint_active(observation: ClaimObservation) -> bool:
    field = observation.identity_constraint_active
    return field.value and confidence_at_least(field.confidence, "medium")


def identity_matchable_across_best_set(
    observation: ClaimObservation,
    images: list[ImageEvidence],
    best_part_image_ids: list[str],
) -> tuple[bool, str]:
    """ESM-R07 / REQ_CAR_IDENTITY_OR_SIDE — decision_matrix §1.1 ESM-R07."""
    if not identity_constraint_active(observation):
        return True, "identity_constraint_inactive"

    best_images = [img for img in images if img.image_id in best_part_image_ids]
    if not best_images:
        return False, "no_images_in_best_part_set"

    claimed_side: IdentitySide | None = None
    if observation.identity_side is not None and confidence_at_least(observation.identity_side.confidence, "medium"):
        claimed_side = observation.identity_side.value

    claimed_color: str | None = None
    if observation.identity_color is not None and confidence_at_least(observation.identity_color.confidence, "medium"):
        claimed_color = observation.identity_color.value.lower()

    if claimed_side is None and claimed_color is None:
        return True, "no_explicit_identity_claim_at_medium_plus"

    for image in best_images:
        features = parse_identity_features(image.vehicle_identity_features)
        if claimed_side is not None:
            side_value = features.get("side")
            if side_value is None:
                return False, f"missing_side_on_{image.image_id}"
            if side_value != claimed_side.value:
                return False, f"side_mismatch_on_{image.image_id}"
        if claimed_color is not None:
            color_value = features.get("color")
            if color_value is None:
                return False, f"missing_color_on_{image.image_id}"
            if color_value.lower() != claimed_color:
                return False, f"color_mismatch_on_{image.image_id}"

    return True, "claimed_identity_matches_best_part_set"
