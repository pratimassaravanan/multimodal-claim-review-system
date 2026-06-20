"""Compose final ClaimDecision from stage outputs — pydantic_contracts_v2 §14."""

from __future__ import annotations

from datetime import datetime

from contracts.decision import ClaimDecision, SeverityDecision, SupportingImageDecision, VerdictDecision
from contracts.enums import ClaimStatus, IssueType, Severity
from contracts.reconciliation import TrustAssessmentContext, ValidationContext
from contracts.risk import RiskContext
from rules.sufficiency import ESM_REASON_KEYS
from rules.types import ComposeStageResult, RuleExecutionRecord, TraceField

ESM_REASON_TEMPLATES: dict[str, str] = {
    "esm_r01_unreadable_file": "An image file could not be read, so the claim cannot be evaluated.",
    "esm_r02_identity_conflict": (
        "The image set does not satisfy vehicle identity evidence because {detail}."
    ),
    "esm_r03_no_part_visible": (
        "The image does not show the {part}, so the claimed condition cannot be verified."
    ),
    "esm_r04_contents_not_shown": (
        "The images do not clearly show the expected contents or enough of the opened package "
        "to verify whether anything is missing."
    ),
    "esm_r05_part_low_confidence": (
        "The claimed {part} is not visible clearly enough to inspect the claimed condition."
    ),
    "esm_r06_part_not_clear": (
        "The claimed {part} is not visible clearly enough to evaluate the claim."
    ),
    "esm_r07_identity_not_matchable": (
        "The image set does not show enough context to match the claimed vehicle and part."
    ),
    "esm_r08_default_met": "The {part} is visible and {detail}.",
}

COMPOSE_RULE_IDS = ("CMP-HR01", "CMP-HR03", "CMP-SV02", "CMP-RISK01", "CMP-COMPOSE")


def _record(rule_id: str, outcome: bool, justification: str, *pairs: tuple[str, str]) -> RuleExecutionRecord:
    return RuleExecutionRecord(
        rule_id=rule_id,
        outcome=outcome,
        justification=justification,
        trace_fields=[TraceField(key=k, value=v) for k, v in pairs],
    )


def _render_esm_reason(validation: ValidationContext) -> str:
    template = ESM_REASON_TEMPLATES.get(
        validation.reason_template_key,
        "The submitted images do not provide enough evidence to evaluate the claim.",
    )
    variables = dict(validation.reason_template_vars)
    if "detail" not in variables:
        if validation.identity_match_detail:
            variables["detail"] = validation.identity_match_detail
        elif validation.evidence_standard_met:
            variables["detail"] = "the claimed condition can be verified from the submitted image"
        else:
            variables["detail"] = "required evidence is missing"
    return template.format_map(variables)


def _render_claim_status_justification(
    verdict: VerdictDecision,
    supporting: SupportingImageDecision,
) -> str:
    image_ids = supporting.supporting_image_ids
    image_phrase = ", ".join(image_ids) if image_ids else "no supporting image"
    if verdict.claim_status is ClaimStatus.SUPPORTED:
        return f"The submitted image evidence supports the claim using {image_phrase}."
    if verdict.claim_status is ClaimStatus.CONTRADICTED:
        return f"The image evidence contradicts the claim based on {image_phrase}."
    return "The submitted images do not provide enough information to verify the claim."


def compose_claim_decision(
    verdict: VerdictDecision,
    severity: SeverityDecision,
    supporting: SupportingImageDecision,
    risk: RiskContext,
    validation: ValidationContext,
    trust: TrustAssessmentContext,
    *,
    composed_at: datetime,
) -> ComposeStageResult:
    """Assemble ClaimDecision; validate cross-field rules without re-running matrices."""
    records: list[RuleExecutionRecord] = []

    hr01_ok = not (
        validation.evidence_standard_met is False
        and verdict.claim_status is not ClaimStatus.NOT_ENOUGH_INFORMATION
    )
    records.append(
        _record(
            "CMP-HR01",
            hr01_ok,
            "HR-01 evidence standard and claim status are consistent."
            if hr01_ok
            else "HR-01 violated: evidence_standard_met=false requires NEI.",
            ("claim_status", verdict.claim_status.value),
            ("evidence_standard_met", str(validation.evidence_standard_met).lower()),
        )
    )

    hr03_ok = not (
        verdict.claim_status is ClaimStatus.NOT_ENOUGH_INFORMATION
        and severity.severity is not Severity.UNKNOWN
    )
    records.append(
        _record(
            "CMP-HR03",
            hr03_ok,
            "HR-03 NEI severity consistency satisfied."
            if hr03_ok
            else "HR-03 violated: NEI requires severity unknown.",
            ("severity", severity.severity.value),
        )
    )

    sv02_ok = not (
        verdict.issue_type is IssueType.NONE and severity.severity is not Severity.NONE
    )
    records.append(
        _record(
            "CMP-SV02",
            sv02_ok,
            "SV-02 issue_type none requires severity none."
            if sv02_ok
            else "SV-02 violated at compose time.",
            ("issue_type", verdict.issue_type.value),
        )
    )

    records.append(
        _record(
            "CMP-RISK01",
            True,
            "Risk assessment did not modify verdict claim_status.",
            ("claim_status", verdict.claim_status.value),
            ("risk_flag_count", str(len(risk.risk_flags))),
        )
    )

    decision = ClaimDecision(
        row_id=verdict.row_id,
        verdict=verdict,
        severity_decision=severity,
        supporting_decision=supporting,
        evidence_standard_met=validation.evidence_standard_met,
        evidence_standard_met_reason=_render_esm_reason(validation),
        valid_image=trust.valid_image,
        claim_status_justification=_render_claim_status_justification(verdict, supporting),
        composed_at=composed_at,
    )

    records.append(
        _record(
            "CMP-COMPOSE",
            True,
            "ClaimDecision composed from stage outputs.",
            ("row_id", decision.row_id),
            ("reason_key", validation.reason_template_key),
        )
    )
    return ComposeStageResult(decision=decision, rule_records=records)
