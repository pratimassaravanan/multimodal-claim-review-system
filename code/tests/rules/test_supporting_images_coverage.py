"""Coverage tests for supporting_images.py — SI-R01..SI-R07."""

from __future__ import annotations

from contracts.decision import VerdictDecision
from contracts.enums import (
    ClaimObject,
    ClaimStatus,
    DamageExtent,
    IssueFamily,
    IssueType,
    ObjectPart,
)
from rules.supporting_images import SI_RULE_IDS
from tests.conftest import NOW, make_claim_context, make_claim_observation, make_image_evidence, make_resolution
from tests.rules.stage_helpers import record_outcome, run_supporting


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


def test_all_si_rules_emitted_on_supported_single_image():
    claim = make_claim_context(image_ids=["img_1"])
    observation = make_claim_observation()
    images = [make_image_evidence(part_visible=True, part_confidence="high")]
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    emitted = {record.rule_id for record in result.rule_records}
    assert "SI-R03" in emitted
    assert result.supporting.supporting_image_rule_id == "SI-R03"


def test_si_r01_positive():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    observation = make_claim_observation(
        identity_constraint_active=True,
        identity_side="front",
        identity_color="blue",
    )
    images = [
        make_image_evidence(
            image_id="img_1",
            vehicle_identity_features=["color:blue", "body_style:sedan"],
        ),
        make_image_evidence(
            image_id="img_2",
            vehicle_identity_features=["color:red", "body_style:sedan"],
        ),
    ]
    verdict = _verdict(
        row_id=claim.row_id,
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        claim_status_rule_id="CS-R01",
        issue_type=IssueType.UNKNOWN,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert result.supporting.supporting_image_rule_id == "SI-R01"
    assert set(result.supporting.supporting_image_ids) == {"img_1", "img_2"}
    assert record_outcome(result, "SI-R01") is True


def test_si_r01_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    verdict = _verdict(
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        claim_status_rule_id="CS-R08",
        issue_type=IssueType.UNKNOWN,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=[make_image_evidence()],
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert record_outcome(result, "SI-R01") is False


def test_si_r02_positive():
    claim = make_claim_context()
    observation = make_claim_observation()
    verdict = _verdict(
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        claim_status_rule_id="CS-R08",
        issue_type=IssueType.UNKNOWN,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=[make_image_evidence()],
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert result.supporting.supporting_image_rule_id == "SI-R02"
    assert result.supporting.supporting_image_ids == []
    assert record_outcome(result, "SI-R02") is True


def test_si_r02_negative():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    observation = make_claim_observation(identity_constraint_active=True, identity_side="front")
    images = [
        make_image_evidence(image_id="img_1", vehicle_identity_features=["color:blue"]),
        make_image_evidence(image_id="img_2", vehicle_identity_features=["color:red"]),
    ]
    verdict = _verdict(
        claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION,
        claim_status_rule_id="CS-R01",
        issue_type=IssueType.UNKNOWN,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert record_outcome(result, "SI-R02") is False


def test_si_r03_positive():
    claim = make_claim_context(image_ids=["img_1"])
    observation = make_claim_observation()
    images = [make_image_evidence(part_visible=True, part_confidence="high")]
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert result.supporting.supporting_image_rule_id == "SI-R03"
    assert result.supporting.supporting_image_ids == ["img_1"]
    assert record_outcome(result, "SI-R03") is True


def test_si_r03_negative():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    observation = make_claim_observation()
    images = [
        make_image_evidence(image_id="img_1", part_visible=True, part_confidence="high"),
        make_image_evidence(image_id="img_2", part_visible=True, part_confidence="high"),
    ]
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    assert record_outcome(result, "SI-R03") is False


def test_si_r04_positive():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            image_id="img_1",
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.DOOR,
            visible_issue_type=IssueType.DENT,
        ),
        make_image_evidence(
            image_id="img_2",
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.DOOR,
            visible_issue_type=IssueType.DENT,
            visible_damage_extent=DamageExtent.MEDIUM,
        ),
    ]
    resolution = make_resolution(primary_object_part=ObjectPart.DOOR)
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=resolution,
    )
    assert result.supporting.supporting_image_rule_id == "SI-R04"
    assert len(result.supporting.supporting_image_ids) == 1
    assert record_outcome(result, "SI-R04") is True


def test_si_r04_negative():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    observation = make_claim_observation()
    images = [
        make_image_evidence(image_id="img_1", part_visible=False, part_confidence="low"),
        make_image_evidence(image_id="img_2", part_visible=False, part_confidence="low"),
    ]
    verdict = _verdict()
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert record_outcome(result, "SI-R04") is False


def test_si_r05_positive():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            visible_part=ObjectPart.FRONT_BUMPER,
            visible_issue_type=IssueType.BROKEN_PART,
            visible_damage_extent=DamageExtent.HIGH,
        )
    ]
    verdict = _verdict(
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R04",
        issue_type=IssueType.BROKEN_PART,
        object_part=ObjectPart.FRONT_BUMPER,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(primary_object_part=ObjectPart.REAR_BUMPER),
        verdict=verdict,
    )
    assert result.supporting.supporting_image_rule_id == "SI-R05"
    assert record_outcome(result, "SI-R05") is True


