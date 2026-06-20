"""Coverage tests for severity.py — SV-R01..SV-R08."""

from __future__ import annotations

from contracts.decision import VerdictDecision
from contracts.enums import ClaimStatus, DamageExtent, IssueType, ObjectPart, Severity
from rules.severity import SV_RULE_IDS
from tests.conftest import NOW, make_image_evidence, make_resolution
from tests.rules.stage_helpers import record_outcome, run_severity


def _verdict(**kwargs) -> VerdictDecision:
    defaults = {
        "row_id": "user_001:case_001",
        "claim_status": ClaimStatus.SUPPORTED,
        "claim_status_rule_id": "CS-R07",
        "issue_type": IssueType.DENT,
        "object_part": ObjectPart.REAR_BUMPER,
        "decided_at": NOW,
    }
    defaults.update(kwargs)
    return VerdictDecision(**defaults)


def test_all_sv_rules_emitted_on_supported_extent_path():
    verdict = _verdict()
    images = [make_image_evidence(visible_damage_extent=DamageExtent.MEDIUM)]
    result = run_severity(verdict, images, make_resolution())
    emitted = {record.rule_id for record in result.rule_records}
    assert set(SV_RULE_IDS).issubset(emitted)
    assert result.severity.severity_rule_id == "SV-R05"


def test_sv_r01_positive():
    verdict = _verdict(
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        claim_status_rule_id="CS-R01",
        issue_type=IssueType.UNKNOWN,
    )
    result = run_severity(verdict, [make_image_evidence()], make_resolution())
    assert result.severity.severity is Severity.UNKNOWN
    assert record_outcome(result, "SV-R01") is True


def test_sv_r01_negative():
    verdict = _verdict()
    result = run_severity(verdict, [make_image_evidence()], make_resolution())
    assert record_outcome(result, "SV-R01") is False


def test_sv_r02_positive():
    verdict = _verdict(issue_type=IssueType.NONE)
    result = run_severity(verdict, [make_image_evidence()], make_resolution())
    assert result.severity.severity is Severity.NONE
    assert record_outcome(result, "SV-R02") is True


def test_sv_r02_negative():
    verdict = _verdict(issue_type=IssueType.DENT)
    result = run_severity(verdict, [make_image_evidence()], make_resolution())
    assert record_outcome(result, "SV-R02") is False


def test_sv_r03_positive():
    verdict = _verdict()
    images = [make_image_evidence(visible_damage_extent=DamageExtent.HIGH)]
    result = run_severity(verdict, images, make_resolution())
    assert result.severity.severity is Severity.HIGH
    assert record_outcome(result, "SV-R03") is True


def test_sv_r03_negative():
    verdict = _verdict()
    images = [make_image_evidence(visible_damage_extent=DamageExtent.MEDIUM)]
    result = run_severity(verdict, images, make_resolution())
    assert record_outcome(result, "SV-R03") is False


def test_sv_r04_positive():
    verdict = _verdict()
    images = [make_image_evidence(visible_damage_extent=DamageExtent.LOW)]
    result = run_severity(verdict, images, make_resolution())
    assert result.severity.severity is Severity.LOW
    assert record_outcome(result, "SV-R04") is True


def test_sv_r04_negative():
    verdict = _verdict()
    images = [make_image_evidence(visible_damage_extent=DamageExtent.MEDIUM)]
    result = run_severity(verdict, images, make_resolution())
    assert record_outcome(result, "SV-R04") is False


def test_sv_r05_positive():
    verdict = _verdict()
    images = [make_image_evidence(visible_damage_extent=DamageExtent.MEDIUM)]
    result = run_severity(verdict, images, make_resolution())
    assert result.severity.severity is Severity.MEDIUM
    assert record_outcome(result, "SV-R05") is True


def test_sv_r05_negative():
    verdict = _verdict()
    images = [make_image_evidence(visible_damage_extent=DamageExtent.HIGH)]
    result = run_severity(verdict, images, make_resolution())
    assert record_outcome(result, "SV-R05") is False


def test_sv_r06_positive():
    verdict = _verdict(issue_type=IssueType.SCRATCH)
    images = [make_image_evidence(visible_damage_extent=DamageExtent.NONE, visible_issue_type=IssueType.SCRATCH)]
    result = run_severity(verdict, images, make_resolution())
    assert result.severity.severity is Severity.NONE
    assert record_outcome(result, "SV-R06") is True


def test_sv_r06_negative():
    verdict = _verdict(issue_type=IssueType.SCRATCH)
    images = [
        make_image_evidence(
            visible_damage_extent=DamageExtent.LOW,
            visible_issue_type=IssueType.SCRATCH,
        )
    ]
    result = run_severity(verdict, images, make_resolution())
    assert record_outcome(result, "SV-R06") is False


def test_sv_r07_positive():
    verdict = _verdict()
    images = [make_image_evidence(visible_damage_extent=DamageExtent.UNKNOWN)]
    result = run_severity(verdict, images, make_resolution())
    assert result.severity.severity is Severity.MEDIUM
    assert record_outcome(result, "SV-R07") is True


def test_sv_r07_negative():
    verdict = _verdict(
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R04",
    )
    images = [make_image_evidence(visible_damage_extent=DamageExtent.UNKNOWN)]
    result = run_severity(verdict, images, make_resolution())
    assert record_outcome(result, "SV-R07") is False


def test_sv_r08_positive():
    verdict = _verdict(
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R04",
        issue_type=IssueType.DENT,
    )
    images = [make_image_evidence(visible_damage_extent=DamageExtent.UNKNOWN)]
    result = run_severity(verdict, images, make_resolution())
    assert result.severity.severity is Severity.LOW
    assert record_outcome(result, "SV-R08") is True


def test_sv_r08_negative():
    verdict = _verdict(
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R04",
        issue_type=IssueType.DENT,
    )
    images = [make_image_evidence(visible_damage_extent=DamageExtent.LOW)]
    result = run_severity(verdict, images, make_resolution())
    assert record_outcome(result, "SV-R08") is False
