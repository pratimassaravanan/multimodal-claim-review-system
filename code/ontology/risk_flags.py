"""Risk flag constants and list handling."""

from __future__ import annotations

from contracts.enums import RiskFlag

# Flags that may appear in output (excluding NONE when combined with others).
OUTPUT_RISK_FLAGS: frozenset[RiskFlag] = frozenset(RiskFlag)

ACTIVE_RISK_FLAGS: frozenset[RiskFlag] = frozenset(flag for flag in RiskFlag if flag is not RiskFlag.NONE)


def is_valid_risk_flag(value: RiskFlag) -> bool:
    return value in OUTPUT_RISK_FLAGS


def risk_flags_are_valid(flags: list[RiskFlag]) -> bool:
    if not flags:
        return False
    if RiskFlag.NONE in flags and len(flags) > 1:
        return False
    return all(is_valid_risk_flag(flag) for flag in flags)
