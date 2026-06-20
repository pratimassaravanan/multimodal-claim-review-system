"""Tests for rules.rule_trace."""

from __future__ import annotations

from contracts.enums import RuleHitStage
from rules.rule_trace import records_to_rule_hits, rule_record_to_hit
from rules.types import RuleExecutionRecord, TraceField


def test_rule_record_to_hit_includes_justification():
    record = RuleExecutionRecord(
        rule_id="ESM-R03",
        outcome=True,
        justification="Claimed part not visible.",
        trace_fields=[TraceField(key="no_part_visible", value="true")],
    )
    hit = rule_record_to_hit(record, sequence=1, stage=RuleHitStage.VALIDATION)
    assert hit.rule_id == "ESM-R03"
    assert hit.matched is True
    assert hit.outputs_snapshot["justification"] == "Claimed part not visible."


def test_records_to_rule_hits_preserves_order():
    records = [
        RuleExecutionRecord(rule_id="ESM-R01", outcome=False, justification="No unreadable files."),
        RuleExecutionRecord(rule_id="ESM-R08", outcome=True, justification="Default met."),
    ]
    hits = records_to_rule_hits(records, stage=RuleHitStage.VALIDATION, start_sequence=3)
    assert [hit.sequence for hit in hits] == [3, 4]
    assert hits[0].rule_id == "ESM-R01"
