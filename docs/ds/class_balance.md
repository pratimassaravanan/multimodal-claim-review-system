# Class Balance Analysis

**Dataset:** `dataset/sample_claims.csv` (n=20 labeled rows)  
**Purpose:** Quantify label imbalance, evaluation risks, and weighted metric justification  
**Companion:** [evaluation_metrics.md](../evaluation_metrics.md) (canonical weights)

---

## 1. claim_status Distribution

| claim_status | Count | Percentage |
|--------------|-------|------------|
| supported | 12 | 60.0% |
| contradicted | 5 | 25.0% |
| not_enough_information | 3 | 15.0% |
| **Total** | **20** | **100%** |

**Imbalance ratio (majority:minority):** 12:3 = **4:1** (supported vs NEI).

### Evaluation risk

- A naive classifier predicting `supported` for every row achieves **60% claim_status accuracy** without learning.
- NEI class has only **3 examples** — high variance; one error = 33% NEI recall loss.
- Contradicted class (5 rows) spans four distinct mechanisms (exaggeration, part mismatch, absent damage, wrong object) — treating as one class hides subtype errors.

### Weighted metric implication

`claim_status` receives **40%** of end-to-end weighted score (see evaluation_metrics.md) — highest single component — precisely because it is both the primary business outcome and the most imbalanced class.

---

## 2. severity Distribution

| severity | Count | Percentage | Typical claim_status |
|----------|-------|------------|----------------------|
| medium | 11 | 55.0% | supported (10), contradicted (1) |
| unknown | 3 | 15.0% | not_enough_information (3) |
| low | 3 | 15.0% | contradicted (2), supported (1) |
| none | 2 | 10.0% | contradicted (2) |
| high | 1 | 5.0% | contradicted (1) |
| **Total** | **20** | **100%** | |

**Note:** `user_033` is contradicted with `severity=low` (visible crease on wrong object).

### Evaluation risk

- **medium** dominates (55%). Defaulting to `medium` on supported rows yields high accuracy.
- **high** appears once (`user_008`) — insufficient to validate high-severity calibration.
- **unknown** perfectly correlates with NEI (HR-03) — 3/3; severity engine correctness is partially redundant with verdict engine on this sample.

### Weighted metric implication

`severity` receives **10%** of weighted score — lower than status because it is derivative of verdict + vision observations and highly correlated with NEI path.

---

## 3. risk_flags Distribution

### Row-level patterns (exact strings)

| risk_flags pattern | Count | user_ids |
|--------------------|-------|----------|
| none | 11 | 001, 004, 007, 003, 009, 010, 011, 012, 018, 015, 030 |
| blurry_image | 1 | 003 |
| wrong_angle;damage_not_visible | 1 | 006 |
| wrong_object;claim_mismatch;manual_review_required | 1 | 002 |
| claim_mismatch;user_history_risk;manual_review_required | 1 | 005 |
| claim_mismatch;non_original_image;user_history_risk;manual_review_required | 1 | 008 |
| damage_not_visible;user_history_risk;manual_review_required | 1 | 020 |
| user_history_risk;manual_review_required | 1 | 031 |
| cropped_or_obstructed;damage_not_visible;manual_review_required | 1 | 032 |
| wrong_object;claim_mismatch;user_history_risk;manual_review_required | 1 | 033 |
| damage_not_visible;text_instruction_present;user_history_risk;manual_review_required | 1 | 034 |

### Individual flag prevalence (row contains flag)

| Flag | Rows | Rate |
|------|------|------|
| none (only flag) | 11 | 55.0% |
| manual_review_required | 8 | 40.0% |
| user_history_risk | 6 | 30.0% |
| damage_not_visible | 4 | 20.0% |
| claim_mismatch | 4 | 20.0% |
| wrong_object | 2 | 10.0% |
| blurry_image | 1 | 5.0% |
| wrong_angle | 1 | 5.0% |
| non_original_image | 1 | 5.0% |
| cropped_or_obstructed | 1 | 5.0% |
| text_instruction_present | 1 | 5.0% |

### Evaluation risk

- **Sparse multi-label:** 9 of 20 rows carry at least one risk flag; exact set match is a hard metric.
- Rare flags (`text_instruction_present`, `non_original_image`) have n=1 — F1 unstable.
- `manual_review_required` is often co-occurring with other flags — partial credit needed (macro-F1 per flag).

### Weighted metric implication

`risk_flags` macro-F1 receives **15%** of weighted score — second highest — because flag errors are visible to judges and sparse positives must not be ignored.

---

## 4. issue_type Distribution

