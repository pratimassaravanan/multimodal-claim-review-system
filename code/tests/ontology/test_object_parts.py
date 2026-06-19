"""Object part ontology validation tests."""

import pytest

from contracts.enums import ClaimObject, ObjectPart
from ontology.object_parts import (
    CAR_PARTS,
    LAPTOP_PARTS,
    PACKAGE_PARTS,
    get_parts_for_object,
    is_valid_part,
)


def test_car_parts_include_rear_bumper():
    assert ObjectPart.REAR_BUMPER in CAR_PARTS
    assert ObjectPart.SCREEN not in CAR_PARTS


def test_laptop_parts_include_screen():
    assert ObjectPart.SCREEN in LAPTOP_PARTS
    assert ObjectPart.HOOD not in LAPTOP_PARTS


def test_package_parts_include_seal():
    assert ObjectPart.SEAL in PACKAGE_PARTS
    assert ObjectPart.DOOR not in PACKAGE_PARTS


@pytest.mark.parametrize(
    "claim_object, part, expected",
    [
        (ClaimObject.CAR, ObjectPart.DOOR, True),
        (ClaimObject.CAR, ObjectPart.KEYBOARD, False),
        (ClaimObject.LAPTOP, ObjectPart.TRACKPAD, True),
        (ClaimObject.PACKAGE, ObjectPart.CONTENTS, True),
        (ClaimObject.PACKAGE, ObjectPart.WINDSHIELD, False),
    ],
)
def test_is_valid_part(claim_object, part, expected):
    assert is_valid_part(part, claim_object) is expected


def test_get_parts_for_object_matches_sets():
    assert get_parts_for_object(ClaimObject.CAR) is CAR_PARTS
    assert get_parts_for_object(ClaimObject.LAPTOP) is LAPTOP_PARTS
    assert get_parts_for_object(ClaimObject.PACKAGE) is PACKAGE_PARTS


def test_unknown_allowed_for_all_objects():
    for obj in ClaimObject:
        assert is_valid_part(ObjectPart.UNKNOWN, obj)
