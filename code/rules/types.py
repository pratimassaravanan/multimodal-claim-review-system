"""Typed rule-layer outputs — no raw dict/tuple public returns."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.decision import ClaimDecision, SeverityDecision, SupportingImageDecision, VerdictDecision
from contracts.primitives import ConfidenceLevel, RuleId
from contracts.risk import RiskContext
from contracts.reconciliation import ConsistencyContext, TrustAssessmentContext, ValidationContext
from contracts.resolution import ClaimResolutionContext


class PredicatesSnapshot(BaseModel):
    """Aggregate of all §0.5 predicates for downstream rule matrices."""

    image_count: int = Field(ge=0)
    any_file_unreadable: bool
    best_part_confidence: ConfidenceLevel
    best_part_image_ids: list[str]
    part_clear: bool
    part_visible_low_only: bool
    no_part_visible: bool
    identity_conflict: bool
    wrong_object_set: bool
    any_non_original_high: bool
    contents_claim: bool
    contents_area_clear: bool
    all_images_unusable: bool

    model_config = {"frozen": True}


class TraceField(BaseModel):
    key: str = Field(min_length=1)
    value: str

    model_config = {"frozen": True}


class RuleExecutionRecord(BaseModel):
    """Traceable outcome for one matrix rule evaluation."""

    rule_id: RuleId
    outcome: bool
    justification: str = Field(min_length=1)
    trace_fields: list[TraceField] = Field(default_factory=list)

    model_config = {"frozen": True}


class PredicateTraceRecord(BaseModel):
    predicate_id: RuleId
    outcome: bool
    value_text: str
    justification: str = Field(min_length=1)
    trace_fields: list[TraceField] = Field(default_factory=list)

    model_config = {"frozen": True}


class PredicatesEvaluationBundle(BaseModel):
    snapshot: PredicatesSnapshot
    records: list[PredicateTraceRecord] = Field(min_length=1)

    model_config = {"frozen": True}


class RequirementEvaluationResult(BaseModel):
    requirement_id: RuleId
    satisfied: bool
    predicate_ref: str = Field(min_length=1)
    justification: str = Field(min_length=1)
    trace_fields: list[TraceField] = Field(default_factory=list)

    model_config = {"frozen": True}


class RequirementEvaluationBundle(BaseModel):
    results: list[RequirementEvaluationResult]

    model_config = {"frozen": True}


class ResolveClaimStageResult(BaseModel):
    resolution: ClaimResolutionContext
    rule_records: list[RuleExecutionRecord] = Field(min_length=1)

    model_config = {"frozen": True}


class ConsistencyStageResult(BaseModel):
    consistency: ConsistencyContext
    rule_records: list[RuleExecutionRecord] = Field(default_factory=list)

    model_config = {"frozen": True}


class SufficiencyStageResult(BaseModel):
    validation: ValidationContext
    rule_records: list[RuleExecutionRecord] = Field(min_length=1)

    model_config = {"frozen": True}


class TrustStageResult(BaseModel):
    trust: TrustAssessmentContext
    rule_records: list[RuleExecutionRecord] = Field(min_length=1)

    model_config = {"frozen": True}


class VerdictStageResult(BaseModel):
    verdict: VerdictDecision
    rule_records: list[RuleExecutionRecord] = Field(min_length=1)

    model_config = {"frozen": True}


class SeverityStageResult(BaseModel):
    severity: SeverityDecision
    rule_records: list[RuleExecutionRecord] = Field(min_length=1)

    model_config = {"frozen": True}


class SupportingImageStageResult(BaseModel):
    supporting: SupportingImageDecision
    rule_records: list[RuleExecutionRecord] = Field(min_length=1)

    model_config = {"frozen": True}


class RiskStageResult(BaseModel):
    risk: RiskContext
    rule_records: list[RuleExecutionRecord] = Field(min_length=1)

    model_config = {"frozen": True}


class ComposeStageResult(BaseModel):
    decision: ClaimDecision
    rule_records: list[RuleExecutionRecord] = Field(min_length=1)

    model_config = {"frozen": True}
