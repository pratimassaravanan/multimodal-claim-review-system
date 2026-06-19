"""Object part constants and per-claim_object validation."""

from __future__ import annotations

from contracts.enums import ClaimObject, ObjectPart

CAR_PARTS: frozenset[ObjectPart] = frozenset(
    {
        ObjectPart.FRONT_BUMPER,
        ObjectPart.REAR_BUMPER,
        ObjectPart.DOOR,
        ObjectPart.HOOD,
        ObjectPart.WINDSHIELD,
        ObjectPart.SIDE_MIRROR,
        ObjectPart.HEADLIGHT,
        ObjectPart.TAILLIGHT,
        ObjectPart.FENDER,
        ObjectPart.QUARTER_PANEL,
        ObjectPart.BODY,
        ObjectPart.UNKNOWN,
    }
)

LAPTOP_PARTS: frozenset[ObjectPart] = frozenset(
    {
        ObjectPart.SCREEN,
        ObjectPart.KEYBOARD,
        ObjectPart.TRACKPAD,
        ObjectPart.HINGE,
        ObjectPart.LID,
        ObjectPart.CORNER,
        ObjectPart.PORT,
        ObjectPart.BASE,
        ObjectPart.BODY,
        ObjectPart.UNKNOWN,
    }
)

PACKAGE_PARTS: frozenset[ObjectPart] = frozenset(
    {
        ObjectPart.BOX,
        ObjectPart.PACKAGE_CORNER,
        ObjectPart.PACKAGE_SIDE,
        ObjectPart.SEAL,
        ObjectPart.LABEL,
        ObjectPart.CONTENTS,
        ObjectPart.ITEM,
        ObjectPart.UNKNOWN,
    }
)

PARTS_BY_OBJECT: dict[ClaimObject, frozenset[ObjectPart]] = {
    ClaimObject.CAR: CAR_PARTS,
    ClaimObject.LAPTOP: LAPTOP_PARTS,
    ClaimObject.PACKAGE: PACKAGE_PARTS,
}


def get_parts_for_object(claim_object: ClaimObject) -> frozenset[ObjectPart]:
    return PARTS_BY_OBJECT[claim_object]


def is_valid_part(part: ObjectPart, claim_object: ClaimObject) -> bool:
    return part in PARTS_BY_OBJECT[claim_object]
