"""Orchestration pipeline tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from contracts.enums import ClaimObject, ClaimStatus
from orchestration.batch_runner import run_batch
from orchestration.emit import OUTPUT_COLUMNS
from orchestration.intake import (
    ClaimInputRow,
    build_claim_context,
    load_requirement_ids,
    load_user_history,
    utc_now,
)
from orchestration.pipeline import process_claim
from providers.exceptions import ProviderError
from providers.gemini import provider_registry as provider_registry_module


@pytest.fixture(autouse=True)
def clear_provider_cache(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    provider_registry_module.reset_provider_cache()
    yield
    provider_registry_module.reset_provider_cache()


def test_process_claim_produces_decision_and_trace(repo_root: Path | None = None):
    repo_root = repo_root or Path(__file__).resolve().parents[2].parent
    input_row = ClaimInputRow(
        user_id="user_005",
        image_paths="images/test/case_003/img_1.jpg",
        user_claim="Customer: Need to file a car damage claim. Door dent.",
        claim_object=ClaimObject.CAR,
    )
    started_at = utc_now()
    claim = build_claim_context(
        input_row,
        repo_root=repo_root,
        user_history=load_user_history(repo_root),
        requirements_by_object=load_requirement_ids(repo_root),
        observed_at=started_at,
    )
    artifacts = process_claim(claim, input_row, started_at=started_at)
    assert artifacts.decision.row_id == claim.row_id
    assert artifacts.trace.row_id == claim.row_id
    assert artifacts.trace.verdict.claim_status in ClaimStatus
    assert len(artifacts.trace.rule_hits_ordered) >= 3


def test_run_batch_writes_output_and_traces(tmp_path):
    repo_root = Path(__file__).resolve().parents[2].parent
    output_csv = tmp_path / "output.csv"
    traces_dir = tmp_path / "decision_traces"
    result_path = run_batch(
        repo_root=repo_root,
        output_csv=output_csv,
        traces_dir=traces_dir,
    )
    assert result_path == output_csv
    assert output_csv.exists()
    with output_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(OUTPUT_COLUMNS)
        rows = list(reader)
    assert len(rows) == 44
    trace_files = list(traces_dir.glob("*.json"))
    assert len(trace_files) == 44
    sample = json.loads(trace_files[0].read_text(encoding="utf-8"))
    assert "row_id" in sample
    assert "decision" in sample


def test_provider_failure_forces_nei(monkeypatch, tmp_path):
    repo_root = Path(__file__).resolve().parents[2].parent

    class _BrokenFlash:
        def observe_claim(self, claim, *, observed_at):
            raise ProviderError("flash down")

    monkeypatch.setattr(provider_registry_module, "get_claim_observer", lambda: _BrokenFlash())
    provider_registry_module.reset_provider_cache()

    input_row = ClaimInputRow(
        user_id="user_005",
        image_paths="images/test/case_003/img_1.jpg",
        user_claim="Customer: Need to file a car damage claim. Door dent.",
        claim_object=ClaimObject.CAR,
    )
    started_at = utc_now()
    claim = build_claim_context(
        input_row,
        repo_root=repo_root,
        user_history=load_user_history(repo_root),
        requirements_by_object=load_requirement_ids(repo_root),
        observed_at=started_at,
    )
    artifacts = process_claim(claim, input_row, started_at=started_at)
    assert artifacts.decision.claim_status is ClaimStatus.NOT_ENOUGH_INFORMATION
    assert any(hit.rule_id == "PROVIDER-FAILURE" for hit in artifacts.trace.rule_hits_ordered)
