"""Deterministic rule layers (no model providers)."""

from rules.predicates import (
    PREDICATE_IDS,
    PredicatesSnapshot,
    compute_all_predicates,
    compute_predicate,
)
from rules.requirements_map import (
    REQUIREMENTS_CATALOG,
    RequirementSpec,
    build_active_requirement_ids,
    evaluate_requirement_satisfaction,
    load_requirements_catalog,
)

__all__ = [
    "PREDICATE_IDS",
    "REQUIREMENTS_CATALOG",
    "PredicatesSnapshot",
    "RequirementSpec",
    "build_active_requirement_ids",
    "compute_all_predicates",
    "compute_predicate",
    "evaluate_requirement_satisfaction",
    "load_requirements_catalog",
]
