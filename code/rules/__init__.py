"""Deterministic rule layers (no model providers)."""

from rules.consistency import build_consistency_context
from rules.predicates import PREDICATE_IDS, compute_all_predicates, compute_predicate
from rules.requirements_map import (
    REQUIREMENTS_CATALOG,
    RequirementSpec,
    build_active_requirement_ids,
    evaluate_all_requirements,
    evaluate_requirement_satisfaction,
    load_requirements_catalog,
)
from rules.resolve_claim import resolve_claim
from rules.rule_trace import predicate_record_to_hit, records_to_rule_hits, rule_record_to_hit
from rules.sufficiency import evaluate_sufficiency
from rules.trust import evaluate_trust
from rules.compose import COMPOSE_RULE_IDS, compose_claim_decision
from rules.risk import MRR_RULE_IDS, evaluate_risk
from rules.severity import SV_RULE_IDS, evaluate_severity
from rules.supporting_images import SI_RULE_IDS, evaluate_supporting_images
from rules.verdict import CS_RULE_IDS, evaluate_verdict
from rules.types import (
    ComposeStageResult,
    ConsistencyStageResult,
    PredicatesEvaluationBundle,
    PredicatesSnapshot,
    RequirementEvaluationBundle,
    RequirementEvaluationResult,
    ResolveClaimStageResult,
    RiskStageResult,
    RuleExecutionRecord,
    SeverityStageResult,
    SupportingImageStageResult,
    SufficiencyStageResult,
    TraceField,
    TrustStageResult,
    VerdictStageResult,
)

__all__ = [
    "COMPOSE_RULE_IDS",
    "PREDICATE_IDS",
    "REQUIREMENTS_CATALOG",
    "ConsistencyStageResult",
    "ComposeStageResult",
    "PredicatesEvaluationBundle",
    "PredicatesSnapshot",
    "RequirementEvaluationBundle",
    "RequirementEvaluationResult",
    "RequirementSpec",
    "ResolveClaimStageResult",
    "RiskStageResult",
    "RuleExecutionRecord",
    "SeverityStageResult",
    "SufficiencyStageResult",
    "SupportingImageStageResult",
    "TraceField",
    "TrustStageResult",
    "VerdictStageResult",
    "build_active_requirement_ids",
    "build_consistency_context",
    "CS_RULE_IDS",
    "MRR_RULE_IDS",
    "SI_RULE_IDS",
    "SV_RULE_IDS",
    "compute_all_predicates",
    "compute_predicate",
    "compose_claim_decision",
    "evaluate_all_requirements",
    "evaluate_requirement_satisfaction",
    "evaluate_risk",
    "evaluate_severity",
    "evaluate_sufficiency",
    "evaluate_supporting_images",
    "evaluate_trust",
    "evaluate_verdict",
    "load_requirements_catalog",
    "predicate_record_to_hit",
    "records_to_rule_hits",
    "resolve_claim",
    "rule_record_to_hit",
]

