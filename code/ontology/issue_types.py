"""Issue type constants and validation."""

from __future__ import annotations

from contracts.enums import IssueType

ALL_ISSUE_TYPES: frozenset[IssueType] = frozenset(IssueType)


def is_valid_issue_type(value: IssueType) -> bool:
    return value in ALL_ISSUE_TYPES
