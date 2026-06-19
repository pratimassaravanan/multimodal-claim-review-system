"""ClaimResolutionContext and EvidenceContext."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from contracts.enums import ClaimObject, IssueFamily, ObjectPart, ResolutionMethod
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from ontology.issue_families import is_family_compatible_with_part
from ontology.object_parts import is_valid_part


class ClaimResolutionContext(BaseModel):
    row_id: str = Field(min_length=1)
    claim_observation_ref: str = Field(min_length=1)
    multi_part_claim: bool
    primary_object_part: ObjectPart
    primary_issue_family: IssueFamily
    secondary_object_parts: list[ObjectPart]
    resolution_method: ResolutionMethod
    resolution_rule_ids: list[str] = Field(min_length=1)
    part_visibility_scores: dict[ObjectPart, int]
    resolved_at: datetime
    claim_object: ClaimObject | None = Field(default=None, exclude=True)
    alleged_parts: list[ObjectPart] | None = Field(default=None, exclude=True)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_resolution(self) -> ClaimResolutionContext:
        if self.claim_object is not None:
            if not is_valid_part(self.primary_object_part, self.claim_object):
                raise ValueError("primary_object_part invalid for claim_object")
            for part in self.secondary_object_parts:
                if not is_valid_part(part, self.claim_object):
                    raise ValueError(f"secondary part {part} invalid for claim_object")
            if not is_family_compatible_with_part(
                self.primary_issue_family, self.claim_object, self.primary_object_part
            ):
                raise ValueError("primary_issue_family incompatible with primary_object_part")
        if self.multi_part_claim and self.alleged_parts is not None:
            if self.primary_object_part not in self.alleged_parts:
                raise ValueError("primary_object_part must be in alleged_parts when multi_part_claim")
            expected_secondary = [p for p in self.alleged_parts if p != self.primary_object_part]
            if sorted(self.secondary_object_parts) != sorted(expected_secondary):
                raise ValueError("secondary_object_parts must equal alleged_parts minus primary")
        for score in self.part_visibility_scores.values():
            if score not in (0, 1, 2, 3):
                raise ValueError("part_visibility_scores must use 0-3 scale")
        return self


class EvidenceContext(BaseModel):
    claim: ClaimContext
    claim_observation: ClaimObservation
    images: list[ImageEvidence] = Field(min_length=1)
    observation_complete: bool
    aggregated_at: datetime

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_evidence(self) -> EvidenceContext:
        if len(self.images) != self.claim.image_count:
            raise ValueError("len(images) must equal claim.image_count")
        if self.claim_observation.row_id != self.claim.row_id:
            raise ValueError("claim_observation.row_id must match claim.row_id")
        for image in self.images:
            if image.row_id != self.claim.row_id:
                raise ValueError("image row_id must match claim.row_id")
        return self
