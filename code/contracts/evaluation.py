"""EvaluationRecord and related evaluation contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from contracts.enums import ClaimStatus, IssueType, ObjectPart, Severity


class OutputRowSnapshot(BaseModel):
    evidence_standard_met: bool
    evidence_standard_met_reason: str = Field(min_length=1)
    risk_flags: str = Field(min_length=1)
    issue_type: IssueType
    object_part: ObjectPart
    claim_status: ClaimStatus
    claim_status_justification: str = Field(min_length=1)
    supporting_image_ids: str = Field(min_length=1)
    valid_image: bool
    severity: Severity

    model_config = {"frozen": True}


class EngineScoreBundle(BaseModel):
    verdict_score: float = Field(ge=0.0, le=1.0)
    severity_score: float = Field(ge=0.0, le=1.0)
    supporting_score: float = Field(ge=0.0, le=1.0)
    extraction_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reconciliation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    weighted_total: float = Field(ge=0.0, le=1.0)

    model_config = {"frozen": True}


class EvaluationRecord(BaseModel):
    record_id: str = Field(min_length=1)
    row_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    predicted: OutputRowSnapshot
    expected: OutputRowSnapshot | None = None
    field_matches: dict[str, bool] | None = None
    claim_status_match: bool | None = None
    evidence_standard_met_match: bool | None = None
    risk_flags_f1: float | None = Field(default=None, ge=0.0, le=1.0)
    weighted_score: float | None = Field(default=None, ge=0.0, le=1.0)
    trace_hash: str = Field(min_length=1)
    evaluated_at: datetime
    verdict_match: bool | None = None
    severity_match: bool | None = None
    supporting_ids_match: bool | None = None
    claim_observation_part_match: bool | None = None
    engine_scores: EngineScoreBundle | None = None
    failure_categories: list[str] | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    model_calls: int | None = Field(default=None, ge=0)
    token_input: int | None = Field(default=None, ge=0)
    token_output: int | None = Field(default=None, ge=0)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_evaluation(self) -> EvaluationRecord:
        if self.expected is None and self.weighted_score is not None:
            raise ValueError("weighted_score requires expected labels")
        if self.expected is not None and self.weighted_score is None:
            pass  # harness may compute later
        return self
