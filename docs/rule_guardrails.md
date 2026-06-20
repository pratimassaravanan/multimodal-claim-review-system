# Rule Layer Guardrails

**Status:** Mandatory for all `code/rules/` modules  
**Authority:** [decision_matrix.md](decision_matrix.md), [ds/hidden_business_rules.md](ds/hidden_business_rules.md), [pydantic_contracts_v2.md](pydantic_contracts_v2.md)

These guardrails apply to every rule module. Violations block merge.

---

## 1. Rule Purity

`resolve_claim.py`, `sufficiency.py`, and `trust.py` **must not** determine:

| Forbidden output | Belongs in |
|------------------|------------|
| `claim_status` | `verdict.py` (P3) |
| `severity` | `severity.py` (P3) |
| `supporting_image_ids` | `supporting_images.py` (P3) |
| `risk_flags` | `risk.py` (P3) |

They may only produce their stage contracts: `ClaimResolutionContext`, `ValidationContext`, `TrustAssessmentContext`.

---

## 2. Contract Boundary

| Direction | Requirement |
|-----------|-------------|
| **Inputs** | Only typed Pydantic contracts (`ClaimContext`, `ClaimObservation`, `ImageEvidence`, etc.) |
| **Outputs** | Only typed contracts or typed stage bundles (`*StageResult` in `rules/types.py`) |
| **Forbidden** | Raw `dict`, `tuple`, or untyped returns from public rule functions |

Internal helpers may use ephemeral structures; public APIs must not.

---

## 3. Rule Coverage

Every **Rule ID** implemented must have:

- one **positive** test (condition matches / rule fires)
- one **negative** test (condition does not match / rule skipped)

Rule IDs are defined in `decision_matrix.md` (e.g. `MP-1`, `ESM-R01`, `VI-R04`, `PRED-PART-CLEAR`).

---

## 4. Hidden Rule Protection

Do **not** invent business rules.

Every rule must map to:

- [decision_matrix.md](decision_matrix.md), or
- [ds/hidden_business_rules.md](ds/hidden_business_rules.md)

If behavior is unclear:

```python
raise NotImplementedError("TODO: <rule_id> — cite missing matrix spec")
```

Do not guess or infer undocumented behavior.

---

## 5. Determinism

Given identical typed inputs and the same `evaluated_at` timestamp passed by the caller:

- outputs must be **byte-identical** (model `model_dump()` equality)
- no `random`, `uuid`, or `datetime.now()` inside rule functions
- no environment-variable branching inside rule logic

Timestamps belong in contracts (`evaluated_at`, `resolved_at`) and are supplied by orchestration.

---

## 6. Traceability

Every rule evaluation emits a `RuleExecutionRecord` (`rules/types.py`) containing:

| Field | Maps to `RuleHit` |
|-------|-------------------|
| `rule_id` | `rule_id` |
| `outcome` | `matched` |
| `justification` | `outputs_snapshot["justification"]` |
| `trace_fields` | remaining `outputs_snapshot` entries |

`rules/rule_trace.py` converts records to `RuleHit` without recomputation.

Stage bundles (`ResolveClaimStageResult`, `SufficiencyStageResult`, etc.) carry both the contract and `rule_records` for trace assembly.

---

## 7. Success Criteria Checklist

Before closing a rule phase:

- [ ] All tests pass
- [ ] No verdict logic in P2 modules
- [ ] No severity logic in P2 modules
- [ ] No risk logic in P2 modules
- [ ] No Gemini / provider imports in `rules/`
- [ ] All public rule outputs are typed contracts or stage bundles
- [ ] Every implemented Rule ID has positive + negative tests
- [ ] `RuleExecutionRecord` emitted for each matrix rule evaluation
- [ ] `records_to_rule_hits()` can assemble `DecisionTrace.rule_hits_ordered` without re-running rules

---

## 8. Module Scope Reference

| Module | Rule IDs | Output contract |
|--------|----------|-----------------|
| `predicates.py` | `PRED-*` (§0.5) | `PredicatesEvaluationBundle` |
| `requirements_map.py` | `REQ_*` satisfaction (§1.2) | `RequirementEvaluationResult` |
| `resolve_claim.py` | `MP-1`..`MP-5` (§7) | `ResolveClaimStageResult` |
| `consistency.py` | Derived §0.5 (no separate matrix table) | `ConsistencyStageResult` |
| `sufficiency.py` | `ESM-R01`..`ESM-R08` (§1) | `SufficiencyStageResult` |
| `trust.py` | `VI-R01`..`VI-R04` (§2) | `TrustStageResult` |
