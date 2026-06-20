# ESM-R06 Analysis

**Date:** 2026-06-19  
**Scope:** Evidence Sufficiency Matrix rule `ESM-R06` ([decision_matrix.md](decision_matrix.md) §1.1)  
**Implementation:** `code/rules/sufficiency.py` → ordered check `not part_clear`  
**Status:** Analysis only — **no production changes**

---

## Matrix Definition

| Rule ID | Condition | `evidence_standard_met` |
|---------|-----------|-------------------------|
| ESM-R06 | `PART_CLEAR = false` | `false` |

Template key: `esm_r06_part_not_clear` — *"The claimed {part} is not visible clearly enough to evaluate the claim."*

---

## Verdict

## **B. Dead rule caused by decision matrix ordering and predicate algebra**

`ESM-R06` is implemented and traced in `rule_records`, but it **cannot become `triggered_rule_id`** under the current §0.5 predicate definitions and top-down ESM evaluation order.

---

## Predicate Definitions (§0.5)

| Predicate | Formal definition |
|-----------|-------------------|
| `PART_CLEAR` | ∃ image: `claimed_primary_part_visible = true` AND confidence ∈ {high, medium} |
| `NO_PART_VISIBLE` | ∀ images: `claimed_primary_part_visible = false` OR confidence = low |

---

## Logical Implication

If `PART_CLEAR = false`, then **no** image has `visible=true` at medium or higher confidence.

For every image, either:

- `visible = false`, or  
- `visible = true` with confidence = **low** only.

In both cases each image satisfies `(not visible) OR (confidence = low)`, so:

```text
PART_CLEAR = false  ⟹  NO_PART_VISIBLE = true
```

---

## Evaluation Order (§1.1)

Rules are evaluated top to bottom; first match wins:

```text
ESM-R01 … ESM-R05 → ESM-R03 (NO_PART_VISIBLE) → … → ESM-R06 (not PART_CLEAR) → ESM-R07 → ESM-R08
```

When `PART_CLEAR = false`:

1. `NO_PART_VISIBLE = true` → **ESM-R03 matches first**
2. Loop breaks before `ESM-R06` is reached
3. `ESM-R06` is **never appended** to `rule_records` on the positive path

When `PART_CLEAR = true`:

1. `ESM-R06` condition is false
2. If evaluation reaches `ESM-R06`, record shows `outcome=False` (see `test_esm_r06_negative_when_part_clear`)

There is **no input** where `ESM-R06` matches with `outcome=True` and becomes `triggered_rule_id`.

---

## Test Evidence

| Test | File | Asserts |
|------|------|---------|
| Negative (condition false) | `test_sufficiency.py::test_esm_r06_negative_when_part_clear` | `ESM-R06` record `outcome=False` when part clear |
| Unreachability (positive trigger) | `test_sufficiency_coverage.py::test_esm_r06_positive_trigger_unreachable` | `triggered_rule_id=ESM-R03`, `ESM-R06` record absent |

---

## Related Rule: ESM-R05

The same preemption pattern affects **ESM-R05** (`PART_VISIBLE_LOW_ONLY` without high-confidence image):

- `PART_VISIBLE_LOW_ONLY = true` requires `best_part_confidence = low`
- That implies all images are at low or absent visibility → `NO_PART_VISIBLE = true`
- **ESM-R03 fires before ESM-R05**

Test: `test_sufficiency_coverage.py::test_esm_r05_positive_trigger_unreachable`

---

## Recommendation

1. **Do not change implementation** for P2 — current code faithfully mirrors the matrix table row-for-row.
2. **Treat ESM-R06 (and ESM-R05) as documentation-layer redundancy** in `decision_matrix.md` — human-readable failure modes that collapse to ESM-R03 in formal evaluation.
3. **Optional future matrix revision** (outside P2): merge ESM-R05/R06 into ESM-R03 with distinct `reason_template_key` variants, or reorder/narrow conditions so rows are mutually exclusive.
4. **Traceability:** mark both rules as **DEAD_TRIGGER** in [rule_coverage_matrix.md](rule_coverage_matrix.md); coverage uses unreachability tests instead of positive trigger tests.

---

## References

- [decision_matrix.md](decision_matrix.md) §0.5, §1.1
- [p2_traceability_review.md](p2_traceability_review.md) §7.4
- `code/rules/sufficiency.py`
