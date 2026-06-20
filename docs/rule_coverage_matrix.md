# Rule Coverage Matrix

**Date:** 2026-06-19  
**Scope:** P2 rule surface (41 Rule IDs)  
**Authority:** [decision_matrix.md](decision_matrix.md), [rule_guardrails.md](rule_guardrails.md) §3  
**Test root:** `code/tests/rules/`

**Traceability status legend:**

| Status | Meaning |
|--------|---------|
| **PASS** | Positive and negative tests documented |
| **DEAD_TRIGGER** | Implemented; positive trigger unreachable (see [esm_r06_analysis.md](esm_r06_analysis.md)) |
| **INVARIANT** | Rule always `outcome=True` when emitted; negative = not emitted or invariant held |

---

## PRED-* (§0.5 → rule_guardrails §8)

| Rule ID | Source | Implementation | Positive test | Negative test | Status |
|---------|--------|----------------|---------------|---------------|--------|
| `PRED-IMAGE-COUNT` | decision_matrix §0.5 | `predicates.py::compute_image_count` | `test_predicates.py::test_predicate_has_positive_and_negative_cases[PRED-IMAGE-COUNT]` | Same (`value_text` 1 vs 2) | PASS |
| `PRED-ANY-FILE-UNREADABLE` | §0.5 | `predicates.py::compute_any_file_unreadable` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-BEST-PART-CONFIDENCE` | §0.5 | `predicates.py::compute_best_part_confidence` | Parametrized (`value_text=high`) | Parametrized (`value_text=low`) | PASS |
| `PRED-BEST-PART-IMAGE-SET` | §0.5 | `predicates.py::compute_best_part_image_set` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-PART-CLEAR` | §0.5 | `predicates.py::compute_part_clear` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-PART-VISIBLE-LOW-ONLY` | §0.5 | `predicates.py::compute_part_visible_low_only` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-NO-PART-VISIBLE` | §0.5 | `predicates.py::compute_no_part_visible` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-IDENTITY-CONFLICT` | §0.5 | `predicates.py::compute_identity_conflict` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-WRONG-OBJECT-SET` | §0.5 | `predicates.py::compute_wrong_object_set` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-ANY-NON-ORIGINAL-HIGH` | §0.5 | `predicates.py::compute_any_non_original_high` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-CONTENTS-CLAIM` | §0.5 | `predicates.py::compute_contents_claim` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-CONTENTS-AREA-CLEAR` | §0.5 | `predicates.py::compute_contents_area_clear` | Parametrized predicate test | Parametrized predicate test | PASS |
| `PRED-ALL-IMAGES-UNUSABLE` | §0.5 | `predicates.py::compute_all_images_unusable` | Parametrized predicate test | Parametrized predicate test | PASS |

---

## REQ_* (§0.3 / §1.2)

| Rule ID | Source | Implementation | Positive test | Negative test | Status |
|---------|--------|----------------|---------------|---------------|--------|
| `REQ_GENERAL_OBJECT_PART` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_general_object_part_positive` | `test_requirements_coverage.py::test_req_general_object_part_negative` | PASS |
| `REQ_GENERAL_MULTI_IMAGE` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_general_multi_image_positive_single_image` | `test_requirements_coverage.py::test_req_general_multi_image_negative_no_clear_image_in_set` | PASS |
| `REQ_REVIEW_TRUST` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_review_trust_positive` | `test_requirements_coverage.py::test_req_review_trust_negative` | PASS |
| `REQ_CAR_BODY_PANEL` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_part_clear_family_positive[REQ_CAR_BODY_PANEL]` | `test_requirements_coverage.py::test_req_part_clear_family_negative[REQ_CAR_BODY_PANEL]` | PASS |
| `REQ_CAR_GLASS_LIGHT_MIRROR` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_part_clear_family_positive[REQ_CAR_GLASS_LIGHT_MIRROR]` | `test_requirements_coverage.py::test_req_part_clear_family_negative[REQ_CAR_GLASS_LIGHT_MIRROR]` | PASS |
| `REQ_CAR_IDENTITY_OR_SIDE` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_car_identity_or_side_positive` | `test_requirements_coverage.py::test_req_car_identity_or_side_negative` | PASS |
| `REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_part_clear_family_positive[REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD]` | `test_requirements_coverage.py::test_req_part_clear_family_negative[REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD]` | PASS |
| `REQ_LAPTOP_BODY_HINGE_PORT` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_part_clear_family_positive[REQ_LAPTOP_BODY_HINGE_PORT]` | `test_requirements_coverage.py::test_req_part_clear_family_negative[REQ_LAPTOP_BODY_HINGE_PORT]` | PASS |
| `REQ_PACKAGE_EXTERIOR` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_part_clear_family_positive[REQ_PACKAGE_EXTERIOR]` | `test_requirements_coverage.py::test_req_part_clear_family_negative[REQ_PACKAGE_EXTERIOR]` | PASS |
| `REQ_PACKAGE_LABEL_OR_STAIN` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_part_clear_family_positive[REQ_PACKAGE_LABEL_OR_STAIN]` | `test_requirements_coverage.py::test_req_part_clear_family_negative[REQ_PACKAGE_LABEL_OR_STAIN]` | PASS |
| `REQ_PACKAGE_CONTENTS` | §1.2 | `requirements_map.py::evaluate_requirement_satisfaction` | `test_requirements_coverage.py::test_req_package_contents_positive` | `test_requirements_coverage.py::test_req_package_contents_negative` | PASS |

