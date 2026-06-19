"""ClaimContext — immutable intake bundle."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

from contracts.enums import ClaimObject, DatasetSplit, HistoryFlag


class ClaimContext(BaseModel):
    row_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    claim_object: ClaimObject
    user_claim: str = Field(min_length=1)
    image_paths: list[str] = Field(min_length=1)
    image_ids: list[str] = Field(min_length=1)
    image_count: int = Field(ge=1)
    resolved_image_files: list[str] = Field(min_length=1)
    history_flags: list[HistoryFlag] = Field(min_length=1)
    history_summary: str | None = None
    past_claim_count: int = Field(ge=0)
    accept_claim: int = Field(ge=0)
    manual_review_claim: int = Field(ge=0)
    rejected_claim: int = Field(ge=0)
    last_90_days_claim_count: int = Field(ge=0)
    applicable_requirement_ids: list[str] = Field(min_length=1)
    pipeline_version: str = Field(min_length=1)
    observed_at: datetime
    dataset_split: DatasetSplit | None = None
    case_folder: str | None = None
    validate_files_exist: bool = Field(default=False, exclude=True)

    model_config = {"frozen": True}

    @field_validator("user_claim")
    @classmethod
    def user_claim_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("user_claim must not be empty or whitespace")
        return value

    @field_validator("history_flags")
    @classmethod
    def normalize_history_flags(cls, flags: list[HistoryFlag]) -> list[HistoryFlag]:
        if flags == [HistoryFlag.NONE]:
            return flags
        return [flag for flag in flags if flag is not HistoryFlag.NONE] or [HistoryFlag.NONE]

    @model_validator(mode="after")
    def validate_image_consistency(self) -> ClaimContext:
        if not (len(self.image_paths) == len(self.image_ids) == len(self.resolved_image_files) == self.image_count):
            raise ValueError("image_paths, image_ids, resolved_image_files, and image_count must match")
        if self.validate_files_exist:
            for path in self.resolved_image_files:
                if not Path(path).is_file():
                    raise ValueError(f"resolved image file does not exist: {path}")
        return self
