"""Tests for rules.requirements_map."""

from __future__ import annotations

from pathlib import Path

from contracts.enums import ClaimObject, IssueFamily, ObjectPart
from rules.predicates import compute_all_predicates
from rules.requirements_map import (
    REQUIREMENTS_CATALOG,
    build_active_requirement_ids,
    evaluate_requirement_satisfaction,
    load_requirements_catalog,
)
from tests.conftest import make_claim_context, make_image_evidence, make_resolution

REPO_ROOT = Path(__file__).resolve().parents[3]
CSV_PATH = REPO_ROOT / "dataset" / "evidence_requirements.csv"


def test_catalog_matches_csv():
    loaded = load_requirements_catalog(CSV_PATH)
    assert set(loaded) == set(REQUIREMENTS_CATALOG)


def test_req_general_object_part_positive_negative():
    claim = make_claim_context()
    resolution = make_resolution()
    clear = compute_all_predicates(claim, [make_image_evidence(part_visible=True, part_confidence="high")], resolution)
    unclear = compute_all_predicates(claim, [make_image_evidence(part_visible=False, part_confidence="low")], resolution)
    pos = evaluate_requirement_satisfaction("REQ_GENERAL_OBJECT_PART", clear.snapshot, [])
    neg = evaluate_requirement_satisfaction("REQ_GENERAL_OBJECT_PART", unclear.snapshot, [])
    assert pos.satisfied is True
    assert neg.satisfied is False


def test_build_active_requirement_ids_package():
    active = build_active_requirement_ids(
        claim_object=ClaimObject.PACKAGE,
        primary_issue_family=IssueFamily.CRUSHED_TORN_SEAL,
        image_count=1,
        identity_constraint_active=False,
    )
    assert "REQ_PACKAGE_EXTERIOR" in active
    assert "REQ_CAR_BODY_PANEL" not in active
