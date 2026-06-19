"""Issue type ontology validation tests."""

import pytest

from contracts.enums import IssueType
from ontology.issue_types import ALL_ISSUE_TYPES, is_valid_issue_type
from ontology.normalize import normalize_issue_type


def test_all_issue_types_contains_problem_statement_values():
    for value in [
        "dent",
        "scratch",
        "crack",
        "glass_shatter",
        "broken_part",
        "missing_part",
        "torn_packaging",
        "crushed_packaging",
        "water_damage",
        "stain",
        "none",
        "unknown",
    ]:
        assert IssueType(value) in ALL_ISSUE_TYPES


@pytest.mark.parametrize("issue_type", list(IssueType))
def test_is_valid_issue_type_accepts_all_enums(issue_type):
    assert is_valid_issue_type(issue_type)


def test_normalize_issue_type_synonyms():
    assert normalize_issue_type("scrape") is IssueType.SCRATCH
    assert normalize_issue_type("shattered") is IssueType.CRACK


def test_normalize_issue_type_unknown_fallback():
    assert normalize_issue_type("rust") is IssueType.UNKNOWN
    assert normalize_issue_type(None) is IssueType.UNKNOWN
