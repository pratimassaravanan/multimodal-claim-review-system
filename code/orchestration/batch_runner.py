"""Batch runner for claims.csv → output.csv + decision traces."""

from __future__ import annotations

from pathlib import Path

from orchestration.emit import decision_to_output_row, write_decision_trace, write_output_csv
from orchestration.intake import (
    build_claim_context,
    load_claim_rows,
    load_requirement_ids,
    load_user_history,
    utc_now,
)
from orchestration.pipeline import process_claim
from providers.gemini.provider_registry import reset_provider_cache


def run_batch(
    *,
    repo_root: Path,
    claims_csv: Path | None = None,
    output_csv: Path | None = None,
    traces_dir: Path | None = None,
) -> Path:
    repo_root = repo_root.resolve()
    claims_csv = claims_csv or (repo_root / "dataset" / "claims.csv")
    output_csv = output_csv or (repo_root / "output.csv")
    traces_dir = traces_dir or (repo_root / "decision_traces")

    reset_provider_cache()
    user_history = load_user_history(repo_root)
    requirements = load_requirement_ids(repo_root)
    claim_rows = load_claim_rows(claims_csv)

    output_rows: list[dict[str, str]] = []
    for input_row in claim_rows:
        started_at = utc_now()
        claim = build_claim_context(
            input_row,
            repo_root=repo_root,
            user_history=user_history,
            requirements_by_object=requirements,
            observed_at=started_at,
        )
        artifacts = process_claim(claim, input_row, started_at=started_at)
        write_decision_trace(traces_dir, artifacts.trace)
        output_rows.append(
            decision_to_output_row(input_row, artifacts.decision, risk_flags=artifacts.risk.risk_flags)
        )

    write_output_csv(output_csv, output_rows)
    return output_csv
