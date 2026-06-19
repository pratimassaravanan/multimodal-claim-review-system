"""Ontology normalization tests."""

from contracts.enums import ClaimObject, IssueType, ObjectPart
from ontology.issue_families import map_issue_type_to_family
from ontology.normalize import normalize_object_part


def test_normalize_object_part_invalid_for_object_becomes_unknown():
    assert normalize_object_part("keyboard", ClaimObject.CAR) is ObjectPart.UNKNOWN
    assert normalize_object_part("hood", ClaimObject.CAR) is ObjectPart.HOOD


def test_map_issue_type_to_family_car_glass():
    family = map_issue_type_to_family(
        IssueType.CRACK, ClaimObject.CAR, ObjectPart.WINDSHIELD
    )
    assert family.value == "crack_broken_missing"


def test_map_issue_type_to_family_laptop_screen():
    family = map_issue_type_to_family(
        IssueType.STAIN, ClaimObject.LAPTOP, ObjectPart.SCREEN
    )
    assert family.value == "screen_keyboard_trackpad"
