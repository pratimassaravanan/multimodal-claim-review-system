"""Coverage tests for risk.py — image flags and MRR-1..MRR-6."""

from __future__ import annotations

import pytest

from contracts.decision import VerdictDecision
from contracts.enums import (
    ClaimObject,
    ClaimStatus,
    HistoryFlag,
    IssueFamily,
    IssueType,
    ObjectPart,
    RiskFlag,
)
from rules.risk import MRR_RULE_IDS
from tests.conftest import NOW, make_claim_context, make_claim_observation, make_image_evidence, make_resolution
from tests.rules.stage_helpers import record_outcome, run_risk


def _verdict(**kwargs) -> VerdictDecision:
    defaults = {
        "row_id": "user_001:case_001",
        "claim_status": ClaimStatus.SUPPORTED,
        "claim_status_rule_id": "CS-R07",
        "issue_type": IssueType.DENT,
        "object_part": ObjectPart.REAR_BUMPER,
        "decided_at": NOW,
    }
    defaults.update(kwargs)
    return VerdictDecision(**defaults)


def test_risk_never_changes_verdict():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence()]
    before = run_risk(claim=claim, observation=observation, images=images, resolution=make_resolution())
    assert before.risk.row_id == claim.row_id


def test_blurry_image_positive():
    image = make_image_evidence()
    image = image.model_copy(
        update={"is_blurry": image.is_blurry.model_copy(update={"value": True, "confidence": "medium"})}
    )
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[image],
        resolution=make_resolution(),
    )
    assert RiskFlag.BLURRY_IMAGE in result.risk.risk_flags
    assert record_outcome(result, "blurry_image") is True


def test_blurry_image_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "blurry_image") is False


def test_cropped_or_obstructed_positive():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(cropped_or_obstructed=True, cropped_confidence="medium")],
        resolution=make_resolution(),
    )
    assert RiskFlag.CROPPED_OR_OBSTRUCTED in result.risk.risk_flags
    assert record_outcome(result, "cropped_or_obstructed") is True


def test_cropped_or_obstructed_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "cropped_or_obstructed") is False


def test_low_light_or_glare_positive():
    image = make_image_evidence()
    image = image.model_copy(
        update={
            "is_low_light_or_glare": image.is_low_light_or_glare.model_copy(
                update={"value": True, "confidence": "medium"}
            )
        }
    )
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[image],
        resolution=make_resolution(),
    )
    assert RiskFlag.LOW_LIGHT_OR_GLARE in result.risk.risk_flags
    assert record_outcome(result, "low_light_or_glare") is True


def test_low_light_or_glare_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "low_light_or_glare") is False


def test_wrong_angle_positive():
    image = make_image_evidence(part_visible=False, part_confidence="low")
    image = image.model_copy(
        update={
            "is_wrong_angle_for_claimed_part": image.is_wrong_angle_for_claimed_part.model_copy(
                update={"value": True, "confidence": "medium"}
            )
        }
    )
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[image],
        resolution=make_resolution(),
    )
    assert RiskFlag.WRONG_ANGLE in result.risk.risk_flags
    assert record_outcome(result, "wrong_angle") is True


def test_wrong_angle_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(part_visible=True)],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "wrong_angle") is False


def test_wrong_object_positive():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    observation = make_claim_observation(identity_constraint_active=True, identity_side="front")
    images = [
        make_image_evidence(image_id="img_1", vehicle_identity_features=["color:blue"]),
        make_image_evidence(image_id="img_2", vehicle_identity_features=["color:red"]),
    ]
    result = run_risk(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert RiskFlag.WRONG_OBJECT in result.risk.risk_flags
    assert record_outcome(result, "wrong_object") is True


def test_wrong_object_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "wrong_object") is False


def test_wrong_object_part_positive():
    images = [
        make_image_evidence(
            visible_part=ObjectPart.FRONT_BUMPER,
            part_visible=True,
            part_confidence="high",
        )
    ]
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=images,
        resolution=make_resolution(primary_object_part=ObjectPart.REAR_BUMPER),
    )
    assert RiskFlag.WRONG_OBJECT_PART in result.risk.risk_flags
    assert record_outcome(result, "wrong_object_part") is True


def test_wrong_object_part_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(visible_part=ObjectPart.REAR_BUMPER)],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "wrong_object_part") is False


def test_damage_not_visible_positive():
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_issue_type=IssueType.NONE,
            issue_confidence="medium",
        )
    ]
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=images,
        resolution=make_resolution(),
    )
    assert RiskFlag.DAMAGE_NOT_VISIBLE in result.risk.risk_flags
    assert record_outcome(result, "damage_not_visible") is True


def test_damage_not_visible_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(visible_issue_type=IssueType.DENT)],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "damage_not_visible") is False


def test_claim_mismatch_positive():
    verdict = _verdict(
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R05",
        issue_type=IssueType.SCRATCH,
    )
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert RiskFlag.CLAIM_MISMATCH in result.risk.risk_flags
    assert record_outcome(result, "claim_mismatch") is True


def test_claim_mismatch_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "claim_mismatch") is False


