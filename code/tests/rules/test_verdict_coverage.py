"""Coverage tests for verdict.py — CS-R01..CS-R08."""

from __future__ import annotations

from contracts.enums import (
    ClaimObject,
    ClaimStatus,
    ClaimedSeverityLanguage,
    DamageExtent,
    IssueType,
    ObjectPart,
)
from rules.verdict import CS_RULE_IDS
from tests.conftest import NOW, make_claim_context, make_claim_observation, make_image_evidence, make_resolution
from tests.rules.verdict_helpers import record_outcome, run_verdict


def test_all_cs_rules_emitted_on_supported_path():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence(part_visible=True, part_confidence="high")]
    resolution = make_resolution()
    result = run_verdict(claim=claim, observation=observation, images=images, resolution=resolution)
    emitted = {record.rule_id for record in result.rule_records}
    assert "CS-R01" in emitted
    assert result.verdict.claim_status is ClaimStatus.SUPPORTED


def test_cs_r01_positive():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence(file_readable=False)]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert result.verdict.claim_status_rule_id == "CS-R01"
    assert result.verdict.claim_status is ClaimStatus.NOT_ENOUGH_INFORMATION
    assert record_outcome(result, "CS-R01") is True


def test_cs_r01_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence(part_visible=True, part_confidence="high")]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "CS-R01") is False


def test_cs_r02_positive():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            depicts_object=False,
            depicts_confidence="high",
            visible_damage_extent=DamageExtent.MEDIUM,
            extent_confidence="medium",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert result.verdict.claim_status_rule_id == "CS-R02"
    assert record_outcome(result, "CS-R02") is True


def test_cs_r02_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            depicts_object=False,
            depicts_confidence="high",
            visible_damage_extent=DamageExtent.NONE,
            extent_confidence="medium",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "CS-R02") is False


def test_cs_r03_positive():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_issue_type=IssueType.NONE,
            issue_confidence="high",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert result.verdict.claim_status_rule_id == "CS-R03"
    assert record_outcome(result, "CS-R03") is True


def test_cs_r03_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence(part_visible=True, part_confidence="high", visible_issue_type=IssueType.DENT)]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "CS-R03") is False


def test_cs_r04_positive():
    claim = make_claim_context()
    observation = make_claim_observation(alleged_parts=[ObjectPart.REAR_BUMPER])
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.DOOR,
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(primary_object_part=ObjectPart.REAR_BUMPER),
    )
    assert result.verdict.claim_status_rule_id == "CS-R04"
    assert record_outcome(result, "CS-R04") is True


def test_cs_r04_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.REAR_BUMPER,
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "CS-R04") is False


def test_cs_r05_positive():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.REAR_BUMPER,
            visible_issue_type=IssueType.STAIN,
            issue_confidence="high",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert result.verdict.claim_status_rule_id == "CS-R05"
    assert record_outcome(result, "CS-R05") is True


def test_cs_r05_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.REAR_BUMPER,
            visible_issue_type=IssueType.DENT,
            issue_confidence="high",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "CS-R05") is False


def test_cs_r06_positive():
    claim = make_claim_context()
    observation = make_claim_observation(claimed_severity_language=ClaimedSeverityLanguage.HIGH)
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.REAR_BUMPER,
            visible_issue_type=IssueType.SCRATCH,
            issue_confidence="high",
            visible_damage_extent=DamageExtent.LOW,
            extent_confidence="medium",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert result.verdict.claim_status_rule_id == "CS-R06"
    assert record_outcome(result, "CS-R06") is True


def test_cs_r06_negative():
    claim = make_claim_context()
    observation = make_claim_observation(claimed_severity_language=ClaimedSeverityLanguage.MEDIUM)
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_damage_extent=DamageExtent.LOW,
            extent_confidence="medium",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "CS-R06") is False


def test_cs_r07_positive():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.REAR_BUMPER,
            visible_issue_type=IssueType.DENT,
            issue_confidence="high",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert result.verdict.claim_status_rule_id == "CS-R07"
    assert result.verdict.claim_status is ClaimStatus.SUPPORTED
    assert record_outcome(result, "CS-R07") is True


def test_cs_r07_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.REAR_BUMPER,
            visible_issue_type=IssueType.DENT,
            issue_confidence="low",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "CS-R07") is False


def test_cs_r08_positive():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.REAR_BUMPER,
            visible_issue_type=IssueType.DENT,
            issue_confidence="low",
        )
    ]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert result.verdict.claim_status_rule_id == "CS-R08"
    assert result.verdict.claim_status is ClaimStatus.NOT_ENOUGH_INFORMATION
    assert record_outcome(result, "CS-R08") is True


def test_cs_r08_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence(part_visible=True, part_confidence="high")]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "CS-R08") is None


def test_verdict_rule_ids_complete():
    assert len(CS_RULE_IDS) == 8


def test_verdict_records_have_justification():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence(part_visible=True, part_confidence="high")]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    for record in result.rule_records:
        assert record.justification
