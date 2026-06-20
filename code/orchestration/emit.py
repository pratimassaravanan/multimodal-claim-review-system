"""Write output.csv rows and DecisionTrace JSON files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from contracts.decision import ClaimDecision
from contracts.enums import RiskFlag
from contracts.trace import DecisionTrace
from ontology.normalize import format_risk_flags
from orchestration.intake import ClaimInputRow

OUTPUT_COLUMNS: tuple[str, ...] = (
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
    "evidence_standard_met",
    "evidence_standard_met_reason",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "claim_status_justification",
    "supporting_image_ids",
    "valid_image",
    "severity",
)


def decision_to_output_row(
    input_row: ClaimInputRow,
    decision: ClaimDecision,
    *,
    risk_flags: list[RiskFlag],
) -> dict[str, str]:
    return {
        "user_id": input_row.user_id,
        "image_paths": input_row.image_paths,
        "user_claim": input_row.user_claim,
        "claim_object": input_row.claim_object.value,
        "evidence_standard_met": str(decision.evidence_standard_met).lower(),
        "evidence_standard_met_reason": decision.evidence_standard_met_reason,
        "risk_flags": format_risk_flags(risk_flags),
        "issue_type": decision.issue_type.value,
        "object_part": decision.object_part.value,
        "claim_status": decision.claim_status.value,
        "claim_status_justification": decision.claim_status_justification,
        "supporting_image_ids": decision.supporting_image_ids_csv,
        "valid_image": str(decision.valid_image).lower(),
        "severity": decision.severity.value,
    }


def write_output_csv(output_path: Path, rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_COLUMNS), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def write_decision_trace(traces_dir: Path, trace: DecisionTrace) -> Path:
    traces_dir.mkdir(parents=True, exist_ok=True)
    safe_name = trace.row_id.replace(":", "_")
    path = traces_dir / f"{safe_name}.json"
    payload = trace.model_dump(mode="json")
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
