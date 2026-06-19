"""ValidationContext, TrustAssessmentContext, ConsistencyContext."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from contracts.enums import RiskFlag
from contracts.primitives import ConfidenceLevel, RuleId


class ValidationPredicates(BaseModel):
    part_clear: bool
    no_part_visible: bool
    part_visible_low_only: bool
    identity_conflict: bool
    contents_claim: bool
    contents_area_clear: bool
    any_file_unreadable: bool
    best_part_confidence: ConfidenceLevel
    best_part_image_ids: list[str]

    model_config = {"frozen": True}


class ValidationContext(BaseModel):
    row_id: str = Field(min_length=1)
    evidence_standard_met: bool
    triggered_rule_id: RuleId
    reason_template_key: str = Field(min_length=1)
    reason_template_vars: dict[str, str]
    active_requirement_ids: list[str]
    requirements_satisfied: dict[str, bool]
    predicates: ValidationPredicates
    evaluated_at: datetime
    identity_match_detail: str | None = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_esm_rule(self) -> ValidationContext:
        false_rules = {f"ESM-R0{i}" for i in range(1, 8)}
        if self.triggered_rule_id in false_rules and self.evidence_standard_met:
            raise ValueError(f"{self.triggered_rule_id} requires evidence_standard_met=false")
        if self.triggered_rule_id == "ESM-R08" and not self.evidence_standard_met:
            raise ValueError("ESM-R08 requires evidence_standard_met=true")
        for req_id in self.active_requirement_ids:
            if req_id not in self.requirements_satisfied:
                raise ValueError(f"missing requirements_satisfied entry for {req_id}")
        if self.predicates.identity_conflict and self.triggered_rule_id not in {"ESM-R02", *false_rules}:
            pass  # higher-priority rules may preempt
        return self


class TrustAssessmentContext(BaseModel):
    row_id: str = Field(min_length=1)
    valid_image: bool
    triggered_rule_id: RuleId
    all_images_unusable: bool
    any_non_original_high: bool
    contents_unreviewable: bool
    trust_failure_image_ids: list[str]
    evaluated_at: datetime
    trust_failure_reason: str | None = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_trust(self) -> TrustAssessmentContext:
        if self.any_non_original_high:
            if self.valid_image:
                raise ValueError("any_non_original_high implies valid_image=false")
            if self.triggered_rule_id != "VI-R02":
                raise ValueError("any_non_original_high requires triggered_rule_id=VI-R02")
        return self


class ImagePairConflict(BaseModel):
    image_id_a: str = Field(min_length=1)
    image_id_b: str = Field(min_length=1)
    conflicting_features: list[str] = Field(min_length=1)
    confidence: ConfidenceLevel

    model_config = {"frozen": True}


class ConsistencyContext(BaseModel):
    row_id: str = Field(min_length=1)
    image_count: int = Field(ge=1)
    identity_conflict: bool
    identity_conflict_image_pairs: list[ImagePairConflict]
    wrong_object_set: bool
    consistent_vehicle_features: bool
    best_part_image_ids: list[str]
    evaluated_at: datetime
    consistency_notes: str | None = None
    claim_object: str | None = Field(default=None, exclude=True)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_consistency(self) -> ConsistencyContext:
        if self.identity_conflict and not self.identity_conflict_image_pairs:
            raise ValueError("identity_conflict_image_pairs required when identity_conflict=true")
        if self.identity_conflict and self.claim_object not in (None, "car"):
            raise ValueError("identity_conflict only applies to car claims")
        if self.identity_conflict and self.image_count < 2:
            raise ValueError("identity_conflict requires image_count >= 2")
        return self
