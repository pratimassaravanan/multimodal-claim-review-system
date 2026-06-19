"""RiskContext contract."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from contracts.enums import HistoryFlag, RiskFlag
from contracts.primitives import RuleId
from ontology.risk_flags import risk_flags_are_valid


class FlagRuleHit(BaseModel):
    flag: RiskFlag
    rule_id: str = Field(min_length=1)
    trigger_image_ids: list[str]
    min_confidence_met: bool

    model_config = {"frozen": True}


class RiskContext(BaseModel):
    row_id: str = Field(min_length=1)
    risk_flags: list[RiskFlag] = Field(min_length=1)
    flag_rule_hits: list[FlagRuleHit]
    manual_review_required: bool
    manual_review_rule_ids: list[RuleId]
    history_flags_input: list[HistoryFlag] = Field(min_length=1)
    evaluated_at: datetime

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_risk(self) -> RiskContext:
        if not risk_flags_are_valid(self.risk_flags):
            raise ValueError("invalid risk_flags list: none cannot combine with other flags")
        if HistoryFlag.USER_HISTORY_RISK in self.history_flags_input:
            if RiskFlag.USER_HISTORY_RISK not in self.risk_flags:
                raise ValueError("HR-04: history user_history_risk must appear in risk_flags")
        if self.manual_review_required:
            if RiskFlag.MANUAL_REVIEW_REQUIRED not in self.risk_flags:
                raise ValueError("manual_review_required=true requires flag in risk_flags")
        else:
            if RiskFlag.MANUAL_REVIEW_REQUIRED in self.risk_flags:
                raise ValueError("manual_review_required=false but flag present")
        if self.risk_flags == [RiskFlag.NONE]:
            if self.flag_rule_hits:
                raise ValueError("none risk_flags should have empty flag_rule_hits")
        return self
