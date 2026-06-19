"""Shared enumerations for pipeline contracts."""

from __future__ import annotations

from enum import StrEnum


class ClaimObject(StrEnum):
    CAR = "car"
    LAPTOP = "laptop"
    PACKAGE = "package"


class ClaimStatus(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    NOT_ENOUGH_INFORMATION = "not_enough_information"


class Severity(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class IssueType(StrEnum):
    DENT = "dent"
    SCRATCH = "scratch"
    CRACK = "crack"
    GLASS_SHATTER = "glass_shatter"
    BROKEN_PART = "broken_part"
    MISSING_PART = "missing_part"
    TORN_PACKAGING = "torn_packaging"
    CRUSHED_PACKAGING = "crushed_packaging"
    WATER_DAMAGE = "water_damage"
    STAIN = "stain"
    NONE = "none"
    UNKNOWN = "unknown"


class RiskFlag(StrEnum):
    NONE = "none"
    BLURRY_IMAGE = "blurry_image"
    CROPPED_OR_OBSTRUCTED = "cropped_or_obstructed"
    LOW_LIGHT_OR_GLARE = "low_light_or_glare"
    WRONG_ANGLE = "wrong_angle"
    WRONG_OBJECT = "wrong_object"
    WRONG_OBJECT_PART = "wrong_object_part"
    DAMAGE_NOT_VISIBLE = "damage_not_visible"
    CLAIM_MISMATCH = "claim_mismatch"
    POSSIBLE_MANIPULATION = "possible_manipulation"
    NON_ORIGINAL_IMAGE = "non_original_image"
    TEXT_INSTRUCTION_PRESENT = "text_instruction_present"
    USER_HISTORY_RISK = "user_history_risk"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class IssueFamily(StrEnum):
    DENT_OR_SCRATCH = "dent_or_scratch"
    CRACK_BROKEN_MISSING = "crack_broken_missing"
    CRUSHED_TORN_SEAL = "crushed_torn_seal"
    WATER_STAIN_LABEL = "water_stain_label"
    CONTENTS_OR_ITEM = "contents_or_item"
    SCREEN_KEYBOARD_TRACKPAD = "screen_keyboard_trackpad"
    HINGE_LID_CORNER_BODY_PORT = "hinge_lid_corner_body_port"


class ObjectPart(StrEnum):
    # Car
    FRONT_BUMPER = "front_bumper"
    REAR_BUMPER = "rear_bumper"
    DOOR = "door"
    HOOD = "hood"
    WINDSHIELD = "windshield"
    SIDE_MIRROR = "side_mirror"
    HEADLIGHT = "headlight"
    TAILLIGHT = "taillight"
    FENDER = "fender"
    QUARTER_PANEL = "quarter_panel"
    # Laptop
    SCREEN = "screen"
    KEYBOARD = "keyboard"
    TRACKPAD = "trackpad"
    HINGE = "hinge"
    LID = "lid"
    CORNER = "corner"
    PORT = "port"
    BASE = "base"
    # Package
    BOX = "box"
    PACKAGE_CORNER = "package_corner"
    PACKAGE_SIDE = "package_side"
    SEAL = "seal"
    LABEL = "label"
    CONTENTS = "contents"
    ITEM = "item"
    # Shared
    BODY = "body"
    UNKNOWN = "unknown"


class IdentitySide(StrEnum):
    LEFT = "left"
    RIGHT = "right"
    FRONT = "front"
    REAR = "rear"


class ClaimedSeverityLanguage(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXAGGERATED = "exaggerated"


class DamageExtent(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class HistoryFlag(StrEnum):
    NONE = "none"
    USER_HISTORY_RISK = "user_history_risk"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class ResolutionMethod(StrEnum):
    SINGLE_PART = "single_part"
    VISIBILITY_SCORE = "visibility_score"
    LAST_MENTION_TIEBREAK = "last_mention_tiebreak"


class ContradictionSubtype(StrEnum):
    WRONG_OBJECT = "wrong_object"
    WRONG_PART = "wrong_part"
    ABSENT_DAMAGE = "absent_damage"
    SEVERITY_EXAGGERATION = "severity_exaggeration"
    ISSUE_FAMILY_MISMATCH = "issue_family_mismatch"


class DatasetSplit(StrEnum):
    SAMPLE = "sample"
    TEST = "test"


class ObservationPass(StrEnum):
    PASS_1 = "1"
    PASS_2 = "2"


class RuleHitStage(StrEnum):
    OBSERVE_CLAIM = "observe_claim"
    OBSERVE_IMAGE = "observe_image"
    RESOLVE = "resolve"
    CONSISTENCY = "consistency"
    VALIDATION = "validation"
    TRUST = "trust"
    VERDICT = "verdict"
    SEVERITY = "severity"
    SUPPORTING = "supporting"
    COMPOSE = "compose"
    RISK = "risk"
    EXPLAIN = "explain"


CONTRACTS_VERSION = "2.0"
