"""Tests for rules.predicates — decision_matrix §0.5."""

from __future__ import annotations

import pytest

from contracts.enums import ClaimObject, IssueFamily, ObjectPart
from rules.predicates import PREDICATE_IDS, compute_all_predicates, compute_predicate
from tests.conftest import make_claim_context, make_image_evidence, make_resolution


@pytest.mark.parametrize("predicate_id", PREDICATE_IDS)
def test_predicate_has_positive_and_negative_cases(predicate_id: str):
    claim = make_claim_context()
    resolution = make_resolution()

    cases: dict[str, tuple[list, list, bool, bool]] = {
        "PRED-IMAGE-COUNT": (
            [make_image_evidence(image_id="img_1")],
            [make_image_evidence(image_id="img_1"), make_image_evidence(image_id="img_2")],
            True,
            True,
        ),
        "PRED-ANY-FILE-UNREADABLE": (
            [make_image_evidence(file_readable=False)],
            [make_image_evidence(file_readable=True)],
            True,
            False,
        ),
        "PRED-BEST-PART-CONFIDENCE": (
            [make_image_evidence(part_confidence="high")],
            [make_image_evidence(part_confidence="low")],
            True,
            True,
        ),
        "PRED-BEST-PART-IMAGE-SET": (
            [make_image_evidence(part_visible=True, part_confidence="high")],
            [make_image_evidence(part_visible=True, part_confidence="low")],
            True,
            False,
        ),
        "PRED-PART-CLEAR": (
            [make_image_evidence(part_visible=True, part_confidence="high")],
            [make_image_evidence(part_visible=False, part_confidence="low")],
            True,
            False,
        ),
        "PRED-PART-VISIBLE-LOW-ONLY": (
            [make_image_evidence(part_visible=True, part_confidence="low")],
            [make_image_evidence(part_visible=True, part_confidence="high")],
            True,
            False,
        ),
        "PRED-NO-PART-VISIBLE": (
            [make_image_evidence(part_visible=False, part_confidence="low")],
            [make_image_evidence(part_visible=True, part_confidence="high")],
            True,
            False,
        ),
        "PRED-IDENTITY-CONFLICT": (
            [
                make_image_evidence(image_id="img_1", vehicle_identity_features=["color:red"], depicts_confidence="high"),
                make_image_evidence(image_id="img_2", vehicle_identity_features=["color:blue"], depicts_confidence="high"),
            ],
            [make_image_evidence()],
            True,
            False,
        ),
        "PRED-WRONG-OBJECT-SET": (
            [make_image_evidence(depicts_object=False, depicts_confidence="high")],
            [make_image_evidence(depicts_object=True, depicts_confidence="high")],
            True,
            False,
        ),
        "PRED-ANY-NON-ORIGINAL-HIGH": (
            [make_image_evidence(non_original=True, non_original_confidence="high")],
            [make_image_evidence(non_original=False, non_original_confidence="low")],
            True,
            False,
        ),
        "PRED-CONTENTS-CLAIM": (
            [],
            [],
            True,
            False,
        ),
        "PRED-CONTENTS-AREA-CLEAR": (
            [
                make_image_evidence(
                    claim_object=ClaimObject.PACKAGE,
                    package_opened=True,
                    contents_visible=True,
                )
            ],
            [make_image_evidence(claim_object=ClaimObject.PACKAGE)],
            True,
            False,
        ),
        "PRED-ALL-IMAGES-UNUSABLE": (
            [make_image_evidence(usable=False)],
            [make_image_evidence(usable=True)],
            True,
            False,
        ),
    }

    pos_images, neg_images, pos_outcome, neg_outcome = cases[predicate_id]

    if predicate_id == "PRED-IDENTITY-CONFLICT":
        pos = compute_predicate(predicate_id, claim=claim, images=pos_images)
        neg = compute_predicate(predicate_id, claim=claim, images=neg_images)
    elif predicate_id == "PRED-CONTENTS-CLAIM":
        pos = compute_predicate(
            predicate_id,
            images=pos_images,
            resolution=make_resolution(
                claim_object=ClaimObject.PACKAGE,
                primary_issue_family=IssueFamily.CONTENTS_OR_ITEM,
                primary_object_part=ObjectPart.CONTENTS,
            ),
        )
        neg = compute_predicate(predicate_id, images=neg_images, resolution=resolution)
    else:
        pos = compute_predicate(predicate_id, claim=claim, images=pos_images, resolution=resolution)
        neg = compute_predicate(predicate_id, claim=claim, images=neg_images, resolution=resolution)

    assert pos.outcome is pos_outcome
    assert neg.outcome is neg_outcome
    assert pos.justification
    assert neg.justification
    if predicate_id == "PRED-IMAGE-COUNT":
        assert pos.value_text != neg.value_text
    if predicate_id == "PRED-BEST-PART-CONFIDENCE":
        assert pos.value_text == "high"
        assert neg.value_text == "low"


def test_compute_all_predicates_bundle():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    images = [
        make_image_evidence(image_id="img_1"),
        make_image_evidence(image_id="img_2", part_confidence="medium"),
    ]
    resolution = make_resolution()
    bundle = compute_all_predicates(claim, images, resolution)
    assert bundle.snapshot.image_count == 2
    assert bundle.snapshot.part_clear is True
    assert len(bundle.records) == 13
