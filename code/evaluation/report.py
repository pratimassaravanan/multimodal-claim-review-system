"""Render evaluation/evaluation_report.md from run results."""

from __future__ import annotations

from pathlib import Path

from evaluation.metrics import CLAIM_STATUS_LABELS
from evaluation.runner import EvaluationRunResult


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _short_label(label: str) -> str:
    if label == "not_enough_information":
        return "not_enough_information"
    return label


def render_evaluation_report(result: EvaluationRunResult) -> str:
    metrics = result.metrics
    mismatches = [row for row in result.rows if not row.claim_status_match]

    lines: list[str] = [
        "# Evaluation Report",
        "",
        f"Dataset: `{result.dataset_path}`",
        f"Rows evaluated: {metrics.total_rows}",
        f"Provider mode: `{result.provider_mode}`",
        f"Evaluated at: {result.evaluated_at.isoformat()}",
        "",
        "## Summary Metrics (claim_status)",
        "",
        f"| Metric | Value |",
        f"| --- | --- |",
        f"| Accuracy | {_pct(metrics.accuracy)} |",
        f"| Macro-F1 | {_pct(metrics.macro_f1)} |",
        f"| False Support Rate | {_pct(metrics.false_support_rate)} |",
        "",
        "## Precision / Recall / F1",
        "",
        "| Class | Precision | Recall | F1 |",
        "| --- | --- | --- | --- |",
    ]

    for label in CLAIM_STATUS_LABELS:
        lines.append(
            f"| {_short_label(label)} | "
            f"{_pct(metrics.precision[label])} | "
            f"{_pct(metrics.recall[label])} | "
            f"{_pct(metrics.f1[label])} |"
        )

    lines.extend(
        [
            "",
            "## Confusion Matrix",
            "",
            "Rows = expected (gold), columns = predicted.",
            "",
        ]
    )

    header = ["expected \\ predicted", *[_short_label(label) for label in CLAIM_STATUS_LABELS]]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row_idx, gold_label in enumerate(CLAIM_STATUS_LABELS):
        counts = metrics.confusion_matrix[row_idx]
        cells = [str(count) for count in counts]
        lines.append(f"| {_short_label(gold_label)} | " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "## False Support Rate",
            "",
            "Definition: `FP_supported / (FP_supported + TN_supported)` where gold `claim_status` ≠ supported.",
            "",
            f"- False supports (predicted supported, gold ≠ supported): {metrics.false_support_fp}",
            f"- Denominator (gold ≠ supported): {metrics.false_support_denominator}",
            f"- Rate: {_pct(metrics.false_support_rate)}",
            "",
            "## Row-Level claim_status Mismatches",
            "",
        ]
    )

    if not mismatches:
        lines.append("None — all rows matched expected `claim_status`.")
    else:
        lines.append("| row_id | expected | predicted |")
        lines.append("| --- | --- | --- |")
        for row in mismatches:
            lines.append(
                f"| `{row.row_id}` | `{row.expected['claim_status']}` | `{row.predicted['claim_status']}` |"
            )

    lines.append("")
    return "\n".join(lines)


def write_evaluation_report(report_path: Path, result: EvaluationRunResult) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_evaluation_report(result), encoding="utf-8")
    return report_path
