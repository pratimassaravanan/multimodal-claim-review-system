"""RuleHit trace assembly for verdict stage."""

from __future__ import annotations

from contracts.enums import RuleHitStage
from rules.rule_trace import records_to_rule_hits
from rules.types import VerdictStageResult
from tests.conftest import make_claim_context, make_claim_observation, make_image_evidence, make_resolution
from tests.rules.verdict_helpers import run_verdict


def test_verdict_records_to_rule_hits():
    claim = make_claim_context()
    observation = make_claim_observation()
    images = [make_image_evidence(part_visible=True, part_confidence="high")]
    result = run_verdict(
        claim=claim,
        observation=observation,
        images=images,
        resolution=make_resolution(),
    )
    hits = records_to_rule_hits(result.rule_records, stage=RuleHitStage.VERDICT, start_sequence=10)
    assert hits[0].stage is RuleHitStage.VERDICT
    assert hits[0].sequence == 10
    assert "justification" in hits[0].outputs_snapshot
