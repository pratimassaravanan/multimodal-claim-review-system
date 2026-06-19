"""Issue family mappings per decision_matrix §0.3 and §0.4."""

from __future__ import annotations

from contracts.enums import ClaimObject, IssueFamily, IssueType, ObjectPart

# decision_matrix §0.4 — alleged issue type → issue family
ISSUE_TYPE_TO_FAMILY: dict[IssueType, IssueFamily] = {
    IssueType.DENT: IssueFamily.DENT_OR_SCRATCH,
    IssueType.SCRATCH: IssueFamily.DENT_OR_SCRATCH,
    IssueType.CRACK: IssueFamily.CRACK_BROKEN_MISSING,  # default; part context may override
    IssueType.GLASS_SHATTER: IssueFamily.CRACK_BROKEN_MISSING,
    IssueType.BROKEN_PART: IssueFamily.CRACK_BROKEN_MISSING,
    IssueType.MISSING_PART: IssueFamily.CONTENTS_OR_ITEM,
    IssueType.TORN_PACKAGING: IssueFamily.CRUSHED_TORN_SEAL,
    IssueType.CRUSHED_PACKAGING: IssueFamily.CRUSHED_TORN_SEAL,
    IssueType.WATER_DAMAGE: IssueFamily.WATER_STAIN_LABEL,
    IssueType.STAIN: IssueFamily.WATER_STAIN_LABEL,
    IssueType.NONE: IssueFamily.DENT_OR_SCRATCH,
    IssueType.UNKNOWN: IssueFamily.DENT_OR_SCRATCH,
}

# Part-aware overrides for crack/broken on different object regions
CAR_GLASS_LIGHT_PARTS: frozenset[ObjectPart] = frozenset(
    {ObjectPart.WINDSHIELD, ObjectPart.HEADLIGHT, ObjectPart.TAILLIGHT, ObjectPart.SIDE_MIRROR}
)

LAPTOP_SCREEN_INPUT_PARTS: frozenset[ObjectPart] = frozenset(
    {ObjectPart.SCREEN, ObjectPart.KEYBOARD, ObjectPart.TRACKPAD}
)

LAPTOP_BODY_PARTS: frozenset[ObjectPart] = frozenset(
    {ObjectPart.HINGE, ObjectPart.LID, ObjectPart.CORNER, ObjectPart.PORT, ObjectPart.BASE, ObjectPart.BODY}
)

PACKAGE_EXTERIOR_PARTS: frozenset[ObjectPart] = frozenset(
    {ObjectPart.BOX, ObjectPart.PACKAGE_CORNER, ObjectPart.PACKAGE_SIDE, ObjectPart.SEAL}
)

PACKAGE_LABEL_PARTS: frozenset[ObjectPart] = frozenset({ObjectPart.LABEL, ObjectPart.PACKAGE_SIDE})

PACKAGE_CONTENTS_PARTS: frozenset[ObjectPart] = frozenset({ObjectPart.CONTENTS, ObjectPart.ITEM})

# decision_matrix §0.3 — family → additional requirement IDs (universal reqs added elsewhere)
FAMILY_REQUIREMENT_IDS: dict[IssueFamily, tuple[str, ...]] = {
    IssueFamily.DENT_OR_SCRATCH: ("REQ_CAR_BODY_PANEL",),
    IssueFamily.CRACK_BROKEN_MISSING: ("REQ_CAR_GLASS_LIGHT_MIRROR",),
    IssueFamily.CRUSHED_TORN_SEAL: ("REQ_PACKAGE_EXTERIOR",),
    IssueFamily.WATER_STAIN_LABEL: ("REQ_PACKAGE_LABEL_OR_STAIN",),
    IssueFamily.CONTENTS_OR_ITEM: ("REQ_PACKAGE_CONTENTS",),
    IssueFamily.SCREEN_KEYBOARD_TRACKPAD: ("REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD",),
    IssueFamily.HINGE_LID_CORNER_BODY_PORT: ("REQ_LAPTOP_BODY_HINGE_PORT",),
}

