"""Entry point: dataset/claims.csv → output.csv + decision_traces/."""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from pathlib import Path

from orchestration.batch_runner import run_batch


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    output_path = run_batch(repo_root=repo_root)
    print(f"Wrote {output_path}")
    print(f"Wrote traces to {repo_root / 'decision_traces'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
