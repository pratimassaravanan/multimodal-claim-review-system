"""Tests for rules.predicates — decision_matrix §0.5."""

from __future__ import annotations

from contracts.enums import ClaimObject, IssueFamily, ObjectPart
from rules.predicates import (
    PREDICATE_IDS,
    compute_all_predicates,
    compute_any_file_unreadable,
    compute_any_non_original_high,
    compute_best_part_confidence,
    compute_best_part_image_set,
    compute_contents_area_clear,
    compute_contents_claim,
    compute_identity_conflict,
    compute_no_part_visible,
    compute_part_clear,
    compute_part_visible_low_only,
    compute_predicate,
    compute_wrong_object_set,
)
from tests.conftest import make_claim_context, make_image_evidence, make_resolution


def test_predicate_ids_complete():
    assert len(PREDICATE_IDS) == 13


def test_part_clear_high_confidence():
    img = make_image_evidence(part_visible=True, part_confidence="high")
    result = compute_part_clear([img])
    assert result.predicate_id == "PRED-PART-CLEAR"
    assert result.value is True
    assert "qualifying_image_ids" in result.outputs


def test_part_clear_low_only_is_false():
    img = make_image_evidence(part_visible=True, part_confidence="low")
    result = compute_part_clear([img])
    assert result.value is False


def test_no_part_visible_all_low():
    images = [
        make_image_evidence(image_id="img_1", part_visible=False, part_confidence="low"),
        make_image_evidence(image_id="img_2", part_visible=True, part_confidence="low"),
    ]
    assert compute_no_part_visible(images).value is True


def test_part_visible_low_only():
    img = make_image_evidence(part_visible=True, part_confidence="low")
    assert compute_part_visible_low_only([img]).value is True


def test_best_part_image_set_requires_medium_plus():
    images = [
        make_image_evidence(image_id="img_1", part_visible=True, part_confidence="high"),
        make_image_evidence(image_id="img_2", part_visible=True, part_confidence="low"),
    ]
    result = compute_best_part_image_set(images)
    assert result.value == ["img_1"]
    assert compute_best_part_confidence(images).value == "high"


def test_identity_conflict_on_car():
    a = make_image_evidence(
        image_id="img_1",
        vehicle_identity_features=["color:red", "side:driver"],
        depicts_confidence="high",
    )
    b = make_image_evidence(
        image_id="img_2",
        vehicle_identity_features=["color:blue", "side:driver"],
        depicts_confidence="high",
    )
    result = compute_identity_conflict(ClaimObject.CAR, [a, b])
    assert result.predicate_id == "PRED-IDENTITY-CONFLICT"
    assert result.value is True
    assert "conflicting_features" in result.outputs


def test_identity_conflict_not_applicable_for_laptop():
    result = compute_identity_conflict(ClaimObject.LAPTOP, [])
    assert result.value is False
    assert result.outputs.get("reason") == "not_applicable"


def test_wrong_object_set():
    img = make_image_evidence(depicts_object=False, depicts_confidence="high")
    assert compute_wrong_object_set([img]).value is True


def test_any_non_original_high():
    img = make_image_evidence(non_original=True, non_original_confidence="high")
    assert compute_any_non_original_high([img]).value is True


def test_contents_claim():
    resolution = make_resolution(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CONTENTS_OR_ITEM,
        primary_object_part=ObjectPart.CONTENTS,
    )
    assert compute_contents_claim(resolution).value is True


def test_contents_area_clear():
    img = make_image_evidence(
        claim_object=ClaimObject.PACKAGE,
        package_opened=True,
        contents_visible=True,
    )
    assert compute_contents_area_clear([img]).value is True


def test_any_file_unreadable_traceable():
    img = make_image_evidence(file_readable=False)
    result = compute_any_file_unreadable([img])
    assert result.value is True
    assert result.outputs["unreadable_image_ids"] == "img_1"


def test_compute_predicate_by_id():
    img = make_image_evidence()
    result = compute_predicate("PRED-PART-CLEAR", images=[img])
    assert result.predicate_id == "PRED-PART-CLEAR"


def test_compute_all_predicates_snapshot():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    images = [
        make_image_evidence(image_id="img_1"),
        make_image_evidence(image_id="img_2", part_confidence="medium"),
    ]
    resolution = make_resolution()
    snapshot, results = compute_all_predicates(claim, images, resolution)
    assert snapshot.image_count == 2
    assert snapshot.part_clear is True
    assert len(results) == 13
    assert {r.predicate_id for r in results} == set(PREDICATE_IDS)
