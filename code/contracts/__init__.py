"""Pydantic contracts for the multimodal claim review pipeline (v2)."""

from contracts.decision import (
    ClaimDecision,
    DecisionContext,
    SeverityDecision,
    SupportingImageDecision,
    VerdictDecision,
)
from contracts.enums import (
    CONTRACTS_VERSION,
    ClaimObject,
    ClaimStatus,
    ClaimedSeverityLanguage,
    ContradictionSubtype,
    DamageExtent,
    DatasetSplit,
    HistoryFlag,
    IdentitySide,
    IssueFamily,
    IssueType,
    ObjectPart,
    ObservationPass,
    ResolutionMethod,
    RiskFlag,
    RuleHitStage,
    Severity,
)
from contracts.evaluation import EngineScoreBundle, EvaluationRecord, OutputRowSnapshot
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.primitives import ConfidenceLevel, RuleId, ScoredField, SourceModule
from contracts.reconciliation import (
    ConsistencyContext,
    ImagePairConflict,
    TrustAssessmentContext,
    ValidationContext,
    ValidationPredicates,
)
from contracts.resolution import ClaimResolutionContext, EvidenceContext
from contracts.risk import FlagRuleHit, RiskContext
from contracts.trace import DecisionTrace, RuleHit

__all__ = [
    "CONTRACTS_VERSION",
    "ClaimContext",
    "ClaimDecision",
    "ClaimObservation",
    "ClaimObject",
    "ClaimStatus",
    "ClaimedSeverityLanguage",
    "ConfidenceLevel",
    "ConsistencyContext",
    "ContradictionSubtype",
    "DamageExtent",
    "DatasetSplit",
    "DecisionContext",
    "DecisionTrace",
    "EngineScoreBundle",
    "EvaluationRecord",
    "EvidenceContext",
    "FlagRuleHit",
    "HistoryFlag",
    "IdentitySide",
    "ImageEvidence",
    "ImagePairConflict",
    "IssueFamily",
    "IssueType",
    "ObjectPart",
    "ObservationPass",
    "OutputRowSnapshot",
    "ResolutionMethod",
    "RiskContext",
    "RiskFlag",
    "RuleHit",
    "RuleHitStage",
    "RuleId",
    "ScoredField",
    "Severity",
    "SeverityDecision",
    "SourceModule",
    "SupportingImageDecision",
    "TrustAssessmentContext",
    "ValidationContext",
    "ValidationPredicates",
    "VerdictDecision",
    "ClaimResolutionContext",
]
