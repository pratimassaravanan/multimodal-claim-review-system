"""Dedicated positive/negative coverage for all REQ_* Rule IDs (§1.2)."""

from __future__ import annotations

import pytest

from contracts.enums import ClaimObject, IssueFamily, ObjectPart
from rules.predicates import compute_all_predicates
from rules.requirements_map import evaluate_requirement_satisfaction
from tests.conftest import make_claim_context, make_image_evidence, make_resolution

ALL_REQ_IDS = (
    "REQ_GENERAL_OBJECT_PART",
    "REQ_GENERAL_MULTI_IMAGE",
    "REQ_REVIEW_TRUST",
    "REQ_CAR_BODY_PANEL",
    "REQ_CAR_GLASS_LIGHT_MIRROR",
    "REQ_CAR_IDENTITY_OR_SIDE",
    "REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD",
    "REQ_LAPTOP_BODY_HINGE_PORT",
    "REQ_PACKAGE_EXTERIOR",
    "REQ_PACKAGE_LABEL_OR_STAIN",
    "REQ_PACKAGE_CONTENTS",
)


def _snapshot(claim_object: ClaimObject, images: list, resolution):
    claim = make_claim_context(claim_object=claim_object, image_ids=[img.image_id for img in images])
    return compute_all_predicates(claim, images, resolution).snapshot


def test_req_general_object_part_positive():
    resolution = make_resolution()
    snap = _snapshot(ClaimObject.CAR, [make_image_evidence(part_visible=True, part_confidence="high")], resolution)
    assert evaluate_requirement_satisfaction("REQ_GENERAL_OBJECT_PART", snap, []).satisfied is True


def test_req_general_object_part_negative():
    resolution = make_resolution()
    snap = _snapshot(ClaimObject.CAR, [make_image_evidence(part_visible=False, part_confidence="low")], resolution)
    assert evaluate_requirement_satisfaction("REQ_GENERAL_OBJECT_PART", snap, []).satisfied is False


def test_req_general_multi_image_positive_single_image():
    resolution = make_resolution()
    snap = _snapshot(ClaimObject.CAR, [make_image_evidence()], resolution)
    assert evaluate_requirement_satisfaction("REQ_GENERAL_MULTI_IMAGE", snap, []).satisfied is True


def test_req_general_multi_image_negative_no_clear_image_in_set():
    resolution = make_resolution()
    images = [
        make_image_evidence(image_id="img_1", part_visible=True, part_confidence="low"),
        make_image_evidence(image_id="img_2", part_visible=True, part_confidence="low"),
    ]
    snap = _snapshot(ClaimObject.CAR, images, resolution)
    assert evaluate_requirement_satisfaction("REQ_GENERAL_MULTI_IMAGE", snap, images).satisfied is False


def test_req_review_trust_positive():
    resolution = make_resolution()
    images = [make_image_evidence(depicts_object=True, depicts_confidence="high", usable=True)]
    snap = _snapshot(ClaimObject.CAR, images, resolution)
    assert evaluate_requirement_satisfaction("REQ_REVIEW_TRUST", snap, images).satisfied is True


def test_req_review_trust_negative():
    resolution = make_resolution()
    images = [make_image_evidence(depicts_object=False, depicts_confidence="high", usable=True)]
    snap = _snapshot(ClaimObject.CAR, images, resolution)
    assert evaluate_requirement_satisfaction("REQ_REVIEW_TRUST", snap, images).satisfied is False


@pytest.mark.parametrize(
    "req_id",
    [
        "REQ_CAR_BODY_PANEL",
        "REQ_CAR_GLASS_LIGHT_MIRROR",
        "REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD",
        "REQ_LAPTOP_BODY_HINGE_PORT",
        "REQ_PACKAGE_EXTERIOR",
        "REQ_PACKAGE_LABEL_OR_STAIN",
    ],
)
def test_req_part_clear_family_positive(req_id: str):
    resolution = make_resolution()
    snap = _snapshot(ClaimObject.CAR, [make_image_evidence(part_visible=True, part_confidence="high")], resolution)
    assert evaluate_requirement_satisfaction(req_id, snap, []).satisfied is True


@pytest.mark.parametrize(
    "req_id",
    [
        "REQ_CAR_BODY_PANEL",
        "REQ_CAR_GLASS_LIGHT_MIRROR",
        "REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD",
        "REQ_LAPTOP_BODY_HINGE_PORT",
        "REQ_PACKAGE_EXTERIOR",
        "REQ_PACKAGE_LABEL_OR_STAIN",
    ],
)
def test_req_part_clear_family_negative(req_id: str):
    resolution = make_resolution()
    snap = _snapshot(ClaimObject.CAR, [make_image_evidence(part_visible=False, part_confidence="low")], resolution)
    assert evaluate_requirement_satisfaction(req_id, snap, []).satisfied is False


def test_req_car_identity_or_side_positive():
    resolution = make_resolution()
    images = [make_image_evidence(vehicle_identity_features=["color:red"])]
    snap = _snapshot(ClaimObject.CAR, images, resolution)
    assert evaluate_requirement_satisfaction("REQ_CAR_IDENTITY_OR_SIDE", snap, images).satisfied is True


def test_req_car_identity_or_side_negative():
    resolution = make_resolution()
    images = [
        make_image_evidence(image_id="img_1", vehicle_identity_features=["color:red"], depicts_confidence="high"),
        make_image_evidence(image_id="img_2", vehicle_identity_features=["color:blue"], depicts_confidence="high"),
    ]
    snap = _snapshot(ClaimObject.CAR, images, resolution)
    assert evaluate_requirement_satisfaction("REQ_CAR_IDENTITY_OR_SIDE", snap, images).satisfied is False


def test_req_package_contents_positive():
    resolution = make_resolution(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CONTENTS_OR_ITEM,
        primary_object_part=ObjectPart.CONTENTS,
    )
    images = [
        make_image_evidence(
            claim_object=ClaimObject.PACKAGE,
            package_opened=True,
            contents_visible=True,
        )
    ]
    snap = _snapshot(ClaimObject.PACKAGE, images, resolution)
    assert evaluate_requirement_satisfaction("REQ_PACKAGE_CONTENTS", snap, images).satisfied is True


def test_req_package_contents_negative():
    resolution = make_resolution(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CONTENTS_OR_ITEM,
        primary_object_part=ObjectPart.CONTENTS,
    )
    images = [make_image_evidence(claim_object=ClaimObject.PACKAGE)]
    snap = _snapshot(ClaimObject.PACKAGE, images, resolution)
    assert evaluate_requirement_satisfaction("REQ_PACKAGE_CONTENTS", snap, images).satisfied is False
