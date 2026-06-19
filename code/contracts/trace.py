"""DecisionTrace contract."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from contracts.decision import ClaimDecision, SeverityDecision, SupportingImageDecision, VerdictDecision
from contracts.enums import CONTRACTS_VERSION, RuleHitStage
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation
from contracts.reconciliation import ConsistencyContext, TrustAssessmentContext, ValidationContext
from contracts.resolution import ClaimResolutionContext, EvidenceContext
from contracts.risk import RiskContext
from contracts.primitives import RuleId


class RuleHit(BaseModel):
    sequence: int = Field(ge=1)
    stage: RuleHitStage
    rule_id: RuleId
    matched: bool
    inputs_snapshot: dict[str, str]
    outputs_snapshot: dict[str, str]

    model_config = {"frozen": True}


class DecisionTrace(BaseModel):
    row_id: str = Field(min_length=1)
    pipeline_version: str = Field(min_length=1)
    contracts_version: str = CONTRACTS_VERSION
    claim: ClaimContext
    evidence: EvidenceContext
    claim_observation: ClaimObservation
    resolution: ClaimResolutionContext
    consistency: ConsistencyContext
    validation: ValidationContext
    trust: TrustAssessmentContext
    verdict: VerdictDecision
    severity_decision: SeverityDecision
    supporting_decision: SupportingImageDecision
    decision: ClaimDecision
    risk: RiskContext
    rule_hits_ordered: list[RuleHit] = Field(min_length=1)
    started_at: datetime
    completed_at: datetime
    deterministic_hash: str = Field(min_length=1)
    model_call_counts: dict[str, int] | None = None
    token_usage: dict[str, int] | None = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_trace(self) -> DecisionTrace:
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must be >= started_at")
        if self.claim_observation.row_id != self.claim.row_id:
            raise ValueError("claim_observation row_id must match claim")
        stages = {hit.stage for hit in self.rule_hits_ordered}
        for required in (RuleHitStage.VERDICT, RuleHitStage.SEVERITY, RuleHitStage.SUPPORTING):
            if required not in stages:
                raise ValueError(f"missing required RuleHit stage: {required}")
        return self
