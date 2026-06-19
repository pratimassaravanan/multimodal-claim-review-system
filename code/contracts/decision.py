"""DecisionContext and decision engine output contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from contracts.enums import (
    ClaimObject,
    ClaimStatus,
    ContradictionSubtype,
    DamageExtent,
    IssueType,
    ObjectPart,
    Severity,
)
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.reconciliation import ConsistencyContext, TrustAssessmentContext, ValidationContext
from contracts.resolution import ClaimResolutionContext
from contracts.primitives import RuleId
from ontology.object_parts import is_valid_part


class DecisionContext(BaseModel):
    row_id: str = Field(min_length=1)
    claim: ClaimContext
    claim_observation: ClaimObservation
    resolution: ClaimResolutionContext
    images: list[ImageEvidence] = Field(min_length=1)
    consistency: ConsistencyContext
    validation: ValidationContext
    trust: TrustAssessmentContext
    evidence_standard_met: bool
    valid_image: bool
    aggregated_at: datetime

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_decision_context(self) -> DecisionContext:
        row_ids = {
            self.row_id,
            self.claim.row_id,
            self.claim_observation.row_id,
            self.resolution.row_id,
            self.consistency.row_id,
            self.validation.row_id,
            self.trust.row_id,
        }
        if len(row_ids) != 1:
            raise ValueError("all nested row_id values must match")
        if self.evidence_standard_met != self.validation.evidence_standard_met:
            raise ValueError("evidence_standard_met must match validation context")
        if self.valid_image != self.trust.valid_image:
            raise ValueError("valid_image must match trust context")
        return self


class VerdictDecision(BaseModel):
    row_id: str = Field(min_length=1)
    claim_status: ClaimStatus
    claim_status_rule_id: RuleId
    issue_type: IssueType
    object_part: ObjectPart
    decided_at: datetime
    contradiction_subtype: ContradictionSubtype | None = None
    claim_object: ClaimObject | None = Field(default=None, exclude=True)
    evidence_standard_met: bool | None = Field(default=None, exclude=True)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_verdict(self) -> VerdictDecision:
        if self.evidence_standard_met is False and self.claim_status is not ClaimStatus.NOT_ENOUGH_INFORMATION:
            raise ValueError("HR-01: evidence_standard_met=false requires not_enough_information")
        if self.claim_status is ClaimStatus.CONTRADICTED and self.evidence_standard_met is False:
            raise ValueError("HR-02: contradicted requires evidence_standard_met=true")
        if self.claim_object is not None and not is_valid_part(self.object_part, self.claim_object):
            raise ValueError("object_part invalid for claim_object")
        return self


class SeverityDecision(BaseModel):
    row_id: str = Field(min_length=1)
    severity: Severity
    severity_rule_id: RuleId
    visible_damage_extent_source: DamageExtent
    source_image_id: str | None = None
    verdict_ref: str = Field(min_length=1)
    decided_at: datetime
    claim_status: ClaimStatus | None = Field(default=None, exclude=True)
    issue_type: IssueType | None = Field(default=None, exclude=True)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_severity(self) -> SeverityDecision:
        if self.claim_status is ClaimStatus.NOT_ENOUGH_INFORMATION and self.severity is not Severity.UNKNOWN:
            raise ValueError("HR-03: NEI requires severity=unknown")
        if self.issue_type is IssueType.NONE and self.severity is not Severity.NONE:
            raise ValueError("SV-02: issue_type=none requires severity=none")
        return self


class SupportingImageDecision(BaseModel):
    row_id: str = Field(min_length=1)
    supporting_image_ids: list[str]
    supporting_image_rule_id: RuleId
    excluded_image_ids: list[str]
    selection_rationale: str = Field(min_length=1)
    verdict_ref: str = Field(min_length=1)
    decided_at: datetime
    allowed_image_ids: list[str] | None = Field(default=None, exclude=True)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_supporting(self) -> SupportingImageDecision:
        if self.allowed_image_ids is not None:
            invalid = set(self.supporting_image_ids) - set(self.allowed_image_ids)
            if invalid:
                raise ValueError(f"supporting_image_ids not subset of claim image_ids: {invalid}")
        return self


class ClaimDecision(BaseModel):
    row_id: str = Field(min_length=1)
    verdict: VerdictDecision
    severity_decision: SeverityDecision
    supporting_decision: SupportingImageDecision
    evidence_standard_met: bool
    evidence_standard_met_reason: str = Field(min_length=1)
    valid_image: bool
    claim_status_justification: str = Field(min_length=1)
    composed_at: datetime

    model_config = {"frozen": True}

    @property
    def claim_status(self) -> ClaimStatus:
        return self.verdict.claim_status

    @property
    def issue_type(self) -> IssueType:
        return self.verdict.issue_type

    @property
    def object_part(self) -> ObjectPart:
        return self.verdict.object_part

    @property
    def severity(self) -> Severity:
        return self.severity_decision.severity

    @property
    def supporting_image_ids_csv(self) -> str:
        if not self.supporting_decision.supporting_image_ids:
            return "none"
        return ";".join(self.supporting_decision.supporting_image_ids)

    @model_validator(mode="after")
    def validate_compose(self) -> ClaimDecision:
        if self.row_id != self.verdict.row_id:
            raise ValueError("row_id mismatch across composed decision")
        if self.verdict.claim_status is ClaimStatus.NOT_ENOUGH_INFORMATION:
            if self.severity_decision.severity is not Severity.UNKNOWN:
                raise ValueError("HR-03 violated at compose time")
        if self.verdict.issue_type is IssueType.NONE and self.severity_decision.severity is not Severity.NONE:
            raise ValueError("SV-02 violated at compose time")
        return self