| issue_type | Count | user_ids |
|------------|-------|----------|
| medium-tier damage types | | |
| dent | 2 | 001, 003 |
| crack | 3 | 004, 009, 018 |
| broken_part | 3 | 002, 007, 008 |
| stain | 1 | 011 |
| scratch | 1 | 005 |
| crushed_packaging | 1 | 015 |
| torn_packaging | 1 | 030 |
| water_damage | 1 | 031 |
| none | 2 | 020, 034 |
| unknown | 3 | 006, 032, 033 |
| **Total** | **20** | |

**Unique issue types:** 11 values across 20 rows.

### Evaluation risk

- Long tail: 8 issue types appear exactly once.
- `unknown` aligns with NEI + one contradicted wrong-object row (`user_033`).
- `none` only on contradicted absent-damage rows.

---

## 5. object_part Distribution

| object_part | Count | claim_object |
|-------------|-------|--------------|
| rear_bumper | 2 | car |
| front_bumper | 2 | car |
| screen | 2 | laptop |
| seal | 2 | package |
| windshield | 1 | car |
| side_mirror | 1 | car |
| headlight | 1 | car |
| door | 1 | car |
| hinge | 1 | laptop |
| keyboard | 1 | laptop |
| corner | 1 | laptop |
| trackpad | 1 | laptop |
| package_corner | 1 | package |
| package_side | 1 | package |
| contents | 1 | package |
| unknown | 1 | package |
| **Total** | **20** | |

**Unique parts:** 16 values — high cardinality relative to n=20.

### Evaluation risk

- Per-part accuracy has high variance; aggregate `object_part_acc` only.
- `unknown` appears once — insufficient for unknown-class calibration.

---

## 6. Cross-Tabulations

### claim_status × claim_object

|  | car (8) | laptop (6) | package (6) |
|--|---------|--------------|---------------|
| supported | 4 | 5 | 3 |
| contradicted | 2 | 1 | 2 |
| NEI | 2 | 0 | 1 |

**Observation:** No NEI laptop rows in sample. Laptop path is under-tested for insufficient-evidence cases.

### claim_status × image_count

|  | 1 image (10) | 2 images (10) |
|--|--------------|---------------|
| supported | 7 | 5 |
| contradicted | 2 | 3 |
| NEI | 1 | 2 |

**Observation:** Identity conflict (`user_002`) and blur+clear (`user_003`) require multi-image handling.

### evidence_standard_met × valid_image

|  | valid_image=true | valid_image=false |
|--|------------------|-------------------|
| ESM=true | 16 | 1 (`user_008`) |
| ESM=false | 2 (`user_002`, `user_006`) | 1 (`user_032`) |

Confirms HR-06 orthogonality.

---

## 7. Class Imbalance Summary

| Dimension | Majority class | Rate | Risk level |
|-----------|----------------|------|------------|
| claim_status | supported | 60% | **High** |
| severity | medium | 55% | Medium |
| risk_flags | none | 55% | Medium |
| issue_type | crack/broken_part (tie) | 15% each | High (long tail) |
| object_part | (no majority) | ≤10% each | High |
| claim_object | car | 40% | Low |

---

## 8. Weighted Metric Justification

Canonical formula (from [evaluation_metrics.md](../evaluation_metrics.md)):

```text
Score = 0.40 × claim_status_acc
      + 0.20 × evidence_standard_met_acc
      + 0.15 × risk_flags_F1_macro
      + 0.10 × (issue_type_acc + object_part_acc) / 2
      + 0.10 × severity_acc
      + 0.05 × supporting_image_ids_exact_match
```

| Component | Weight | Justification from imbalance |
|-----------|--------|------------------------------|
| claim_status | 0.40 | Highest imbalance; primary judge metric; naive 60% baseline |
| evidence_standard_met | 0.20 | Gates verdict; only 3 negatives but critical for NEI path |
| risk_flags F1 | 0.15 | Sparse multi-label; 45% rows have flags |
| issue_type + object_part | 0.10 | Long tail; secondary to status |
| severity | 0.10 | Partially redundant with NEI→unknown |
| supporting_image_ids | 0.05 | Exact set; easier when NEI→none rule applies |

### Reporting requirements

Always report **slice metrics** alongside aggregate score:

1. Per `claim_status` class recall
2. Per `claim_object` accuracy
3. Per-flag risk F1
4. Confusion matrix for `claim_status`

---

## 9. Recommendations

1. **Do not optimize on accuracy alone** — report weighted score and per-class recall.
2. **Treat n=20 as development only** — use [synthetic_generation_strategy.md](../synthetic_generation_strategy.md) for underrepresented classes (NEI laptop, high severity, rare flags).
3. **Freeze weights** in `code/config/metrics_weights.yaml` during implementation — changes require new hypothesis entry in [hypotheses.md](hypotheses.md).
