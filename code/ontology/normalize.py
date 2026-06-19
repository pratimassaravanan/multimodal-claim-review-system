"""Normalize raw strings and model outputs to closed ontology enums."""

from __future__ import annotations

from contracts.enums import (
    ClaimObject,
    ClaimedSeverityLanguage,
    ClaimStatus,
    DamageExtent,
    HistoryFlag,
    IssueFamily,
    IssueType,
    ObjectPart,
    RiskFlag,
    Severity,
)
from ontology.issue_families import map_issue_type_to_family
from ontology.issue_types import ALL_ISSUE_TYPES
from ontology.object_parts import PARTS_BY_OBJECT
from ontology.risk_flags import OUTPUT_RISK_FLAGS

_ISSUE_SYNONYMS: dict[str, IssueType] = {
    "scrape": IssueType.SCRATCH,
    "scuff": IssueType.SCRATCH,
    "shatter": IssueType.CRACK,
    "shattered": IssueType.CRACK,
    "glass_shatter": IssueType.GLASS_SHATTER,
    "broken": IssueType.BROKEN_PART,
    "crushed": IssueType.CRUSHED_PACKAGING,
    "torn": IssueType.TORN_PACKAGING,
    "water": IssueType.WATER_DAMAGE,
    "oil_stain": IssueType.STAIN,
}

_PART_SYNONYMS: dict[str, ObjectPart] = {
    "bumper": ObjectPart.REAR_BUMPER,
    "rear": ObjectPart.REAR_BUMPER,
    "front": ObjectPart.FRONT_BUMPER,
    "windshield": ObjectPart.WINDSHIELD,
    "mirror": ObjectPart.SIDE_MIRROR,
    "track_pad": ObjectPart.TRACKPAD,
    "package": ObjectPart.BOX,
}


def _clean_token(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def normalize_issue_type(raw: str | IssueType | None) -> IssueType:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return IssueType.UNKNOWN
    if isinstance(raw, IssueType):
        return raw
    token = _clean_token(raw)
    if token in IssueType._value2member_map_:
        return IssueType(token)
    return _ISSUE_SYNONYMS.get(token, IssueType.UNKNOWN)


def normalize_object_part(
    raw: str | ObjectPart | None,
    claim_object: ClaimObject,
) -> ObjectPart:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return ObjectPart.UNKNOWN
    if isinstance(raw, ObjectPart):
        candidate = raw
    else:
        token = _clean_token(raw)
        if token in ObjectPart._value2member_map_:
            candidate = ObjectPart(token)
        else:
            candidate = _PART_SYNONYMS.get(token, ObjectPart.UNKNOWN)

    allowed = PARTS_BY_OBJECT[claim_object]
    return candidate if candidate in allowed else ObjectPart.UNKNOWN


def normalize_risk_flag(raw: str | RiskFlag | None) -> RiskFlag | None:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    if isinstance(raw, RiskFlag):
        return raw
    token = _clean_token(raw)
    if token in RiskFlag._value2member_map_:
        return RiskFlag(token)
    return None


def parse_risk_flags(raw: str | None) -> list[RiskFlag]:
    if raw is None or not raw.strip() or raw.strip().lower() == "none":
        return [RiskFlag.NONE]
    flags: list[RiskFlag] = []
    for piece in raw.split(";"):
        normalized = normalize_risk_flag(piece)
        if normalized is not None and normalized not in flags:
            flags.append(normalized)
    return flags or [RiskFlag.NONE]


def format_risk_flags(flags: list[RiskFlag]) -> str:
    if not flags or flags == [RiskFlag.NONE]:
        return "none"
    active = sorted({flag.value for flag in flags if flag is not RiskFlag.NONE})
    return ";".join(active) if active else "none"


def parse_history_flags(raw: str | None) -> list[HistoryFlag]:
    if raw is None or not raw.strip() or raw.strip().lower() == "none":
        return [HistoryFlag.NONE]
    flags: list[HistoryFlag] = []
    for piece in raw.split(";"):
        token = _clean_token(piece)
        if token in HistoryFlag._value2member_map_:
            flag = HistoryFlag(token)
            if flag not in flags:
                flags.append(flag)
    return flags or [HistoryFlag.NONE]


def normalize_claim_status(raw: str | ClaimStatus | None) -> ClaimStatus | None:
    if raw is None:
        return None
    if isinstance(raw, ClaimStatus):
        return raw
    token = _clean_token(raw)
    if token in ClaimStatus._value2member_map_:
        return ClaimStatus(token)
    return None


def normalize_severity(raw: str | Severity | None) -> Severity:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return Severity.UNKNOWN
    if isinstance(raw, Severity):
        return raw
    token = _clean_token(raw)
    if token in Severity._value2member_map_:
        return Severity(token)
    return Severity.UNKNOWN


def normalize_damage_extent(raw: str | DamageExtent | None) -> DamageExtent:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return DamageExtent.UNKNOWN
    if isinstance(raw, DamageExtent):
        return raw
    token = _clean_token(raw)
    if token in DamageExtent._value2member_map_:
        return DamageExtent(token)
    return DamageExtent.UNKNOWN


def normalize_claimed_severity_language(raw: str | ClaimedSeverityLanguage | None) -> ClaimedSeverityLanguage:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return ClaimedSeverityLanguage.NONE
    if isinstance(raw, ClaimedSeverityLanguage):
        return raw
    token = _clean_token(raw)
    if token in ClaimedSeverityLanguage._value2member_map_:
        return ClaimedSeverityLanguage(token)
    if token in {"bad", "severe", "pretty_bad"}:
        return ClaimedSeverityLanguage.EXAGGERATED
    return ClaimedSeverityLanguage.NONE


def normalize_issue_family(
    raw: str | IssueFamily | None,
    *,
    issue_type: IssueType | None = None,
    claim_object: ClaimObject | None = None,
    object_part: ObjectPart | None = None,
) -> IssueFamily:
    if isinstance(raw, IssueFamily):
        return raw
    if isinstance(raw, str) and raw.strip():
        token = _clean_token(raw)
        if token in IssueFamily._value2member_map_:
            return IssueFamily(token)
    if issue_type is not None and claim_object is not None:
        return map_issue_type_to_family(issue_type, claim_object, object_part)
    return IssueFamily.DENT_OR_SCRATCH


def ensure_valid_issue_type(value: IssueType) -> IssueType:
    return value if value in ALL_ISSUE_TYPES else IssueType.UNKNOWN


def ensure_valid_risk_flag(value: RiskFlag) -> RiskFlag:
    return value if value in OUTPUT_RISK_FLAGS else RiskFlag.NONE