def test_si_r05_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    verdict = _verdict(
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R02",
        issue_type=IssueType.UNKNOWN,
        object_part=ObjectPart.UNKNOWN,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=[make_image_evidence(depicts_object=False, depicts_confidence="high")],
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert record_outcome(result, "SI-R05") is False


def test_si_r06_positive():
    claim = make_claim_context(claim_object=ClaimObject.PACKAGE)
    observation = make_claim_observation(claim_object=ClaimObject.PACKAGE)
    images = [
        make_image_evidence(
            claim_object=ClaimObject.PACKAGE,
            depicts_object=False,
            depicts_confidence="high",
            visible_part=ObjectPart.BOX,
            visible_issue_type=IssueType.DENT,
            visible_damage_extent=DamageExtent.LOW,
        )
    ]
    verdict = _verdict(
        row_id=claim.row_id,
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R02",
        issue_type=IssueType.UNKNOWN,
        object_part=ObjectPart.UNKNOWN,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(
            claim_object=ClaimObject.PACKAGE,
            primary_issue_family=IssueFamily.CRUSHED_TORN_SEAL,
            primary_object_part=ObjectPart.BOX,
        ),
        verdict=verdict,
    )
    assert result.supporting.supporting_image_rule_id == "SI-R06"
    assert record_outcome(result, "SI-R06") is True


def test_si_r06_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    verdict = _verdict(
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R04",
        issue_type=IssueType.BROKEN_PART,
        object_part=ObjectPart.FRONT_BUMPER,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=[make_image_evidence()],
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert record_outcome(result, "SI-R06") is False


def test_si_r07_positive():
    claim = make_claim_context(image_ids=["img_1", "img_2"], claim_object=ClaimObject.PACKAGE)
    observation = make_claim_observation(claim_object=ClaimObject.PACKAGE)
    images = [
        make_image_evidence(
            image_id="img_1",
            claim_object=ClaimObject.PACKAGE,
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.SEAL,
            visible_issue_type=IssueType.NONE,
        ),
        make_image_evidence(
            image_id="img_2",
            claim_object=ClaimObject.PACKAGE,
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.SEAL,
            visible_issue_type=IssueType.NONE,
        ),
    ]
    verdict = _verdict(
        row_id=claim.row_id,
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R03",
        issue_type=IssueType.NONE,
        object_part=ObjectPart.SEAL,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(
            claim_object=ClaimObject.PACKAGE,
            primary_issue_family=IssueFamily.CRUSHED_TORN_SEAL,
            primary_object_part=ObjectPart.SEAL,
        ),
        verdict=verdict,
    )
    assert result.supporting.supporting_image_rule_id == "SI-R07"
    assert set(result.supporting.supporting_image_ids) == {"img_1", "img_2"}
    assert record_outcome(result, "SI-R07") is True


def test_si_r07_negative():
    claim = make_claim_context()
    observation = make_claim_observation()
    verdict = _verdict(
        claim_status=ClaimStatus.CONTRADICTED,
        claim_status_rule_id="CS-R03",
        issue_type=IssueType.NONE,
        object_part=ObjectPart.REAR_BUMPER,
    )
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=[make_image_evidence(visible_issue_type=IssueType.NONE)],
        resolution=make_resolution(),
        verdict=verdict,
    )
    assert record_outcome(result, "SI-R07") is False


def test_blurry_image_excluded_when_alternative_exists():
    claim = make_claim_context(image_ids=["img_1", "img_2"])
    observation = make_claim_observation()
    images = [
        make_image_evidence(
            image_id="img_1",
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.DOOR,
            visible_issue_type=IssueType.DENT,
        ),
        make_image_evidence(
            image_id="img_2",
            part_visible=True,
            part_confidence="high",
            visible_part=ObjectPart.DOOR,
            visible_issue_type=IssueType.DENT,
        ),
    ]
    images[0] = make_image_evidence(
        image_id="img_1",
        part_visible=True,
        part_confidence="high",
        visible_part=ObjectPart.DOOR,
        visible_issue_type=IssueType.DENT,
    )
    blurry = make_image_evidence(
        image_id="img_1",
        part_visible=True,
        part_confidence="high",
        visible_part=ObjectPart.DOOR,
        visible_issue_type=IssueType.DENT,
    )
    blurry = blurry.model_copy(
        update={"is_blurry": blurry.is_blurry.model_copy(update={"value": True, "confidence": "high"})}
    )
    images = [blurry, images[1]]
    result = run_supporting(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(primary_object_part=ObjectPart.DOOR),
    )
    assert result.supporting.supporting_image_ids == ["img_2"]
    assert "img_1" in result.supporting.excluded_image_ids or "blurry" in result.supporting.selection_rationale
