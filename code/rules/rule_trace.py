"""Convert typed rule records into DecisionTrace RuleHit entries."""

from __future__ import annotations

from contracts.enums import RuleHitStage
from contracts.trace import RuleHit
from rules.types import PredicateTraceRecord, RuleExecutionRecord, TraceField


def trace_fields_to_snapshot(fields: list[TraceField]) -> dict[str, str]:
    return {field.key: field.value for field in fields}


def rule_record_to_hit(
    record: RuleExecutionRecord,
    *,
    sequence: int,
    stage: RuleHitStage,
    input_fields: list[TraceField] | None = None,
) -> RuleHit:
    outputs = trace_fields_to_snapshot(record.trace_fields)
    outputs["justification"] = record.justification
    return RuleHit(
        sequence=sequence,
        stage=stage,
        rule_id=record.rule_id,
        matched=record.outcome,
        inputs_snapshot=trace_fields_to_snapshot(input_fields or []),
        outputs_snapshot=outputs,
    )


def predicate_record_to_hit(
    record: PredicateTraceRecord,
    *,
    sequence: int,
    stage: RuleHitStage = RuleHitStage.VALIDATION,
) -> RuleHit:
    outputs = trace_fields_to_snapshot(record.trace_fields)
    outputs["justification"] = record.justification
    outputs["value_text"] = record.value_text
    return RuleHit(
        sequence=sequence,
        stage=stage,
        rule_id=record.predicate_id,
        matched=record.outcome,
        inputs_snapshot={},
        outputs_snapshot=outputs,
    )


def records_to_rule_hits(
    records: list[RuleExecutionRecord],
    *,
    stage: RuleHitStage,
    start_sequence: int = 1,
    input_fields: list[TraceField] | None = None,
) -> list[RuleHit]:
    """Assemble ordered RuleHit list without re-running rule logic."""
    hits: list[RuleHit] = []
    for index, record in enumerate(records):
        hits.append(
            rule_record_to_hit(
                record,
                sequence=start_sequence + index,
                stage=stage,
                input_fields=input_fields,
            )
        )
    return hits
