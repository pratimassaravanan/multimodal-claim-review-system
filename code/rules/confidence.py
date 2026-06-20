"""Shared confidence ranking helpers."""

from __future__ import annotations

from contracts.primitives import ConfidenceLevel

CONFIDENCE_RANK: dict[ConfidenceLevel, int] = {"low": 1, "medium": 2, "high": 3}


def confidence_at_least(level: ConfidenceLevel, minimum: ConfidenceLevel) -> bool:
    return CONFIDENCE_RANK[level] >= CONFIDENCE_RANK[minimum]
