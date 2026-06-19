"""Evidence requirement catalog and active-requirement resolution.

Maps ``dataset/evidence_requirements.csv`` and decision_matrix §0.3 / §1.2.
No verdict, severity, or risk logic.
"""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import BaseModel, Field

from contracts.enums import ClaimObject, IssueFamily
from contracts.observation import ImageEvidence
from contracts.primitives import RuleId
from ontology.issue_families import (
    CAR_IDENTITY_REQUIREMENT_ID,
    FAMILY_REQUIREMENT_IDS,
    MULTI_IMAGE_REQUIREMENT_ID,
    UNIVERSAL_REQUIREMENT_IDS,
)
from rules.predicates import PredicatesSnapshot, confidence_at_least


class RequirementSpec(BaseModel):
    requirement_id: RuleId
    claim_object: str = Field(description="car | laptop | package | all")
    applies_to: str
    minimum_image_evidence: str

    model_config = {"frozen": True}


# Canonical catalog — mirrors dataset/evidence_requirements.csv
REQUIREMENTS_CATALOG: dict[str, RequirementSpec] = {
    "REQ_GENERAL_OBJECT_PART": RequirementSpec(
        requirement_id="REQ_GENERAL_OBJECT_PART",
        claim_object="all",
        applies_to="general claim review",
        minimum_image_evidence=(
            "The claimed object and relevant part should be visible clearly enough "
            "to inspect the claimed condition."
        ),
    ),
    "REQ_GENERAL_MULTI_IMAGE": RequirementSpec(
        requirement_id="REQ_GENERAL_MULTI_IMAGE",
        claim_object="all",
        applies_to="multi-image rows",
        minimum_image_evidence=(
            "Each submitted image should be considered separately; at least one relevant "
            "image should show the claimed object or part clearly enough to evaluate the claim."
        ),
    ),
    "REQ_CAR_BODY_PANEL": RequirementSpec(
        requirement_id="REQ_CAR_BODY_PANEL",
        claim_object="car",
        applies_to="dent or scratch",
        minimum_image_evidence=(
            "The claimed car panel or bumper should be visible from an angle where "
            "surface marks or deformation can be assessed."
        ),
    ),
    "REQ_CAR_GLASS_LIGHT_MIRROR": RequirementSpec(
        requirement_id="REQ_CAR_GLASS_LIGHT_MIRROR",
        claim_object="car",
        applies_to="crack, broken, or missing part",
        minimum_image_evidence=(
            "The claimed glass, light, mirror, or component should be visible clearly "
            "enough to inspect cracks, breakage, or missing parts."
        ),
    ),
    "REQ_CAR_IDENTITY_OR_SIDE": RequirementSpec(
        requirement_id="REQ_CAR_IDENTITY_OR_SIDE",
        claim_object="car",
        applies_to="vehicle identity or orientation",
        minimum_image_evidence=(
            "When the claim depends on vehicle identity, side, or orientation, the image "
            "set should show enough context to match the claimed vehicle and part."
        ),
    ),
    "REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD": RequirementSpec(
        requirement_id="REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD",
        claim_object="laptop",
        applies_to="screen, keyboard, or trackpad",
        minimum_image_evidence=(
            "The claimed laptop screen, keyboard, or trackpad area should be visible "
            "clearly enough to inspect cracks, stains, missing keys, or surface damage."
        ),
    ),
    "REQ_LAPTOP_BODY_HINGE_PORT": RequirementSpec(
        requirement_id="REQ_LAPTOP_BODY_HINGE_PORT",
        claim_object="laptop",
        applies_to="hinge, lid, corner, body, or port",
        minimum_image_evidence=(
            "The claimed laptop hinge, lid, corner, body, base, or port should be visible "
            "with enough context to identify the relevant laptop part."
        ),
    ),
    "REQ_PACKAGE_EXTERIOR": RequirementSpec(
        requirement_id="REQ_PACKAGE_EXTERIOR",
        claim_object="package",
        applies_to="crushed, torn, or seal damage",
        minimum_image_evidence=(
            "The package exterior and claimed side, corner, flap, or seal should be visible "
            "clearly enough to inspect packaging damage."
        ),
    ),
    "REQ_PACKAGE_LABEL_OR_STAIN": RequirementSpec(
        requirement_id="REQ_PACKAGE_LABEL_OR_STAIN",
        claim_object="package",
        applies_to="water, stain, or label damage",
        minimum_image_evidence=(
            "The affected package surface or label should be visible clearly enough to assess "
            "stain, water damage, label readability, or label damage."
        ),
    ),
    "REQ_PACKAGE_CONTENTS": RequirementSpec(
        requirement_id="REQ_PACKAGE_CONTENTS",
        claim_object="package",
        applies_to="contents or inner item",
        minimum_image_evidence=(
            "The opened package and relevant contents area should be visible clearly enough "
            "to assess missing or damaged items."
        ),
    ),
    "REQ_REVIEW_TRUST": RequirementSpec(
        requirement_id="REQ_REVIEW_TRUST",
        claim_object="all",
        applies_to="reviewability",
        minimum_image_evidence=(
            "The submitted images should provide visual evidence that is usable, relevant "
            "to the claim, and grounded in the claimed object."
        ),
    ),
}


