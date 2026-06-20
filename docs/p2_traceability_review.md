# P2 Traceability Review

**Date:** 2026-06-19  
**Scope:** `code/rules/` (P1A + P2) vs [decision_matrix.md](decision_matrix.md) and [rule_guardrails.md](rule_guardrails.md)  
**Reviewer:** Principal Software Engineer (automated audit)

---

## Verdict

## **P2_TRACEABILITY_GAPS_FOUND**

Implementation coverage for the P2 rule surface is complete (41 Rule IDs). Guardrail-required **positive + negative test pairs** are incomplete for 24 Rule IDs. One matrix rule (`ESM-R06`) is structurally unreachable as a positive trigger. No duplicate or unreferenced Rule IDs were found among implemented IDs.

---

## Review Method

1. Enumerate Rule IDs emitted or evaluated in `code/rules/`.
2. Map each ID to a `decision_matrix.md` section (or guardrails §8 mapping for `PRED-*`).
3. Cross-check `code/tests/rules/` for dedicated positive and negative assertions per ID.
4. Flag missing, untested, duplicate, dead, and unreferenced IDs.

**P2 in-scope Rule families:** `PRED-*` (§0.5), `REQ_*` (§0.3 / §1.2), `MP-1`..`MP-5` (§7), `ESM-R01`..`ESM-R08` (§1), `VI-R01`..`VI-R04` (§2).

**Out of scope (P3+):** `CS-R*`, `SV-R*`, `SI-R*`, `MRR-*`, `HR-*` — listed under Missing only as future work, not P2 gaps.

---

## 1. Predicate Rule IDs (`PRED-*` → decision_matrix §0.5)

Matrix names (`IMAGE_COUNT`, `PART_CLEAR`, …) map to implementation IDs via [rule_guardrails.md](rule_guardrails.md) §8.

| Rule ID | Matrix § | Implementation | Positive test | Negative test |
|---------|----------|----------------|---------------|---------------|
| `PRED-IMAGE-COUNT` | §0.5 | `predicates.py` → `compute_image_count` | `test_predicates.py::test_predicate_has_positive_and_negative_cases[PRED-IMAGE-COUNT]` | Same (outcome always `True`; value differs — **weak negative**) |
| `PRED-ANY-FILE-UNREADABLE` | §0.5 | `predicates.py` → `compute_any_file_unreadable` | Parametrized predicate test | Parametrized predicate test |
| `PRED-BEST-PART-CONFIDENCE` | §0.5 | `predicates.py` → `compute_best_part_confidence` | Parametrized predicate test | Same (outcome always `True` — **weak negative**) |
| `PRED-BEST-PART-IMAGE-SET` | §0.5 | `predicates.py` → `compute_best_part_image_set` | Parametrized predicate test | Parametrized predicate test |
| `PRED-PART-CLEAR` | §0.5 | `predicates.py` → `compute_part_clear` | Parametrized predicate test | Parametrized predicate test |
| `PRED-PART-VISIBLE-LOW-ONLY` | §0.5 | `predicates.py` → `compute_part_visible_low_only` | Parametrized predicate test | Parametrized predicate test |
| `PRED-NO-PART-VISIBLE` | §0.5 | `predicates.py` → `compute_no_part_visible` | Parametrized predicate test | Parametrized predicate test |
| `PRED-IDENTITY-CONFLICT` | §0.5 | `predicates.py` → `compute_identity_conflict`; shared logic in `identity_helpers.py` | Parametrized predicate test | Parametrized predicate test |
| `PRED-WRONG-OBJECT-SET` | §0.5 | `predicates.py` → `compute_wrong_object_set` | Parametrized predicate test | Parametrized predicate test |
| `PRED-ANY-NON-ORIGINAL-HIGH` | §0.5 | `predicates.py` → `compute_any_non_original_high` | Parametrized predicate test | Parametrized predicate test |
| `PRED-CONTENTS-CLAIM` | §0.5 | `predicates.py` → `compute_contents_claim` | Parametrized predicate test | Parametrized predicate test |
| `PRED-CONTENTS-AREA-CLEAR` | §0.5 | `predicates.py` → `compute_contents_area_clear` | Parametrized predicate test | Parametrized predicate test |
| `PRED-ALL-IMAGES-UNUSABLE` | §0.5 | `predicates.py` → `compute_all_images_unusable` | Parametrized predicate test | Parametrized predicate test |

