"""Risk flag ontology validation tests."""

import pytest

from contracts.enums import RiskFlag
from ontology.normalize import format_risk_flags, parse_risk_flags
from ontology.risk_flags import ACTIVE_RISK_FLAGS, is_valid_risk_flag, risk_flags_are_valid


def test_active_risk_flags_exclude_none():
    assert RiskFlag.NONE not in ACTIVE_RISK_FLAGS
    assert RiskFlag.BLURRY_IMAGE in ACTIVE_RISK_FLAGS


@pytest.mark.parametrize("flag", list(RiskFlag))
def test_is_valid_risk_flag(flag):
    assert is_valid_risk_flag(flag)


def test_risk_flags_reject_none_with_others():
    assert risk_flags_are_valid([RiskFlag.NONE]) is True
    assert risk_flags_are_valid([RiskFlag.BLURRY_IMAGE, RiskFlag.WRONG_ANGLE]) is True
    assert risk_flags_are_valid([RiskFlag.NONE, RiskFlag.BLURRY_IMAGE]) is False


def test_parse_and_format_risk_flags_roundtrip():
    assert parse_risk_flags("none") == [RiskFlag.NONE]
    flags = parse_risk_flags("blurry_image;wrong_angle")
    assert flags == [RiskFlag.BLURRY_IMAGE, RiskFlag.WRONG_ANGLE]
    assert format_risk_flags(flags) == "blurry_image;wrong_angle"


def test_format_risk_flags_none_sentinel():
    assert format_risk_flags([RiskFlag.NONE]) == "none"
    assert format_risk_flags([]) == "none"