def load_requirements_catalog(csv_path: Path | str) -> dict[str, RequirementSpec]:
    """Load requirement specs from evidence_requirements.csv for validation/sync."""
    path = Path(csv_path)
    catalog: dict[str, RequirementSpec] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            spec = RequirementSpec(
                requirement_id=row["requirement_id"],
                claim_object=row["claim_object"],
                applies_to=row["applies_to"],
                minimum_image_evidence=row["minimum_image_evidence"],
            )
            catalog[spec.requirement_id] = spec
    return catalog


def build_active_requirement_ids(
    *,
    claim_object: ClaimObject,
    primary_issue_family: IssueFamily,
    image_count: int,
    identity_constraint_active: bool,
) -> list[str]:
    """Return ordered active requirement IDs per decision_matrix §0.3."""
    active: list[str] = list(UNIVERSAL_REQUIREMENT_IDS)

    family_reqs = FAMILY_REQUIREMENT_IDS.get(primary_issue_family, ())
    for req_id in family_reqs:
        spec = REQUIREMENTS_CATALOG[req_id]
        if spec.claim_object in ("all", claim_object.value) and req_id not in active:
            active.append(req_id)

    if image_count >= 2 and MULTI_IMAGE_REQUIREMENT_ID not in active:
        active.append(MULTI_IMAGE_REQUIREMENT_ID)

    if claim_object is ClaimObject.CAR and identity_constraint_active:
        if CAR_IDENTITY_REQUIREMENT_ID not in active:
            active.append(CAR_IDENTITY_REQUIREMENT_ID)

    return active


def evaluate_requirement_satisfaction(
    requirement_id: str,
    predicates: PredicatesSnapshot,
    images: list[ImageEvidence],
) -> tuple[bool, dict[str, str]]:
    """Evaluate whether a single requirement is satisfied (decision_matrix §1.2)."""
    outputs: dict[str, str] = {"requirement_id": requirement_id}

    if requirement_id == "REQ_GENERAL_OBJECT_PART":
        outputs["predicate"] = "PRED-PART-CLEAR"
        return predicates.part_clear, outputs

    if requirement_id == "REQ_GENERAL_MULTI_IMAGE":
        satisfied = predicates.image_count < 2 or bool(predicates.best_part_image_ids)
        outputs["predicate"] = "PRED-BEST-PART-IMAGE-SET"
        outputs["image_count"] = str(predicates.image_count)
        return satisfied, outputs

    if requirement_id == "REQ_REVIEW_TRUST":
        qualifying = [
            img.image_id
            for img in images
            if img.usable_for_automated_review
            and img.depicts_claim_object.value
            and confidence_at_least(img.depicts_claim_object.confidence, "medium")
        ]
        satisfied = len(qualifying) > 0
        outputs["predicate"] = "depicts_claim_object>=medium"
        outputs["qualifying_image_ids"] = ",".join(qualifying) if qualifying else "none"
        return satisfied, outputs

    if requirement_id == "REQ_CAR_BODY_PANEL":
        outputs["predicate"] = "PRED-PART-CLEAR"
        return predicates.part_clear, outputs

    if requirement_id == "REQ_CAR_GLASS_LIGHT_MIRROR":
        outputs["predicate"] = "PRED-PART-CLEAR"
        return predicates.part_clear, outputs

    if requirement_id == "REQ_CAR_IDENTITY_OR_SIDE":
        satisfied = not predicates.identity_conflict
        outputs["predicate"] = "PRED-IDENTITY-CONFLICT"
        outputs["identity_conflict"] = str(predicates.identity_conflict).lower()
        return satisfied, outputs

    if requirement_id == "REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD":
        outputs["predicate"] = "PRED-PART-CLEAR"
        return predicates.part_clear, outputs

    if requirement_id == "REQ_LAPTOP_BODY_HINGE_PORT":
        outputs["predicate"] = "PRED-PART-CLEAR"
        return predicates.part_clear, outputs

    if requirement_id == "REQ_PACKAGE_EXTERIOR":
        outputs["predicate"] = "PRED-PART-CLEAR"
        return predicates.part_clear, outputs

    if requirement_id == "REQ_PACKAGE_LABEL_OR_STAIN":
        outputs["predicate"] = "PRED-PART-CLEAR"
        return predicates.part_clear, outputs

    if requirement_id == "REQ_PACKAGE_CONTENTS":
        outputs["predicate"] = "PRED-CONTENTS-AREA-CLEAR"
        return predicates.contents_area_clear, outputs

    outputs["error"] = "unknown_requirement"
    return False, outputs


def evaluate_all_requirements(
    requirement_ids: list[str],
    predicates: PredicatesSnapshot,
    images: list[ImageEvidence],
) -> dict[str, bool]:
    """Return satisfaction map for all active requirements."""
    return {
        req_id: evaluate_requirement_satisfaction(req_id, predicates, images)[0]
        for req_id in requirement_ids
    }