**Aggregate:** `predicates.py::compute_all_predicates` → `test_predicates.py::test_compute_all_predicates_bundle`

---

## 2. Requirement Rule IDs (`REQ_*` → decision_matrix §0.3 / §1.2)

| Rule ID | Matrix § | Implementation | Positive test | Negative test |
|---------|----------|----------------|---------------|---------------|
| `REQ_GENERAL_OBJECT_PART` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | `test_requirements_map.py::test_req_general_object_part_positive_negative` | Same |
| `REQ_GENERAL_MULTI_IMAGE` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | — | — |
| `REQ_REVIEW_TRUST` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | — | — |
| `REQ_CAR_BODY_PANEL` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | — | — |
| `REQ_CAR_GLASS_LIGHT_MIRROR` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | — | — |
| `REQ_CAR_IDENTITY_OR_SIDE` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | — | — |
| `REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | — | — |
| `REQ_LAPTOP_BODY_HINGE_PORT` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | — | — |
| `REQ_PACKAGE_EXTERIOR` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | Indirect: `test_build_active_requirement_ids_package` (activation only) | — |
| `REQ_PACKAGE_LABEL_OR_STAIN` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | — | — |
| `REQ_PACKAGE_CONTENTS` | §1.2 | `requirements_map.py` → `evaluate_requirement_satisfaction` | — | — |

**Catalog / activation:** `REQUIREMENTS_CATALOG`, `build_active_requirement_ids`, `load_requirements_catalog` — `test_requirements_map.py::test_catalog_matches_csv`, `test_build_active_requirement_ids_package`

---

## 3. Multi-Part Resolution (`MP-*` → decision_matrix §7)

| Rule ID | Matrix § | Implementation | Positive test | Negative test |
|---------|----------|----------------|---------------|---------------|
| `MP-1` | §7.2 step 1 | `resolve_claim.py` → `resolve_claim` (always records MP-1) | Implicit in all `test_resolve_claim.py` cases | — (**no negative**; MP-1 always `outcome=True` when `alleged_parts` non-empty) |
| `MP-2` | §7.2 step 2 | `resolve_claim.py` → single-part branch | `test_resolve_claim.py::test_mp2_single_part_positive` | `test_resolve_claim.py::test_mp2_multi_part_negative` |
| `MP-3` | §7.2 step 3 | `resolve_claim.py` → multi-part branch | `test_resolve_claim.py::test_mp4_visibility_selection_positive` (MP-3 record) | — (**skipped on single-part path**; no dedicated negative) |
| `MP-4` | §7.2 step 4 | `resolve_claim.py` → visibility or tie-break selection | `test_resolve_claim.py::test_mp4_visibility_selection_positive` | — (**no case where MP-4 `outcome=False`**) |
| `MP-5` | §7.2 step 5 | `resolve_claim.py` → secondary parts | `test_resolve_claim.py::test_mp5_secondary_parts_positive` | — (**no single-part negative**; MP-5 not emitted) |

---

## 4. Evidence Sufficiency (`ESM-R*` → decision_matrix §1.1)

| Rule ID | Matrix § | Implementation | Positive test | Negative test |
|---------|----------|----------------|---------------|---------------|
| `ESM-R01` | §1.1 | `sufficiency.py` → `evaluate_sufficiency` | `test_sufficiency.py::test_esm_rules_positive[ESM-R01]` | `test_sufficiency.py::test_esm_r01_negative_when_readable` |
| `ESM-R02` | §1.1 | `sufficiency.py` → ordered check on `identity_conflict` | — | — |
| `ESM-R03` | §1.1 | `sufficiency.py` → ordered check on `no_part_visible` | `test_sufficiency.py::test_esm_rules_positive[ESM-R03]` | — |
| `ESM-R04` | §1.1 | `sufficiency.py` → contents claim + area check | — | — |
| `ESM-R05` | §1.1 | `sufficiency.py` → `part_visible_low_only` gate | — | — |
| `ESM-R06` | §1.1 | `sufficiency.py` → `not part_clear` | — (**structurally dead** — see §6) | `test_sufficiency.py::test_esm_r06_negative_when_part_clear` |
| `ESM-R07` | §1.1 | `sufficiency.py` + `identity_helpers.py` → `identity_matchable_across_best_set` | — | — |
| `ESM-R08` | §1.1 | `sufficiency.py` → default branch | `test_sufficiency.py::test_esm_r08_default_positive` | — |

**Helper (no separate Rule ID):** `identity_helpers.py::identity_matchable_across_best_set` — referenced by ESM-R07 and `REQ_CAR_IDENTITY_OR_SIDE` predicate path.

---

## 5. Valid Image / Trust (`VI-R*` → decision_matrix §2.1)

| Rule ID | Matrix § | Implementation | Positive test | Negative test |
|---------|----------|----------------|---------------|---------------|
| `VI-R01` | §2.1 | `trust.py` → `evaluate_trust` | `test_trust.py::test_vi_rules_positive[VI-R01]` | `test_trust.py::test_vi_r01_negative_when_usable` |
| `VI-R02` | §2.1 | `trust.py` → `any_non_original_high` check | `test_trust.py::test_vi_rules_positive[VI-R02]` | — |
| `VI-R03` | §2.1 | `trust.py` → `_contents_unreviewable` | — | — |
| `VI-R04` | §2.1 | `trust.py` → default branch | `test_trust.py::test_vi_r04_default_positive` | — |

---

## 6. Supporting Modules (no matrix Rule IDs)

| Module | Role | Matrix reference |
|--------|------|------------------|
| `confidence.py` | Shared confidence ranking | §8.1 (policy, not a Rule ID) |
| `consistency.py` | Aggregates §0.5 predicates into `ConsistencyContext` | §0.5 (derived; no separate rule table) |
| `types.py` | Typed stage bundles, `RuleExecutionRecord` | Guardrails §6 |
| `rule_trace.py` | `RuleExecutionRecord` → `RuleHit` | Guardrails §6; contracts `DecisionTrace` |
| `__init__.py` | Public exports | — |

---

## 7. Gap Analysis

### 7.1 Missing Rule IDs (P2 scope)

**None.** All 41 P2-scoped Rule IDs are implemented.

**Future phases (not P2 gaps):**

| Family | Count | Expected phase |
|--------|-------|----------------|
| `CS-R01`..`CS-R08` | 8 | P3 `verdict.py` |
| `SV-R01`..`SV-R08` | 8 | P3 `severity.py` |
| `SI-R01`..`SI-R07` | 7 | P3 `supporting_images.py` |
| `MRR-1`..`MRR-6` | 6 | P3 `risk.py` |

### 7.2 Untested Rule IDs (missing positive and/or negative per guardrails §3)

| Rule ID | Positive test | Negative test | Gap |
|---------|---------------|---------------|-----|
| `PRED-IMAGE-COUNT` | ✓ (weak) | Weak — outcome never `False` | Minor |
| `PRED-BEST-PART-CONFIDENCE` | ✓ (weak) | Weak — outcome never `False` | Minor |
| `REQ_GENERAL_MULTI_IMAGE` | ✗ | ✗ | **Major** |
| `REQ_REVIEW_TRUST` | ✗ | ✗ | **Major** |
| `REQ_CAR_BODY_PANEL` | ✗ | ✗ | **Major** |
| `REQ_CAR_GLASS_LIGHT_MIRROR` | ✗ | ✗ | **Major** |
| `REQ_CAR_IDENTITY_OR_SIDE` | ✗ | ✗ | **Major** |
| `REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD` | ✗ | ✗ | **Major** |
| `REQ_LAPTOP_BODY_HINGE_PORT` | ✗ | ✗ | **Major** |
| `REQ_PACKAGE_EXTERIOR` | Partial (activation only) | ✗ | **Major** |
| `REQ_PACKAGE_LABEL_OR_STAIN` | ✗ | ✗ | **Major** |
| `REQ_PACKAGE_CONTENTS` | ✗ | ✗ | **Major** |
| `MP-1` | Implicit | ✗ | **Major** |
| `MP-3` | ✓ | ✗ | **Major** |
| `MP-4` | ✓ | ✗ | **Major** |
| `MP-5` | ✓ | ✗ | **Major** |
| `ESM-R02` | ✗ | ✗ | **Major** |
| `ESM-R03` | ✓ | ✗ | **Major** |
| `ESM-R04` | ✗ | ✗ | **Major** |
| `ESM-R05` | ✗ | ✗ | **Major** |
| `ESM-R06` | ✗ (dead path) | ✓ | **Major** |
| `ESM-R07` | ✗ | ✗ | **Major** |
| `ESM-R08` | ✓ | ✗ | **Major** |
| `VI-R02` | ✓ | ✗ | **Major** |
| `VI-R03` | ✗ | ✗ | **Major** |
| `VI-R04` | ✓ | ✗ | **Major** |

**Summary:** 24 Rule IDs lack a complete positive + negative test pair per [rule_guardrails.md](rule_guardrails.md) §3.

### 7.3 Duplicate Rule IDs

**None found** in a single evaluation trace.

- `MP-4` is emitted once per multi-part resolution (visibility win or tie-break variant — same ID, different justification).
- ESM rules are evaluated in order; only one rule sets `triggered_rule_id`, but all evaluated rules appear once in `rule_records`.

### 7.4 Dead Rule IDs

| Rule ID | Status | Reason |
|---------|--------|--------|
| `ESM-R06` | **Dead positive path** | `PART_CLEAR=false` implies `NO_PART_VISIBLE=true` under §0.5 predicate definitions, so `ESM-R03` always fires first. `ESM-R06` is evaluated and recorded with `outcome=False` but cannot become `triggered_rule_id`. |

No other implemented Rule IDs are unreachable.

### 7.5 Rule IDs Implemented but Not Referenced by decision_matrix.md

**None.**

- `PRED-*` IDs are the implementation trace IDs for §0.5 predicate names — documented in [rule_guardrails.md](rule_guardrails.md) §8.
- All `REQ_*` IDs appear in §1.2 and `dataset/evidence_requirements.csv`.
- All `MP-*`, `ESM-R*`, `VI-R*` IDs appear in §7, §1.1, and §2.1 respectively.

---

## 8. Traceability Infrastructure

| Capability | Location | Test |
|------------|----------|------|
| `RuleExecutionRecord` (rule_id, outcome, justification) | `rules/types.py` | `test_rule_guardrails.py::test_rule_execution_record_has_required_trace_fields` |
| `RuleHit` assembly without recomputation | `rules/rule_trace.py` | `test_rule_trace.py` |
| P2 purity (no verdict/severity/risk) | AST guard | `test_rule_guardrails.py::test_p2_modules_avoid_verdict_severity_risk_symbols` |

---

## 9. Remediation Checklist (to reach `P2_TRACEABILITY_APPROVED`)

1. Add dedicated test module `test_requirements_coverage.py` with pos/neg pairs for all 11 `REQ_*` satisfaction paths.
2. Add ESM positive tests: `ESM-R02` (identity conflict), `ESM-R04` (contents), `ESM-R05` (low-only part), `ESM-R07` (identity constraint mismatch); ESM-R08 negative (force a higher-priority match).
3. Add VI-R03 positive (contents + all cropped high) and negatives for `VI-R02`, `VI-R04`.
4. Add MP negative tests: single-part path asserts MP-3/MP-4/MP-5 absent or `outcome=False`; document MP-1 as always-true invariant test.
5. Resolve or document `ESM-R06` dead path (merge with ESM-R03 in matrix commentary, or narrow ESM-R06 condition in implementation if matrix intent differs).
6. Strengthen `PRED-IMAGE-COUNT` and `PRED-BEST-PART-CONFIDENCE` negative cases to assert distinguishable outcomes or value_text deltas.

---

## 10. Test Suite Snapshot

| Metric | Value |
|--------|-------|
| Total tests (`code/tests/`) | 103 passing |
| Implemented P2 Rule IDs | 41 |
| Rule IDs with full pos+neg coverage | 17 |
| Rule IDs with coverage gaps | 24 |

---

## References

- [decision_matrix.md](decision_matrix.md) — §0.5, §1, §2, §7
- [rule_guardrails.md](rule_guardrails.md) — §3 Rule Coverage, §6 Traceability, §8 Module Scope
- [p0_review.md](p0_review.md) — P0 gate (approved)
