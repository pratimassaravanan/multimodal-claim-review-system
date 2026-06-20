"""Tests for rules.resolve_claim — MP-1..MP-5."""

from __future__ import annotations

from contracts.enums import ClaimObject, ObjectPart, ResolutionMethod
from rules.resolve_claim import resolve_claim
from tests.conftest import NOW, make_claim_context, make_claim_observation, make_image_evidence


def test_mp2_single_part_positive():
    claim = make_claim_context()
    observation = make_claim_observation(alleged_parts=[ObjectPart.REAR_BUMPER])
    result = resolve_claim(claim, observation, [make_image_evidence()], evaluated_at=NOW)
    assert result.resolution.primary_object_part is ObjectPart.REAR_BUMPER
    assert result.resolution.resolution_method is ResolutionMethod.SINGLE_PART
    assert any(record.rule_id == "MP-2" and record.outcome for record in result.rule_records)


def test_mp2_multi_part_negative():
    claim = make_claim_context(image_ids=["img_1"])
    observation = make_claim_observation(
        alleged_parts=[ObjectPart.REAR_BUMPER, ObjectPart.FRONT_BUMPER],
    )
    result = resolve_claim(claim, observation, [make_image_evidence()], evaluated_at=NOW)
    mp2 = next(record for record in result.rule_records if record.rule_id == "MP-2")
    assert mp2.outcome is False


def test_mp4_visibility_selection_positive():
    claim = make_claim_context(image_ids=["img_1"])
    observation = make_claim_observation(
        alleged_parts=[ObjectPart.REAR_BUMPER, ObjectPart.FRONT_BUMPER],
    )
    images = [
        make_image_evidence(
            visible_part=ObjectPart.REAR_BUMPER,
            part_visible=True,
            part_confidence="high",
        )
    ]
    result = resolve_claim(claim, observation, images, evaluated_at=NOW)
    assert result.resolution.primary_object_part is ObjectPart.REAR_BUMPER
    assert any(record.rule_id == "MP-4" and record.outcome for record in result.rule_records)


def test_mp5_secondary_parts_positive():
    claim = make_claim_context(image_ids=["img_1"])
    observation = make_claim_observation(
        alleged_parts=[ObjectPart.REAR_BUMPER, ObjectPart.FRONT_BUMPER],
    )
    result = resolve_claim(claim, observation, [make_image_evidence()], evaluated_at=NOW)
    assert ObjectPart.FRONT_BUMPER in result.resolution.secondary_object_parts
    assert any(record.rule_id == "MP-5" and record.outcome for record in result.rule_records)


def test_mp1_positive_always_records():
    result = resolve_claim(
        make_claim_context(),
        make_claim_observation(alleged_parts=[ObjectPart.REAR_BUMPER]),
        [make_image_evidence()],
        evaluated_at=NOW,
    )
    mp1 = next(record for record in result.rule_records if record.rule_id == "MP-1")
    assert mp1.outcome is True


def test_mp1_negative_never_false():
    """MP-1 invariant: non-empty alleged_parts always yield MP-1 outcome=True."""
    result = resolve_claim(
        make_claim_context(),
        make_claim_observation(alleged_parts=[ObjectPart.REAR_BUMPER, ObjectPart.FRONT_BUMPER]),
        [make_image_evidence()],
        evaluated_at=NOW,
    )
    mp1 = next(record for record in result.rule_records if record.rule_id == "MP-1")
    assert mp1.outcome is True


def test_mp3_negative_not_emitted_on_single_part():
    result = resolve_claim(
        make_claim_context(),
        make_claim_observation(alleged_parts=[ObjectPart.REAR_BUMPER]),
        [make_image_evidence()],
        evaluated_at=NOW,
    )
    assert not any(record.rule_id == "MP-3" for record in result.rule_records)


def test_mp4_negative_not_emitted_on_single_part():
    result = resolve_claim(
        make_claim_context(),
        make_claim_observation(alleged_parts=[ObjectPart.REAR_BUMPER]),
        [make_image_evidence()],
        evaluated_at=NOW,
    )
    assert not any(record.rule_id == "MP-4" for record in result.rule_records)


def test_mp5_negative_not_emitted_on_single_part():
    result = resolve_claim(
        make_claim_context(),
        make_claim_observation(alleged_parts=[ObjectPart.REAR_BUMPER]),
        [make_image_evidence()],
        evaluated_at=NOW,
    )
    assert not any(record.rule_id == "MP-5" for record in result.rule_records)
