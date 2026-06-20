"""Architecture guardrail enforcement for P2 rule modules."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

P2_MODULES = [
    "resolve_claim.py",
    "sufficiency.py",
    "trust.py",
]

FORBIDDEN_SYMBOLS = {
    "claim_status",
    "ClaimStatus",
    "VerdictDecision",
    "SeverityDecision",
    "SupportingImageDecision",
    "supporting_image_ids",
    "risk_flags",
    "RiskContext",
    "RiskFlag",
}


@pytest.mark.parametrize("module_name", P2_MODULES)
def test_p2_modules_avoid_verdict_severity_risk_symbols(module_name: str):
    path = Path(__file__).resolve().parents[2] / "rules" / module_name
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    violations = names & FORBIDDEN_SYMBOLS
    assert not violations, f"{module_name} references forbidden symbols: {violations}"


def test_rule_execution_record_has_required_trace_fields():
    from rules.types import RuleExecutionRecord

    record = RuleExecutionRecord(
        rule_id="ESM-R08",
        outcome=True,
        justification="Default sufficiency met.",
    )
    assert record.rule_id == "ESM-R08"
    assert record.outcome is True
    assert record.justification
