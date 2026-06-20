"""Evaluate pipeline outputs against dataset/sample_claims.csv gold labels."""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from pathlib import Path

from evaluation.report import write_evaluation_report
from evaluation.runner import run_sample_evaluation


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    report_path = Path(__file__).resolve().parent / "evaluation_report.md"

    result = run_sample_evaluation(repo_root)
    write_evaluation_report(report_path, result)

    metrics = result.metrics
    print(f"Wrote {report_path}")
    print(f"Accuracy: {metrics.accuracy:.4f}")
    print(f"Macro-F1: {metrics.macro_f1:.4f}")
    print(f"False Support Rate: {metrics.false_support_rate:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