UNIVERSAL_REQUIREMENT_IDS: tuple[str, ...] = ("REQ_GENERAL_OBJECT_PART", "REQ_REVIEW_TRUST")
MULTI_IMAGE_REQUIREMENT_ID = "REQ_GENERAL_MULTI_IMAGE"
CAR_IDENTITY_REQUIREMENT_ID = "REQ_CAR_IDENTITY_OR_SIDE"


def map_issue_type_to_family(
    issue_type: IssueType,
    claim_object: ClaimObject,
    object_part: ObjectPart | None = None,
) -> IssueFamily:
    """Map alleged or visible issue type to issue family using part context when needed."""
    if issue_type in (IssueType.TORN_PACKAGING, IssueType.CRUSHED_PACKAGING):
        return IssueFamily.CRUSHED_TORN_SEAL

    if claim_object is ClaimObject.LAPTOP and object_part is not None:
        if object_part in LAPTOP_SCREEN_INPUT_PARTS:
            if issue_type in (IssueType.CRACK, IssueType.GLASS_SHATTER, IssueType.STAIN):
                return IssueFamily.SCREEN_KEYBOARD_TRACKPAD
        if object_part in LAPTOP_BODY_PARTS:
            if issue_type in (IssueType.BROKEN_PART, IssueType.DENT):
                return IssueFamily.HINGE_LID_CORNER_BODY_PORT

    if issue_type in (IssueType.WATER_DAMAGE, IssueType.STAIN):
        return IssueFamily.WATER_STAIN_LABEL
    if issue_type is IssueType.MISSING_PART and claim_object is ClaimObject.PACKAGE:
        return IssueFamily.CONTENTS_OR_ITEM

    if claim_object is ClaimObject.CAR and object_part is not None:
        if issue_type in (IssueType.CRACK, IssueType.GLASS_SHATTER, IssueType.BROKEN_PART):
            if object_part in CAR_GLASS_LIGHT_PARTS:
                return IssueFamily.CRACK_BROKEN_MISSING
            return IssueFamily.DENT_OR_SCRATCH

    if claim_object is ClaimObject.PACKAGE and object_part is not None:
        if object_part in PACKAGE_CONTENTS_PARTS:
            return IssueFamily.CONTENTS_OR_ITEM
        if object_part in PACKAGE_LABEL_PARTS and issue_type is IssueType.STAIN:
            return IssueFamily.WATER_STAIN_LABEL
        if object_part in PACKAGE_EXTERIOR_PARTS:
            return IssueFamily.CRUSHED_TORN_SEAL

    return ISSUE_TYPE_TO_FAMILY.get(issue_type, IssueFamily.DENT_OR_SCRATCH)


def is_family_compatible_with_part(family: IssueFamily, claim_object: ClaimObject, part: ObjectPart) -> bool:
    """Check primary_issue_family is plausible for primary_object_part (decision_matrix §0.3)."""
    if claim_object is ClaimObject.CAR:
        if family is IssueFamily.DENT_OR_SCRATCH:
            return part in {
                ObjectPart.FRONT_BUMPER,
                ObjectPart.REAR_BUMPER,
                ObjectPart.DOOR,
                ObjectPart.HOOD,
                ObjectPart.FENDER,
                ObjectPart.QUARTER_PANEL,
                ObjectPart.BODY,
            }
        if family is IssueFamily.CRACK_BROKEN_MISSING:
            return part in CAR_GLASS_LIGHT_PARTS | {ObjectPart.DOOR, ObjectPart.HOOD, ObjectPart.BODY}
    if claim_object is ClaimObject.LAPTOP:
        if family is IssueFamily.SCREEN_KEYBOARD_TRACKPAD:
            return part in LAPTOP_SCREEN_INPUT_PARTS
        if family is IssueFamily.HINGE_LID_CORNER_BODY_PORT:
            return part in LAPTOP_BODY_PARTS
    if claim_object is ClaimObject.PACKAGE:
        if family is IssueFamily.CRUSHED_TORN_SEAL:
            return part in PACKAGE_EXTERIOR_PARTS
        if family is IssueFamily.WATER_STAIN_LABEL:
            return part in PACKAGE_LABEL_PARTS | {ObjectPart.PACKAGE_SIDE}
        if family is IssueFamily.CONTENTS_OR_ITEM:
            return part in PACKAGE_CONTENTS_PARTS
    return part is ObjectPart.UNKNOWN
