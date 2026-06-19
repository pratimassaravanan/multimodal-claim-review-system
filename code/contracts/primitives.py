"""Shared primitive types and ScoredField wrapper."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

NonEmptyString = str
RuleId = str
RequirementId = str
SemicolonList = str

ConfidenceLevel = Literal["high", "medium", "low"]
SourceModule = Literal["claim_observer", "image_observer", "rule_engine"]


class ScoredField(BaseModel, Generic[T]):
    """Observation value with confidence metadata for rule gating."""

    value: T
    confidence: ConfidenceLevel
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    source_module: SourceModule
    source_image_id: str | None = None

    model_config = {"frozen": True}
