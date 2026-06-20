"""Helpers for verdict rule tests."""

from __future__ import annotations

from contracts.enums import ClaimObject
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.resolution import ClaimResolutionContext
from rules.consistency import build_consistency_context
from rules.sufficiency import evaluate_sufficiency
from rules.trust import evaluate_trust
from rules.types import VerdictStageResult
from rules.verdict import evaluate_verdict
from tests.conftest import NOW, make_evidence_context


def run_verdict(
    *,
    claim: ClaimContext,
    observation: ClaimObservation,
    images: list[ImageEvidence],
    resolution: ClaimResolutionContext,
) -> VerdictStageResult:
    evidence = make_evidence_context(claim=claim, observation=observation, images=images)
    consistency = build_consistency_context(evidence, resolution, evaluated_at=NOW).consistency
    validation = evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=NOW).validation
    trust = evaluate_trust(evidence, resolution, evaluated_at=NOW).trust
    return evaluate_verdict(
        validation,
        trust,
        consistency,
        resolution,
        images=images,
        claim_observation=observation,
        claim_object=claim.claim_object,
        evaluated_at=NOW,
    )


def record_outcome(result: VerdictStageResult, rule_id: str) -> bool | None:
    for record in result.rule_records:
        if record.rule_id == rule_id:
            return record.outcome
    return None
