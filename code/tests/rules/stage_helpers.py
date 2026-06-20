"""Helpers for P3 rule stage tests."""

from __future__ import annotations

from contracts.decision import SeverityDecision, SupportingImageDecision, VerdictDecision
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.reconciliation import ConsistencyContext, TrustAssessmentContext, ValidationContext
from contracts.resolution import ClaimResolutionContext
from contracts.risk import RiskContext
from rules.compose import compose_claim_decision
from rules.consistency import build_consistency_context
from rules.risk import evaluate_risk
from rules.severity import evaluate_severity
from rules.sufficiency import evaluate_sufficiency
from rules.supporting_images import evaluate_supporting_images
from rules.trust import evaluate_trust
from rules.types import (
    ComposeStageResult,
    RiskStageResult,
    SeverityStageResult,
    SupportingImageStageResult,
    VerdictStageResult,
)
from rules.verdict import evaluate_verdict
from tests.conftest import NOW, make_evidence_context
from tests.rules.verdict_helpers import run_verdict


def run_severity(
    verdict: VerdictDecision,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
) -> SeverityStageResult:
    return evaluate_severity(verdict, images, resolution, evaluated_at=NOW)


def run_supporting(
    *,
    claim: ClaimContext,
    observation: ClaimObservation,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
    verdict: VerdictDecision | None = None,
) -> SupportingImageStageResult:
    evidence = make_evidence_context(claim=claim, observation=observation, images=images)
    consistency = build_consistency_context(evidence, resolution, evaluated_at=NOW).consistency
    validation = evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=NOW).validation
    if verdict is None:
        verdict = run_verdict(
            claim=claim,
            observation=observation,
            images=images,
            resolution=resolution,
        ).verdict
    return evaluate_supporting_images(
        verdict,
        images,
        resolution,
        validation,
        consistency,
        claim_object=claim.claim_object,
        evaluated_at=NOW,
    )


def run_risk(
    *,
    claim: ClaimContext,
    observation: ClaimObservation,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
    verdict: VerdictDecision | None = None,
) -> RiskStageResult:
    evidence = make_evidence_context(claim=claim, observation=observation, images=images)
    consistency = build_consistency_context(evidence, resolution, evaluated_at=NOW).consistency
    validation = evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=NOW).validation
    if verdict is None:
        verdict = run_verdict(
            claim=claim,
            observation=observation,
            images=images,
            resolution=resolution,
        ).verdict
    return evaluate_risk(
        claim,
        observation,
        verdict,
        images,
        validation,
        consistency,
        resolution,
        evaluated_at=NOW,
    )


def run_compose(
    *,
    claim: ClaimContext,
    observation: ClaimObservation,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
    verdict: VerdictDecision | None = None,
    severity: SeverityDecision | None = None,
    supporting: SupportingImageDecision | None = None,
    risk: RiskContext | None = None,
) -> ComposeStageResult:
    evidence = make_evidence_context(claim=claim, observation=observation, images=images)
    consistency = build_consistency_context(evidence, resolution, evaluated_at=NOW).consistency
    validation = evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=NOW).validation
    trust = evaluate_trust(evidence, resolution, evaluated_at=NOW).trust
    if verdict is None:
        verdict = evaluate_verdict(
            validation,
            trust,
            consistency,
            resolution,
            images=images,
            claim_observation=observation,
            claim_object=claim.claim_object,
            evaluated_at=NOW,
        ).verdict
    if severity is None:
        severity = evaluate_severity(verdict, images, resolution, evaluated_at=NOW).severity
    if supporting is None:
        supporting = evaluate_supporting_images(
            verdict,
            images,
            resolution,
            validation,
            consistency,
            claim_object=claim.claim_object,
            evaluated_at=NOW,
        ).supporting
    if risk is None:
        risk = evaluate_risk(
            claim,
            observation,
            verdict,
            images,
            validation,
            consistency,
            resolution,
            evaluated_at=NOW,
        ).risk
    return compose_claim_decision(
        verdict,
        severity,
        supporting,
        risk,
        validation,
        trust,
        composed_at=NOW,
    )


def record_outcome(result, rule_id: str) -> bool | None:
    for record in result.rule_records:
        if record.rule_id == rule_id:
            return record.outcome
    return None