---

## MP-* (§7.2)

| Rule ID | Source | Implementation | Positive test | Negative test | Status |
|---------|--------|----------------|---------------|---------------|--------|
| `MP-1` | §7.2 step 1 | `resolve_claim.py::resolve_claim` | `test_resolve_claim.py::test_mp1_positive_always_records` | `test_resolve_claim.py::test_mp1_negative_never_false` (invariant) | INVARIANT |
| `MP-2` | §7.2 step 2 | `resolve_claim.py::resolve_claim` | `test_resolve_claim.py::test_mp2_single_part_positive` | `test_resolve_claim.py::test_mp2_multi_part_negative` | PASS |
| `MP-3` | §7.2 step 3 | `resolve_claim.py::resolve_claim` | `test_resolve_claim.py::test_mp4_visibility_selection_positive` | `test_resolve_claim.py::test_mp3_negative_not_emitted_on_single_part` | PASS |
| `MP-4` | §7.2 step 4 | `resolve_claim.py::resolve_claim` | `test_resolve_claim.py::test_mp4_visibility_selection_positive` | `test_resolve_claim.py::test_mp4_negative_not_emitted_on_single_part` | PASS |
| `MP-5` | §7.2 step 5 | `resolve_claim.py::resolve_claim` | `test_resolve_claim.py::test_mp5_secondary_parts_positive` | `test_resolve_claim.py::test_mp5_negative_not_emitted_on_single_part` | PASS |

---

## ESM-R* (§1.1)

| Rule ID | Source | Implementation | Positive test | Negative test | Status |
|---------|--------|----------------|---------------|---------------|--------|
| `ESM-R01` | §1.1 | `sufficiency.py::evaluate_sufficiency` | `test_sufficiency.py::test_esm_rules_positive[ESM-R01]` | `test_sufficiency.py::test_esm_r01_negative_when_readable` | PASS |
| `ESM-R02` | §1.1 | `sufficiency.py::evaluate_sufficiency` | `test_sufficiency_coverage.py::test_esm_r02_positive` | `test_sufficiency_coverage.py::test_esm_r02_negative` | PASS |
| `ESM-R03` | §1.1 | `sufficiency.py::evaluate_sufficiency` | `test_sufficiency.py::test_esm_rules_positive[ESM-R03]` | `test_sufficiency_coverage.py::test_esm_r03_negative_when_part_visible` | PASS |
| `ESM-R04` | §1.1 | `sufficiency.py::evaluate_sufficiency` | `test_sufficiency_coverage.py::test_esm_r04_positive` | `test_sufficiency_coverage.py::test_esm_r04_negative` | PASS |
| `ESM-R05` | §1.1 | `sufficiency.py::evaluate_sufficiency` | `test_sufficiency_coverage.py::test_esm_r05_positive_trigger_unreachable` | `test_sufficiency_coverage.py::test_esm_r05_negative` | DEAD_TRIGGER |
| `ESM-R06` | §1.1 | `sufficiency.py::evaluate_sufficiency` | `test_sufficiency_coverage.py::test_esm_r06_positive_trigger_unreachable` | `test_sufficiency.py::test_esm_r06_negative_when_part_clear` | DEAD_TRIGGER |
| `ESM-R07` | §1.1 | `sufficiency.py` + `identity_helpers.py` | `test_sufficiency_coverage.py::test_esm_r07_positive` | `test_sufficiency_coverage.py::test_esm_r07_negative` | PASS |
| `ESM-R08` | §1.1 | `sufficiency.py::evaluate_sufficiency` | `test_sufficiency.py::test_esm_r08_default_positive` | `test_sufficiency_coverage.py::test_esm_r08_negative_when_higher_priority_matches` | PASS |

---

## VI-R* (§2.1)

| Rule ID | Source | Implementation | Positive test | Negative test | Status |
|---------|--------|----------------|---------------|---------------|--------|
| `VI-R01` | §2.1 | `trust.py::evaluate_trust` | `test_trust.py::test_vi_rules_positive[VI-R01]` | `test_trust.py::test_vi_r01_negative_when_usable` | PASS |
| `VI-R02` | §2.1 | `trust.py::evaluate_trust` | `test_trust.py::test_vi_rules_positive[VI-R02]` | `test_trust_coverage.py::test_vi_r02_negative` | PASS |
| `VI-R03` | §2.1 | `trust.py::evaluate_trust` | `test_trust_coverage.py::test_vi_r03_positive` | `test_trust_coverage.py::test_vi_r03_negative` | PASS |
| `VI-R04` | §2.1 | `trust.py::evaluate_trust` | `test_trust.py::test_vi_r04_default_positive` | `test_trust_coverage.py::test_vi_r04_negative_when_vi_r01_matches` | PASS |

---

## Summary

| Metric | Count |
|--------|-------|
| Total Rule IDs | 41 |
| PASS | 38 |
| DEAD_TRIGGER | 2 (`ESM-R05`, `ESM-R06`) |
| INVARIANT | 1 (`MP-1`) |
| Production logic changes | 0 |

---

## References

- [decision_matrix.md](decision_matrix.md)
- [rule_guardrails.md](rule_guardrails.md)
- [esm_r06_analysis.md](esm_r06_analysis.md)
- [p2_traceability_remediation_review.md](p2_traceability_remediation_review.md)
