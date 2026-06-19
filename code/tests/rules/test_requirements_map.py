"""Tests for rules.requirements_map — §0.3 catalog and §1.2 satisfaction."""

from __future__ import annotations

from pathlib import Path

from contracts.enums import ClaimObject, IssueFamily, ObjectPart
from rules.predicates import compute_all_predicates
from rules.requirements_map import (
    REQUIREMENTS_CATALOG,
    build_active_requirement_ids,
    evaluate_requirement_satisfaction,
    load_requirements_catalog,
)
from tests.conftest import make_claim_context, make_image_evidence, make_resolution

REPO_ROOT = Path(__file__).resolve().parents[3]
CSV_PATH = REPO_ROOT / "dataset" / "evidence_requirements.csv"


def test_catalog_matches_csv():
    loaded = load_requirements_catalog(CSV_PATH)
    assert set(loaded) == set(REQUIREMENTS_CATALOG)
    for req_id, spec in REQUIREMENTS_CATALOG.items():
        assert loaded[req_id].minimum_image_evidence == spec.minimum_image_evidence


def test_universal_requirements_always_active():
    active = build_active_requirement_ids(
        claim_object=ClaimObject.CAR,
        primary_issue_family=IssueFamily.DENT_OR_SCRATCH,
        image_count=1,
        identity_constraint_active=False,
    )
    assert "REQ_GENERAL_OBJECT_PART" in active
    assert "REQ_REVIEW_TRUST" in active


def test_multi_image_requirement_when_two_images():
    active = build_active_requirement_ids(
        claim_object=ClaimObject.CAR,
        primary_issue_family=IssueFamily.DENT_OR_SCRATCH,
        image_count=2,
        identity_constraint_active=False,
    )
    assert "REQ_GENERAL_MULTI_IMAGE" in active


def test_car_identity_requirement_when_constraint_active():
    active = build_active_requirement_ids(
        claim_object=ClaimObject.CAR,
        primary_issue_family=IssueFamily.DENT_OR_SCRATCH,
        image_count=1,
        identity_constraint_active=True,
    )
    assert "REQ_CAR_IDENTITY_OR_SIDE" in active


def test_family_requirement_filtered_by_claim_object():
    active = build_active_requirement_ids(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CRUSHED_TORN_SEAL,
        image_count=1,
        identity_constraint_active=False,
    )
    assert "REQ_PACKAGE_EXTERIOR" in active
    assert "REQ_CAR_BODY_PANEL" not in active


def test_req_general_object_part_satisfaction():
    claim = make_claim_context()
    images = [make_image_evidence(part_visible=True, part_confidence="high")]
    resolution = make_resolution()
    snapshot, _ = compute_all_predicates(claim, images, resolution)
    satisfied, outputs = evaluate_requirement_satisfaction("REQ_GENERAL_OBJECT_PART", snapshot, images)
    assert satisfied is True
    assert outputs["predicate"] == "PRED-PART-CLEAR"


def test_req_review_trust_requires_usable_depiction():
    claim = make_claim_context()
    images = [make_image_evidence(depicts_object=True, depicts_confidence="high", usable=True)]
    resolution = make_resolution()
    snapshot, _ = compute_all_predicates(claim, images, resolution)
    satisfied, _ = evaluate_requirement_satisfaction("REQ_REVIEW_TRUST", snapshot, images)
    assert satisfied is True


def test_req_package_contents_uses_contents_predicate():
    claim = make_claim_context(claim_object=ClaimObject.PACKAGE, image_ids=["img_1"])
    images = [
        make_image_evidence(
            claim_object=ClaimObject.PACKAGE,
            package_opened=True,
            contents_visible=True,
        )
    ]
    resolution = make_resolution(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CONTENTS_OR_ITEM,
        primary_object_part=ObjectPart.CONTENTS,
    )
    snapshot, _ = compute_all_predicates(claim, images, resolution)
    satisfied, outputs = evaluate_requirement_satisfaction("REQ_PACKAGE_CONTENTS", snapshot, images)
    assert satisfied is True
    assert outputs["predicate"] == "PRED-CONTENTS-AREA-CLEAR"


def test_req_car_identity_satisfied_without_conflict():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    images = [
        make_image_evidence(image_id="img_1", vehicle_identity_features=["color:red"]),
        make_image_evidence(image_id="img_2", vehicle_identity_features=["color:red"]),
    ]
    resolution = make_resolution()
    snapshot, _ = compute_all_predicates(claim, images, resolution)
    satisfied, outputs = evaluate_requirement_satisfaction("REQ_CAR_IDENTITY_OR_SIDE", snapshot, images)
    assert satisfied is True
    assert outputs["predicate"] == "PRED-IDENTITY-CONFLICT"
