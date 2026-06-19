"""Ontology package — closed vocabularies and normalization."""

from ontology.issue_families import (
    CAR_IDENTITY_REQUIREMENT_ID,
    FAMILY_REQUIREMENT_IDS,
    MULTI_IMAGE_REQUIREMENT_ID,
    UNIVERSAL_REQUIREMENT_IDS,
    is_family_compatible_with_part,
    map_issue_type_to_family,
)
from ontology.issue_types import ALL_ISSUE_TYPES, is_valid_issue_type
from ontology.normalize import (
    ensure_valid_issue_type,
    ensure_valid_risk_flag,
    format_risk_flags,
    normalize_claim_status,
    normalize_claimed_severity_language,
    normalize_damage_extent,
    normalize_issue_family,
    normalize_issue_type,
    normalize_object_part,
    normalize_risk_flag,
    normalize_severity,
    parse_history_flags,
    parse_risk_flags,
)
from ontology.object_parts import (
    CAR_PARTS,
    LAPTOP_PARTS,
    PACKAGE_PARTS,
    PARTS_BY_OBJECT,
    get_parts_for_object,
    is_valid_part,
)
from ontology.risk_flags import ACTIVE_RISK_FLAGS, OUTPUT_RISK_FLAGS, is_valid_risk_flag, risk_flags_are_valid

__all__ = [
    "ACTIVE_RISK_FLAGS",
    "ALL_ISSUE_TYPES",
    "CAR_IDENTITY_REQUIREMENT_ID",
    "CAR_PARTS",
    "FAMILY_REQUIREMENT_IDS",
    "LAPTOP_PARTS",
    "MULTI_IMAGE_REQUIREMENT_ID",
    "OUTPUT_RISK_FLAGS",
    "PACKAGE_PARTS",
    "PARTS_BY_OBJECT",
    "UNIVERSAL_REQUIREMENT_IDS",
    "ensure_valid_issue_type",
    "ensure_valid_risk_flag",
    "format_risk_flags",
    "get_parts_for_object",
    "is_family_compatible_with_part",
    "is_valid_issue_type",
    "is_valid_part",
    "is_valid_risk_flag",
    "map_issue_type_to_family",
    "normalize_claim_status",
    "normalize_claimed_severity_language",
    "normalize_damage_extent",
    "normalize_issue_family",
    "normalize_issue_type",
    "normalize_object_part",
    "normalize_risk_flag",
    "normalize_severity",
    "parse_history_flags",
    "parse_risk_flags",
    "risk_flags_are_valid",
]
