"""Single-claim end-to-end pipeline wiring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from contracts.decision import ClaimDecision
from contracts.enums import ObjectPart
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.resolution import ClaimResolutionContext, EvidenceContext
from contracts.risk import RiskContext
from contracts.trace import DecisionTrace
from orchestration.fallback import (
    apply_provider_failure_nei,
    fallback_claim_observation,
    fallback_image_evidence,
)
from orchestration.intake import ClaimInputRow
from orchestration.trace_collector import build_decision_trace, build_rule_hits
from providers.exceptions import ProviderError
from providers.gemini import provider_registry
from rules.compose import compose_claim_decision
from rules.consistency import build_consistency_context
from rules.resolve_claim import resolve_claim
from rules.risk import evaluate_risk
from rules.severity import evaluate_severity
from rules.supporting_images import evaluate_supporting_images
from rules.sufficiency import evaluate_sufficiency
from rules.trust import evaluate_trust
from rules.types import RuleExecutionRecord
from rules.verdict import evaluate_verdict


@dataclass
class PipelineArtifacts:
    claim_observation: ClaimObservation
    images: list[ImageEvidence]
    resolution: ClaimResolutionContext
    evidence: EvidenceContext
    decision: ClaimDecision
    risk: RiskContext
    trace: DecisionTrace
    provider_failures: list[str] = field(default_factory=list)
    resolve_records: list[RuleExecutionRecord] = field(default_factory=list)
    consistency_records: list[RuleExecutionRecord] = field(default_factory=list)
    validation_records: list[RuleExecutionRecord] = field(default_factory=list)
    trust_records: list[RuleExecutionRecord] = field(default_factory=list)
    verdict_records: list[RuleExecutionRecord] = field(default_factory=list)
    severity_records: list[RuleExecutionRecord] = field(default_factory=list)
    supporting_records: list[RuleExecutionRecord] = field(default_factory=list)
    risk_records: list[RuleExecutionRecord] = field(default_factory=list)
    compose_records: list[RuleExecutionRecord] = field(default_factory=list)


def _observe_claim(claim: ClaimContext, *, observed_at: datetime, failures: list[str]) -> ClaimObservation:
    flash = provider_registry.get_claim_observer()
    try:
        return flash.observe_claim(claim, observed_at=observed_at)
    except ProviderError as exc:
        failures.append(f"claim_observer: {exc}")
        return fallback_claim_observation(claim, observed_at=observed_at)


def _observe_images(
    claim: ClaimContext,
    *,
    primary_object_part: ObjectPart | None,
    observation_pass: Literal[1, 2],
    observed_at: datetime,
    failures: list[str],
) -> list[ImageEvidence]:
    pro = provider_registry.get_image_observer()
    images: list[ImageEvidence] = []
    for image_id, image_path in zip(claim.image_ids, claim.resolved_image_files, strict=True):
        try:
            images.append(
                pro.observe_image(
                    claim,
                    image_id=image_id,
                    image_path=image_path,
                    primary_object_part=primary_object_part,
                    observation_pass=observation_pass,
                    observed_at=observed_at,
                )
            )
        except ProviderError as exc:
            failures.append(f"image_observer:{image_id}: {exc}")
            images.append(
                fallback_image_evidence(
                    claim,
                    image_id=image_id,
                    image_path=image_path,
                    observed_at=observed_at,
                    observation_pass=observation_pass,
                )
            )
    return images


def process_claim(
    claim: ClaimContext,
    input_row: ClaimInputRow,
    *,
    started_at: datetime,
) -> PipelineArtifacts:
    failures: list[str] = []
    failure_trace: list[tuple[str, str]] = []
    evaluated_at = started_at

    claim_observation = _observe_claim(claim, observed_at=evaluated_at, failures=failures)
    if failures:
        failure_trace.append(("observe_claim", failures[-1]))

    pass1_images = _observe_images(
        claim,
        primary_object_part=None,
        observation_pass=1,
        observed_at=evaluated_at,
        failures=failures,
    )
    for image_id in claim.image_ids:
        marker = f"image_observer:{image_id}:"
        for failure in failures:
            if failure.startswith(marker):
                failure_trace.append(("observe_image", failure))

    resolve_result = resolve_claim(claim, claim_observation, pass1_images, evaluated_at=evaluated_at)
    resolution = resolve_result.resolution

    images = pass1_images
    if resolution.multi_part_claim:
        pass2_images = _observe_images(
            claim,
            primary_object_part=resolution.primary_object_part,
            observation_pass=2,
            observed_at=evaluated_at,
            failures=failures,
        )
        images = pass2_images

    evidence = EvidenceContext(
        claim=claim,
        claim_observation=claim_observation,
        images=images,
        observation_complete=True,
        aggregated_at=evaluated_at,
    )

    consistency_result = build_consistency_context(evidence, resolution, evaluated_at=evaluated_at)
    consistency = consistency_result.consistency

    sufficiency_result = evaluate_sufficiency(evidence, resolution, consistency, evaluated_at=evaluated_at)
    validation = sufficiency_result.validation

    trust_result = evaluate_trust(evidence, resolution, evaluated_at=evaluated_at)
    trust = trust_result.trust

    verdict_result = evaluate_verdict(
        validation,
        trust,
        consistency,
        resolution,
        images=images,
        claim_observation=claim_observation,
        claim_object=claim.claim_object,
        evaluated_at=evaluated_at,
    )
    verdict = verdict_result.verdict

    severity_result = evaluate_severity(verdict, images, resolution, evaluated_at=evaluated_at)
    severity = severity_result.severity

    supporting_result = evaluate_supporting_images(
        verdict,
        images,
        resolution,
        validation,
        consistency,
        claim_object=claim.claim_object,
        evaluated_at=evaluated_at,
    )
    supporting = supporting_result.supporting

    risk_result = evaluate_risk(
        claim,
        claim_observation,
        verdict,
        images,
        validation,
        consistency,
        resolution,
        evaluated_at=evaluated_at,
    )
    risk = risk_result.risk

    compose_result = compose_claim_decision(
        verdict,
        severity,
        supporting,
        risk,
        validation,
        trust,
        composed_at=evaluated_at,
    )
    decision = compose_result.decision

    if failures:
        decision = apply_provider_failure_nei(decision, failures=failures, evaluated_at=evaluated_at)
        verdict = decision.verdict
        severity = decision.severity_decision
        supporting = decision.supporting_decision

    rule_hits = build_rule_hits(
        provider_failures=failure_trace,
        resolve_records=resolve_result.rule_records,
        consistency_records=consistency_result.rule_records,
        validation_records=sufficiency_result.rule_records,
        trust_records=trust_result.rule_records,
        verdict_records=verdict_result.rule_records,
        severity_records=severity_result.rule_records,
        supporting_records=supporting_result.rule_records,
        risk_records=risk_result.rule_records,
        compose_records=compose_result.rule_records,
    )

    trace = build_decision_trace(
        claim=claim,
        evidence=evidence,
        claim_observation=claim_observation,
        resolution=resolution,
        consistency=consistency,
        validation=validation,
        trust=trust,
        verdict=verdict,
        severity_decision=severity,
        supporting_decision=supporting,
        decision=decision,
        risk=risk,
        rule_hits_ordered=rule_hits,
        started_at=started_at,
        completed_at=evaluated_at,
        model_call_counts={
            "claim_observer": 1,
            "image_observer": len(claim.image_ids) * (2 if resolution.multi_part_claim else 1),
        },
    )

    return PipelineArtifacts(
        claim_observation=claim_observation,
        images=images,
        resolution=resolution,
        evidence=evidence,
        decision=decision,
        risk=risk,
        trace=trace,
        provider_failures=failures,
        resolve_records=resolve_result.rule_records,
        consistency_records=consistency_result.rule_records,
        validation_records=sufficiency_result.rule_records,
        trust_records=trust_result.rule_records,
        verdict_records=verdict_result.rule_records,
        severity_records=severity_result.rule_records,
        supporting_records=supporting_result.rule_records,
        risk_records=risk_result.rule_records,
        compose_records=compose_result.rule_records,
    )
