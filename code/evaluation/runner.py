"""Run the existing pipeline on sample_claims.csv and compare to gold labels."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from contracts.enums import DatasetSplit
from evaluation.loader import LABEL_COLUMNS, SampleClaimRow, load_sample_claims
from evaluation.metrics import ClaimStatusMetrics, compute_claim_status_metrics
from orchestration.emit import decision_to_output_row
from orchestration.intake import (
    build_claim_context,
    load_requirement_ids,
    load_user_history,
    utc_now,
)
from orchestration.pipeline import process_claim
from providers.gemini.provider_registry import reset_provider_cache


@dataclass(frozen=True)
class RowComparison:
    row_id: str
    expected: dict[str, str]
    predicted: dict[str, str]
    claim_status_match: bool


@dataclass(frozen=True)
class EvaluationRunResult:
    dataset_path: Path
    evaluated_at: datetime
    provider_mode: str
    rows: tuple[RowComparison, ...]
    metrics: ClaimStatusMetrics


def _predicted_labels(
    sample_row: SampleClaimRow,
    *,
    repo_root: Path,
    user_history,
    requirements,
    observed_at,
) -> dict[str, str]:
    claim = build_claim_context(
        sample_row.input_row,
        repo_root=repo_root,
        user_history=user_history,
        requirements_by_object=requirements,
        observed_at=observed_at,
        dataset_split=DatasetSplit.SAMPLE,
    )
    artifacts = process_claim(claim, sample_row.input_row, started_at=observed_at)
    output_row = decision_to_output_row(
        sample_row.input_row,
        artifacts.decision,
        risk_flags=artifacts.risk.risk_flags,
    )
    return {column: output_row[column] for column in LABEL_COLUMNS}


def run_sample_evaluation(
    repo_root: Path,
    *,
    sample_csv: Path | None = None,
) -> EvaluationRunResult:
    repo_root = repo_root.resolve()
    sample_csv = sample_csv or (repo_root / "dataset" / "sample_claims.csv")

    reset_provider_cache()
    import os

    provider_mode = "gemini" if os.environ.get("GOOGLE_API_KEY") else "mock"

    user_history = load_user_history(repo_root)
    requirements = load_requirement_ids(repo_root)
    sample_rows = load_sample_claims(sample_csv)

    comparisons: list[RowComparison] = []
    for sample_row in sample_rows:
        observed_at = utc_now()
        predicted = _predicted_labels(
            sample_row,
            repo_root=repo_root,
            user_history=user_history,
            requirements=requirements,
            observed_at=observed_at,
        )
        comparisons.append(
            RowComparison(
                row_id=sample_row.row_id,
                expected=sample_row.expected,
                predicted=predicted,
                claim_status_match=predicted["claim_status"] == sample_row.expected["claim_status"],
            )
        )

    metrics = compute_claim_status_metrics(
        expected=[row.expected["claim_status"] for row in comparisons],
        predicted=[row.predicted["claim_status"] for row in comparisons],
    )

    return EvaluationRunResult(
        dataset_path=sample_csv,
        evaluated_at=datetime.now(timezone.utc),
        provider_mode=provider_mode,
        rows=tuple(comparisons),
        metrics=metrics,
    )
