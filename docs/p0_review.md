# P0 Review — Contracts & Ontology Layer

**Date:** 2026-06-19  
**Reviewers:** Principal Software Engineer · Staff ML Platform Engineer  
**Scope:** `code/contracts/`, `code/ontology/`, `code/tests/` (P0 deliverable)  
**References:** [pydantic_contracts_v2.md](pydantic_contracts_v2.md), [project_structure.md](project_structure.md), [decision_matrix.md](decision_matrix.md), [implementation_readiness_review.md](implementation_readiness_review.md)

---

## Verdict

## **P0_APPROVED**

P0 is complete and compliant for progression to **P1A** (`rules/predicates.py`, `rules/requirements_map.py`). Minor gaps are documented below as non-blocking recommendations.

---

## 1. Architecture Compliance

| Check | Status | Evidence |
|-------|--------|----------|
| All 16 v2 contracts implemented | **PASS** | `ClaimContext` through `EvaluationRecord` in `code/contracts/` |
| `ClaimObservation` first-class | **PASS** | `observation.py` — no verdict fields |
| Three decision outputs split | **PASS** | `VerdictDecision`, `SeverityDecision`, `SupportingImageDecision` in `decision.py` |
| `ClaimDecision` composition-only | **PASS** | Composes sub-decisions; HR checks at compose |
| `ImageEvidence.observation_pass` | **PASS** | `Literal[1, 2]` on model |
| `DecisionTrace` v2 stages | **PASS** | `RuleHitStage` includes `verdict`, `severity`, `supporting`; no `decide` |
| `CONTRACTS_VERSION = "2.0"` | **PASS** | `enums.py`, `trace.py` |
| No Gemini / providers in P0 | **PASS** | No `providers/` directory |
| No rules / orchestration in P0 | **PASS** | No `rules/`, `modules/`, `main.py` yet |
| AGENTS.md layout | **PASS** | `code/pyproject.toml`, `code/README.md`, package installable |

**Minor note:** `contracts/resolution.py` and `contracts/observation.py` import `ontology` for part validation. This is acceptable — ontology is a foundation layer below rules; contracts use it only for enum validation, not business verdict logic.

---

## 2. Dependency Compliance

Hard rules from [project_structure.md](project_structure.md) §10:

| Rule | Status |
|------|--------|
| `contracts/` must not import `modules/`, `rules/`, `providers/` | **PASS** |
| `ontology/` must not import `providers/` | **PASS** |
| `ontology/` must not import `rules/` | **PASS** |
| No circular imports observed | **PASS** |

**Dependency graph (actual):**

```text
ontology → contracts.enums
contracts → ontology (validation helpers only)
tests → contracts, ontology
```

No violations. P1 `rules/` may import `contracts` + `ontology` per design.

---

## 3. Validation-Only Contracts

| Check | Status | Notes |
|-------|--------|-------|
| Pydantic models are typed boundaries | **PASS** | No raw dict handoffs |
| Cross-field HR validators on decision contracts | **PASS** | HR-01, HR-03, HR-04 in models |
| Optional hook fields (`claim_object`, `exclude=True`) | **PASS** | Enables validation without circular deps |
| No CSV / file I/O in contracts | **PASS** | `ClaimContext.validate_files_exist` optional flag only |
| No model API calls | **PASS** | |
| ESM/VI rule execution not in contracts | **PASS** | Only structural validation on `ValidationContext` / `TrustAssessmentContext` |

**Minor gap:** HR-02 (`contradicted ⟹ ESM=true`) validated on `VerdictDecision` but not covered by unit test. Non-blocking.

---

## 4. Ontology Purity

| Check | Status | Notes |
|-------|--------|-------|
| Closed enum sets per `problem_statement.md` | **PASS** | Car/laptop/package parts |
| Normalization → `unknown` fallback | **PASS** | `normalize.py` |
| Issue family mapping §0.3/§0.4 | **PASS** | `issue_families.py` with part-aware overrides |
| Risk flag parse/format | **PASS** | `none` sentinel enforced |
| No verdict / status logic | **PASS** | No `claim_status` in ontology |
| No Gemini references | **PASS** | |
| Requirement ID constants | **PASS** | Duplicated in ontology for mapping; P1A `requirements_map.py` will canonicalize from CSV |

---

## 5. Test Coverage Alignment

**Executed:** `pytest tests/ -v` → **67 passed**

| Planned suite (project_structure §5) | Status | Coverage |
|--------------------------------------|--------|----------|
| **T1** `tests/contracts/` | **Partial PASS** | Enums + 7 model tests; not all 16 contracts individually tested |
| **T2** `tests/ontology/` | **PASS** | Parts, issue types, risk flags, normalize |
| HR invariant tests | **Partial** | HR-01, HR-03, HR-04 tested; HR-02 untested |
| Full contract round-trip JSON | **Not started** | Deferred — acceptable for P0 |

**Gaps (non-blocking):**

- No dedicated tests for `DecisionTrace`, `EvidenceContext`, `EvaluationRecord` construction
- No `tests/contracts/test_validation.py` for every enum rejection on nested models
- T3+ suites not applicable until P1+

Coverage is **sufficient for P0 gate** per implementation_readiness_review §8.

---

## 6. Summary Scorecard

| Dimension | Result |
|-----------|--------|
| Architecture compliance | **PASS** |
| Dependency compliance | **PASS** |
| Validation-only contracts | **PASS** (minor test gap) |
| Ontology purity | **PASS** |
| Test coverage alignment | **PASS** (T1 partial) |

---

## 7. Recommendations (Post-P0, Non-Blocking)

1. Add `test_verdict_hr02` when touching decision tests next.
2. Add smoke tests for `DecisionTrace` minimum stage validation before P7.
3. Consolidate requirement metadata in `rules/requirements_map.py` (P1A) — reduce duplication with `ontology/issue_families.py` over time.

---

## 8. Authorization

**P0_APPROVED** — proceed to **P1A**: `code/rules/predicates.py`, `code/rules/requirements_map.py`.
