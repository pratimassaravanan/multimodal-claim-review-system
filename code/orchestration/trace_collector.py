"""Assemble DecisionTrace and deterministic hash."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from contracts.decision import ClaimDecision, SeverityDecision, SupportingImageDecision, VerdictDecision
from contracts.enums import RuleHitStage
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation
from contracts.reconciliation import ConsistencyContext, TrustAssessmentContext, ValidationContext
from contracts.resolution import ClaimResolutionContext, EvidenceContext
from contracts.risk import RiskContext
from contracts.trace import DecisionTrace, RuleHit
from orchestration.intake import PIPELINE_VERSION
from rules.rule_trace import records_to_rule_hits
from rules.types import RuleExecutionRecord


def compute_deterministic_hash(trace_payload: dict) -> str:
    encoded = json.dumps(trace_payload, sort_keys=True, default=str)
    return f"sha256:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


def build_rule_hits(
    *,
    provider_failures: list[tuple[str, str]],
    resolve_records: list[RuleExecutionRecord],
    consistency_records: list[RuleExecutionRecord],
    validation_records: list[RuleExecutionRecord],
    trust_records: list[RuleExecutionRecord],
    verdict_records: list[RuleExecutionRecord],
    severity_records: list[RuleExecutionRecord],
    supporting_records: list[RuleExecutionRecord],
    risk_records: list[RuleExecutionRecord],
    compose_records: list[RuleExecutionRecord],
) -> list[RuleHit]:
    hits: list[RuleHit] = []
    sequence = 1
    for stage_name, message in provider_failures:
        stage = (
            RuleHitStage.OBSERVE_CLAIM
            if stage_name == "observe_claim"
            else RuleHitStage.OBSERVE_IMAGE
        )
        hits.append(
            RuleHit(
                sequence=sequence,
                stage=stage,
                rule_id="PROVIDER-FAILURE",
                matched=True,
                inputs_snapshot={"stage": stage_name},
                outputs_snapshot={"justification": message},
            )
        )
        sequence += 1

    stage_groups: list[tuple[RuleHitStage, list[RuleExecutionRecord]]] = [
        (RuleHitStage.RESOLVE, resolve_records),
        (RuleHitStage.CONSISTENCY, consistency_records),
        (RuleHitStage.VALIDATION, validation_records),
        (RuleHitStage.TRUST, trust_records),
        (RuleHitStage.VERDICT, verdict_records),
        (RuleHitStage.SEVERITY, severity_records),
        (RuleHitStage.SUPPORTING, supporting_records),
        (RuleHitStage.RISK, risk_records),
        (RuleHitStage.COMPOSE, compose_records),
    ]
    for stage, records in stage_groups:
        if not records:
            continue
        converted = records_to_rule_hits(records, stage=stage, start_sequence=sequence)
        hits.extend(converted)
        sequence += len(converted)
    return hits


def build_decision_trace(
    *,
    claim: ClaimContext,
    evidence: EvidenceContext,
    claim_observation: ClaimObservation,
    resolution: ClaimResolutionContext,
    consistency: ConsistencyContext,
    validation: ValidationContext,
    trust: TrustAssessmentContext,
    verdict: VerdictDecision,
    severity_decision: SeverityDecision,
    supporting_decision: SupportingImageDecision,
    decision: ClaimDecision,
    risk: RiskContext,
    rule_hits_ordered: list[RuleHit],
    started_at: datetime,
    completed_at: datetime,
    model_call_counts: dict[str, int] | None = None,
) -> DecisionTrace:
    hash_payload = {
        "row_id": claim.row_id,
        "observation_raw_hash": claim_observation.observation_raw_hash,
        "verdict_rule_id": verdict.claim_status_rule_id,
        "severity_rule_id": severity_decision.severity_rule_id,
        "supporting_image_rule_id": supporting_decision.supporting_image_rule_id,
        "risk_flags": [flag.value for flag in risk.risk_flags],
    }
    return DecisionTrace(
        row_id=claim.row_id,
        pipeline_version=PIPELINE_VERSION,
        claim=claim,
        evidence=evidence,
        claim_observation=claim_observation,
        resolution=resolution,
        consistency=consistency,
        validation=validation,
        trust=trust,
        verdict=verdict,
        severity_decision=severity_decision,
        supporting_decision=supporting_decision,
        decision=decision,
        risk=risk,
        rule_hits_ordered=rule_hits_ordered,
        started_at=started_at,
        completed_at=completed_at,
        deterministic_hash=compute_deterministic_hash(hash_payload),
        model_call_counts=model_call_counts,
    )
