"""Pipeline stage identifiers aligned with DecisionTrace RuleHitStage."""

from __future__ import annotations

from enum import StrEnum


class PipelineStage(StrEnum):
    INTAKE = "intake"
    OBSERVE_CLAIM = "observe_claim"
    RESOLVE = "resolve"
    OBSERVE_IMAGE = "observe_image"
    AGGREGATE = "aggregate"
    CONSISTENCY = "consistency"
    VALIDATION = "validation"
    TRUST = "trust"
    VERDICT = "verdict"
    SEVERITY = "severity"
    SUPPORTING = "supporting"
    RISK = "risk"
    COMPOSE = "compose"
    EMIT = "emit"


EXECUTION_ORDER: tuple[PipelineStage, ...] = (
    PipelineStage.INTAKE,
    PipelineStage.OBSERVE_CLAIM,
    PipelineStage.RESOLVE,
    PipelineStage.OBSERVE_IMAGE,
    PipelineStage.AGGREGATE,
    PipelineStage.CONSISTENCY,
    PipelineStage.VALIDATION,
    PipelineStage.TRUST,
    PipelineStage.VERDICT,
    PipelineStage.SEVERITY,
    PipelineStage.SUPPORTING,
    PipelineStage.RISK,
    PipelineStage.COMPOSE,
    PipelineStage.EMIT,
)
