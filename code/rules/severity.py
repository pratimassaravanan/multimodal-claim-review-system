"""Severity matrix — decision_matrix §4 (SV-R01..SV-R08)."""

from __future__ import annotations

from datetime import datetime

from contracts.decision import SeverityDecision, VerdictDecision
from contracts.enums import ClaimStatus, DamageExtent, IssueType, Severity
from contracts.observation import ImageEvidence
from contracts.resolution import ClaimResolutionContext
from rules.confidence import confidence_at_least
from rules.image_helpers import select_reference_image, verdict_ref
from rules.types import RuleExecutionRecord, SeverityStageResult, TraceField

SV_RULE_IDS = (
    "SV-R01",
    "SV-R02",
    "SV-R03",
    "SV-R04",
    "SV-R05",
    "SV-R06",
    "SV-R07",
    "SV-R08",
)


def _record(rule_id: str, outcome: bool, justification: str, *pairs: tuple[str, str]) -> RuleExecutionRecord:
    return RuleExecutionRecord(
        rule_id=rule_id,
        outcome=outcome,
        justification=justification,
        trace_fields=[TraceField(key=k, value=v) for k, v in pairs],
    )


def _select_source_image(
    verdict: VerdictDecision,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
) -> ImageEvidence | None:
    if not images:
        return None
    if verdict.claim_status is ClaimStatus.SUPPORTED:
        for image in images:
            if (
                image.visible_part.value == resolution.primary_object_part
                and confidence_at_least(image.visible_part.confidence, "medium")
                and confidence_at_least(image.visible_issue_type.confidence, "medium")
            ):
                return image
    if verdict.claim_status is ClaimStatus.CONTRADICTED:
        if verdict.claim_status_rule_id == "CS-R02":
            for image in images:
                if not image.depicts_claim_object.value and confidence_at_least(
                    image.depicts_claim_object.confidence, "medium"
                ):
                    return image
        return select_reference_image(images, [img.image_id for img in images])
    return select_reference_image(images, [img.image_id for img in images])


def evaluate_severity(
    verdict: VerdictDecision,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
    *,
    evaluated_at: datetime,
) -> SeverityStageResult:
    records: list[RuleExecutionRecord] = []
    ref = verdict_ref(verdict)
    nei = verdict.claim_status is ClaimStatus.NOT_ENOUGH_INFORMATION
    issue_none = verdict.issue_type is IssueType.NONE

    records.append(
        _record(
            "SV-R01",
            nei,
            "Not enough information claim status maps severity to unknown."
            if nei
            else "Claim status is not NEI.",
            ("claim_status", verdict.claim_status.value),
        )
    )
    records.append(
        _record(
            "SV-R02",
            issue_none and not nei,
            "Issue type none maps severity to none."
            if issue_none and not nei
            else "Issue type is not none or NEI preempts SV-R02.",
            ("issue_type", verdict.issue_type.value),
        )
    )

    source = _select_source_image(verdict, images, resolution)
    extent = source.visible_damage_extent.value if source else DamageExtent.UNKNOWN
    source_id = source.image_id if source else None

    extent_rules: list[tuple[str, DamageExtent, Severity]] = [
        ("SV-R03", DamageExtent.HIGH, Severity.HIGH),
        ("SV-R04", DamageExtent.LOW, Severity.LOW),
        ("SV-R05", DamageExtent.MEDIUM, Severity.MEDIUM),
        ("SV-R06", DamageExtent.NONE, Severity.NONE),
    ]
    for rule_id, expected_extent, _severity_value in extent_rules:
        matched = (
            not nei
            and not issue_none
            and extent is expected_extent
        )
        records.append(
            _record(
                rule_id,
                matched,
                f"Visible damage extent {extent.value} on source image."
                if matched
                else f"Extent {extent.value} does not match {expected_extent.value}.",
                ("visible_damage_extent", extent.value),
                ("source_image_id", source_id or "none"),
            )
        )

    sv_r07 = (
        not nei
        and not issue_none
        and extent is DamageExtent.UNKNOWN
        and verdict.claim_status is ClaimStatus.SUPPORTED
    )
    records.append(
        _record(
            "SV-R07",
            sv_r07,
            "Unknown extent on supported claim defaults to medium severity."
            if sv_r07
            else "SV-R07 requires supported status with unknown extent.",
            ("claim_status", verdict.claim_status.value),
            ("visible_damage_extent", extent.value),
        )
    )

    sv_r08 = (
        not nei
        and not issue_none
        and extent is DamageExtent.UNKNOWN
        and verdict.claim_status is ClaimStatus.CONTRADICTED
    )
    records.append(
        _record(
            "SV-R08",
            sv_r08,
            "Unknown extent on contradicted claim with visible issue maps to low severity."
            if sv_r08
            else "SV-R08 conditions not met.",
            ("visible_damage_extent", extent.value),
        )
    )

    winner_rule_id = "SV-R07"
    winner_severity = Severity.MEDIUM
    if nei:
        winner_rule_id = "SV-R01"
        winner_severity = Severity.UNKNOWN
        extent = DamageExtent.UNKNOWN
        source_id = None
    elif issue_none:
        winner_rule_id = "SV-R02"
        winner_severity = Severity.NONE
    else:
        for rule_id, expected_extent, severity_value in extent_rules:
            if extent is expected_extent:
                winner_rule_id = rule_id
                winner_severity = severity_value
                break
        else:
            if sv_r07:
                winner_rule_id = "SV-R07"
                winner_severity = Severity.MEDIUM
            elif sv_r08:
                winner_rule_id = "SV-R08"
                winner_severity = Severity.LOW

    decision = SeverityDecision(
        row_id=verdict.row_id,
        severity=winner_severity,
        severity_rule_id=winner_rule_id,
        visible_damage_extent_source=extent,
        source_image_id=source_id,
        verdict_ref=ref,
        decided_at=evaluated_at,
        claim_status=verdict.claim_status,
        issue_type=verdict.issue_type,
    )
    return SeverityStageResult(severity=decision, rule_records=records)
