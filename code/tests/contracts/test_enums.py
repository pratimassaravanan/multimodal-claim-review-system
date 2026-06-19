"""Enum validation tests."""

import pytest
from pydantic import ValidationError

from contracts.enums import (
    ClaimObject,
    ClaimStatus,
    IssueType,
    ObjectPart,
    RiskFlag,
    RuleHitStage,
)


@pytest.mark.parametrize(
    "enum_cls, value",
    [
        (ClaimObject, "car"),
        (ClaimStatus, "supported"),
        (IssueType, "dent"),
        (ObjectPart, "rear_bumper"),
        (RiskFlag, "blurry_image"),
        (RuleHitStage, "verdict"),
    ],
)
def test_enum_accepts_valid_values(enum_cls, value):
    assert enum_cls(value) == value


@pytest.mark.parametrize(
    "enum_cls, bad_value",
    [
        (ClaimObject, "truck"),
        (ClaimStatus, "approved"),
        (IssueType, "rust"),
        (ObjectPart, "engine"),
        (RiskFlag, "fake_flag"),
        (RuleHitStage, "decide"),
    ],
)
def test_enum_rejects_invalid_values(enum_cls, bad_value):
    with pytest.raises(ValueError):
        enum_cls(bad_value)


def test_object_part_str_enum_membership():
    assert ObjectPart.REAR_BUMPER.value == "rear_bumper"
    assert "screen" in {part.value for part in ObjectPart}


def test_rule_hit_stage_v2_includes_split_decision_stages():
    assert RuleHitStage.VERDICT.value == "verdict"
    assert RuleHitStage.SEVERITY.value == "severity"
    assert RuleHitStage.SUPPORTING.value == "supporting"
    with pytest.raises(ValueError):
        RuleHitStage("decide")