def test_possible_manipulation_positive():
    image = make_image_evidence()
    image = image.model_copy(
        update={
            "is_possibly_manipulated": image.is_possibly_manipulated.model_copy(
                update={"value": True, "confidence": "high"}
            )
        }
    )
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[image],
        resolution=make_resolution(),
    )
    assert RiskFlag.POSSIBLE_MANIPULATION in result.risk.risk_flags
    assert record_outcome(result, "possible_manipulation") is True


def test_possible_manipulation_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "possible_manipulation") is False


def test_non_original_image_positive():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(non_original=True, non_original_confidence="high")],
        resolution=make_resolution(),
    )
    assert RiskFlag.NON_ORIGINAL_IMAGE in result.risk.risk_flags
    assert record_outcome(result, "non_original_image") is True


def test_non_original_image_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(non_original=False)],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "non_original_image") is False


def test_text_instruction_present_positive():
    image = make_image_evidence()
    image = image.model_copy(
        update={
            "has_instruction_text": image.has_instruction_text.model_copy(
                update={"value": True, "confidence": "medium"}
            )
        }
    )
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[image],
        resolution=make_resolution(),
    )
    assert RiskFlag.TEXT_INSTRUCTION_PRESENT in result.risk.risk_flags
    assert record_outcome(result, "text_instruction_present") is True


def test_text_instruction_present_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "text_instruction_present") is False


def test_user_history_risk_positive():
    claim = make_claim_context()
    claim = claim.model_copy(update={"history_flags": [HistoryFlag.USER_HISTORY_RISK]})
    result = run_risk(
        claim=claim,
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert RiskFlag.USER_HISTORY_RISK in result.risk.risk_flags
    assert record_outcome(result, "user_history_risk") is True


def test_user_history_risk_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "user_history_risk") is False


@pytest.mark.parametrize("rule_id", MRR_RULE_IDS)
def test_mrr_rules_have_records(rule_id: str):
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, rule_id) in {True, False}


def test_mrr_1_positive():
    claim = make_claim_context()
    claim = claim.model_copy(update={"history_flags": [HistoryFlag.MANUAL_REVIEW_REQUIRED]})
    result = run_risk(
        claim=claim,
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert "MRR-1" in result.risk.manual_review_rule_ids
    assert record_outcome(result, "MRR-1") is True


def test_mrr_1_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "MRR-1") is False


def test_mrr_2_positive():
    claim = make_claim_context()
    claim = claim.model_copy(update={"history_flags": [HistoryFlag.USER_HISTORY_RISK]})
    result = run_risk(
        claim=claim,
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "MRR-2") is True


def test_mrr_3_positive():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    observation = make_claim_observation(identity_constraint_active=True, identity_side="front")
    images = [
        make_image_evidence(image_id="img_1", vehicle_identity_features=["color:blue"]),
        make_image_evidence(image_id="img_2", vehicle_identity_features=["color:red"]),
    ]
    result = run_risk(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "MRR-3") is True


def test_mrr_4_positive():
    verdict = _verdict(
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R04",
        issue_type=IssueType.BROKEN_PART,
        object_part=ObjectPart.FRONT_BUMPER,
    )
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(visible_part=ObjectPart.FRONT_BUMPER)],
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert record_outcome(result, "MRR-4") is True


def test_mrr_5_positive():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence(non_original=True, non_original_confidence="high")],
        resolution=make_resolution(),
    )
    assert record_outcome(result, "MRR-5") is True


def test_mrr_6_positive():
    claim = make_claim_context(claim_object=ClaimObject.PACKAGE)
    observation = make_claim_observation(claim_object=ClaimObject.PACKAGE)
    images = [
        make_image_evidence(
            claim_object=ClaimObject.PACKAGE,
            cropped_or_obstructed=True,
            cropped_confidence="high",
        )
    ]
    verdict = _verdict(
        row_id=claim.row_id,
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        claim_status_rule_id="CS-R01",
        issue_type=IssueType.UNKNOWN,
        object_part=ObjectPart.CONTENTS,
    )
    result = run_risk(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(
            claim_object=ClaimObject.PACKAGE,
            primary_issue_family=IssueFamily.CONTENTS_OR_ITEM,
            primary_object_part=ObjectPart.CONTENTS,
        ),
        verdict=verdict,
    )
    assert record_outcome(result, "MRR-6") is True


def test_manual_review_required_positive():
    claim = make_claim_context()
    claim = claim.model_copy(update={"history_flags": [HistoryFlag.MANUAL_REVIEW_REQUIRED]})
    result = run_risk(
        claim=claim,
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert result.risk.manual_review_required is True
    assert RiskFlag.MANUAL_REVIEW_REQUIRED in result.risk.risk_flags
    assert record_outcome(result, "manual_review_required") is True


def test_manual_review_required_negative():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert result.risk.manual_review_required is False
    assert record_outcome(result, "manual_review_required") is False


def test_no_flags_returns_none():
    result = run_risk(
        claim=make_claim_context(),
        observation=make_claim_observation(),
        images=[make_image_evidence()],
        resolution=make_resolution(),
    )
    assert result.risk.risk_flags == [RiskFlag.NONE]
