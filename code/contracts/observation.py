"""ClaimObservation and ImageEvidence contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from contracts.enums import (
    ClaimObject,
    ClaimedSeverityLanguage,
    DamageExtent,
    IdentitySide,
    IssueFamily,
    IssueType,
    ObjectPart,
)
from contracts.primitives import ConfidenceLevel, ScoredField
from ontology.object_parts import is_valid_part


class ClaimObservation(BaseModel):
    row_id: str = Field(min_length=1)
    alleged_parts: list[ObjectPart] = Field(min_length=1)
    alleged_issue_types: list[IssueType] = Field(min_length=1)
    alleged_issue_families: list[IssueFamily] = Field(min_length=1)
    exclusions: list[str]
    identity_constraint_active: ScoredField[bool]
    identity_side: ScoredField[IdentitySide] | None = None
    identity_color: ScoredField[str] | None = None
    claimed_damage_alleged: ScoredField[bool]
    claimed_severity_language: ScoredField[ClaimedSeverityLanguage]
    multi_part_detected: bool
    injection_detected_in_chat: bool
    injection_excerpt: str | None = None
    sanitized_claim_excerpt: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    observation_raw_hash: str = Field(min_length=1)
    observed_at: datetime
    detected_languages: list[str] | None = None
    last_customer_message_excerpt: str | None = None
    overall_extraction_confidence: ConfidenceLevel | None = None
    claim_object: ClaimObject | None = Field(default=None, exclude=True)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_observation(self) -> ClaimObservation:
        expected_multi = len(self.alleged_parts) > 1
        if self.multi_part_detected != expected_multi:
            raise ValueError("multi_part_detected must equal len(alleged_parts) > 1")
        if self.claim_object is not None:
            for part in self.alleged_parts:
                if not is_valid_part(part, self.claim_object):
                    raise ValueError(f"alleged part {part} invalid for {self.claim_object}")
        if (
            self.injection_detected_in_chat
            and self.injection_excerpt
            and self.injection_excerpt in self.sanitized_claim_excerpt
        ):
            raise ValueError("sanitized_claim_excerpt must not contain actionable injection text")
        return self


class ImageEvidence(BaseModel):
    row_id: str = Field(min_length=1)
    image_id: str = Field(min_length=1)
    image_path: str = Field(min_length=1)
    file_readable: bool
    usable_for_automated_review: bool
    depicts_claim_object: ScoredField[bool]
    visible_part: ScoredField[ObjectPart]
    claimed_primary_part_visible: ScoredField[bool]
    visible_issue_type: ScoredField[IssueType]
    visible_damage_extent: ScoredField[DamageExtent]
    is_blurry: ScoredField[bool]
    is_cropped_or_obstructed: ScoredField[bool]
    is_low_light_or_glare: ScoredField[bool]
    is_wrong_angle_for_claimed_part: ScoredField[bool]
    is_non_original_image: ScoredField[bool]
    is_possibly_manipulated: ScoredField[bool]
    has_instruction_text: ScoredField[bool]
    package_is_opened: ScoredField[bool]
    contents_area_visible: ScoredField[bool]
    vehicle_identity_features: list[str]
    model_name: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    observed_at: datetime
    observation_pass: Literal[1, 2] = 1
    observation_raw_hash: str | None = None
    injection_text_excerpt: str | None = None
    claim_object: ClaimObject | None = Field(default=None, exclude=True)
    allowed_image_ids: list[str] | None = Field(default=None, exclude=True)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_image_evidence(self) -> ImageEvidence:
        if self.allowed_image_ids is not None and self.image_id not in self.allowed_image_ids:
            raise ValueError(f"image_id {self.image_id} not in claim image_ids")
        if not self.file_readable:
            low_fields = [
                self.depicts_claim_object,
                self.visible_part,
                self.claimed_primary_part_visible,
                self.visible_issue_type,
                self.visible_damage_extent,
            ]
            for field in low_fields:
                if field.confidence != "low":
                    raise ValueError("unreadable file requires low confidence on scored observation fields")
        if self.claim_object is not None:
            if not is_valid_part(self.visible_part.value, self.claim_object):
                raise ValueError(f"visible_part {self.visible_part.value} invalid for {self.claim_object}")
        return self
