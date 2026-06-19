# Label Analysis

**Dataset:** `dataset/sample_claims.csv` (n=20)  
**Supplementary:** `dataset/user_history.csv` for history-flag cross-check  
**Analysis date:** 2026-06-19

---

## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| Total labeled rows | 20 |
| Unique user_ids | 20 |
| claim_object types | 3 (car, laptop, package) |
| Image count range | 1–2 per row |
| Total images referenced | 30 |
| Languages observed | English (primary), Hindi (2 rows), mixed narrative English |

---

## 2. Per-Object Statistics

### 2.1 Car (n=8)

| user_id | claim_status | issue_type | object_part | ESM | valid_image | severity | images |
|---------|--------------|------------|-------------|-----|-------------|----------|--------|
| user_001 | supported | dent | rear_bumper | true | true | medium | 1 |
| user_002 | NEI | broken_part | front_bumper | false | true | unknown | 2 |
| user_003 | supported | dent | door | true | true | medium | 2 |
| user_004 | supported | crack | windshield | true | true | medium | 2 |
| user_005 | contradicted | scratch | rear_bumper | true | true | low | 2 |
| user_006 | NEI | unknown | headlight | false | true | unknown | 1 |
| user_007 | supported | broken_part | side_mirror | true | true | medium | 1 |
| user_008 | contradicted | broken_part | front_bumper | true | false | high | 1 |

| Metric | car |
|--------|-----|
| supported | 4 (50%) |
| contradicted | 2 (25%) |
| NEI | 2 (25%) |
| Multi-image rows | 4 (50%) |
| ESM false | 2 |
| valid_image false | 1 |
| With risk flags | 5 (63%) |

**Car-specific patterns:** Identity conflict (`user_002`), severity exaggeration (`user_005`), part mismatch (`user_008`), wrong angle (`user_006`), blur compensation (`user_003`).

---

### 2.2 Laptop (n=6)

| user_id | claim_status | issue_type | object_part | ESM | valid_image | severity | images |
|---------|--------------|------------|-------------|-----|-------------|----------|--------|
| user_009 | supported | crack | screen | true | true | medium | 1 |
| user_010 | supported | broken_part | hinge | true | true | medium | 2 |
| user_011 | supported | stain | keyboard | true | true | medium | 1 |
| user_012 | supported | dent | corner | true | true | low | 2 |
| user_018 | supported | crack | screen | true | true | medium | 1 |
| user_020 | contradicted | none | trackpad | true | true | none | 1 |

| Metric | laptop |
|--------|--------|
| supported | 5 (83%) |
| contradicted | 1 (17%) |
| NEI | 0 (0%) |
| Multi-image rows | 2 (33%) |
| With risk flags | 1 (17%) |

**Laptop-specific patterns:** Dominantly supported; one absent-damage contradiction (`user_020`); shattered language → crack (`user_018`).

---

### 2.3 Package (n=6)

| user_id | claim_status | issue_type | object_part | ESM | valid_image | severity | images |
|---------|--------------|------------|-------------|-----|-------------|----------|
| user_015 | supported | crushed_packaging | package_corner | true | true | medium | 1 |
| user_030 | supported | torn_packaging | seal | true | true | medium | 2 |
| user_031 | supported | water_damage | package_side | true | true | medium | 1 |
| user_032 | NEI | unknown | contents | false | false | unknown | 2 |
| user_033 | contradicted | unknown | unknown | true | true | low | 1 |
| user_034 | contradicted | none | seal | true | true | none | 2 |

| Metric | package |
|--------|---------|
| supported | 3 (50%) |
| contradicted | 2 (33%) |
| NEI | 1 (17%) |
| Multi-image rows | 3 (50%) |
| valid_image false | 1 |
| With risk flags | 4 (67%) |

**Package-specific patterns:** Contents missing (`user_032`), wrong object (`user_033`), intact seal contradiction (`user_034`), Hindi chat (`user_030`).

---

## 3. Supported vs Contradicted vs NEI

| Status | Count | % | Primary triggers (from labels) |
|--------|-------|---|--------------------------------|
| **supported** | 12 | 60% | Clear part visible + damage matches claim |
| **contradicted** | 5 | 25% | Exaggeration, part mismatch, absent damage, wrong object |
| **not_enough_information** | 3 | 15% | Identity conflict, part not visible, contents not shown |

### Contradiction subtypes (empirical)

| Subtype | user_id | Mechanism |
|---------|---------|-----------|
| Severity exaggeration | user_005 | CS-R06 — minor scratch vs "pretty bad" |
| Part mismatch | user_008 | CS-R04 — hood claimed, bumper visible |
| Absent damage | user_020, user_034 | CS-R03 — part visible, no damage / intact seal |
| Wrong object | user_033 | CS-R02 — not a shipping box |

---

## 4. Multi-Image Frequency

| image_count | rows | % |
|-------------|------|---|
| 1 | 10 | 50% |
| 2 | 10 | 50% |

### Multi-image row outcomes

| Pattern | user_ids |
|---------|----------|
| Blur + clear → supported | user_003 |
| Identity conflict → NEI | user_002 |
| Both images for contradiction | user_034 |
| Close-up + context → supported | user_004, user_010, user_012, user_030 |
| Two photos, NEI contents | user_032 |

**REQ_GENERAL_MULTI_IMAGE** applies to 10 rows (image count ≥ 2).

---

## 5. Risk Flag Frequency

See [class_balance.md](class_balance.md) §3 for full table.

**Key observations:**

- 9 rows (45%) carry at least one non-`none` flag
- `manual_review_required` is the most common composite trigger (8 rows)
- Image-quality flags (`blurry_image`, `wrong_angle`, `cropped_or_obstructed`) appear in 3 rows
- Authenticity flags (`non_original_image`, `text_instruction_present`) appear in 2 rows

### History flag correlation (sample users in user_history.csv)

| user_id | history_flags | UHR in output? | MRR in output? |
|---------|---------------|----------------|----------------|
| user_005 | user_history_risk | yes | yes |
| user_008 | user_history_risk | yes | yes |
| user_020 | user_history_risk | yes | yes |
| user_031 | user_history_risk | yes | yes |
| user_032 | manual_review_required | no | yes |
| user_033 | user_history_risk | yes | yes |
| user_034 | user_history_risk | yes | yes |

HR-04 and HR-10 validated on sample subset.

---

## 6. Common Issue Types

| Rank | issue_type | count | typical status |
|------|------------|-------|----------------|
| 1 | crack | 3 | supported |
| 1 | broken_part | 3 | mixed |
| 1 | unknown | 3 | NEI + wrong object |
| 4 | dent | 2 | supported |
| 4 | none | 2 | contradicted |
| 6+ | (6 others) | 1 each | various |

**Packaging issues:** `crushed_packaging`, `torn_packaging`, `water_damage` — one each, all supported except contradicted seal.

---

## 7. Common Object Parts

| claim_object | most frequent parts |
|--------------|---------------------|
| car | rear_bumper (2), front_bumper (2), then 1 each |
| laptop | screen (2), then 1 each |
| package | seal (2), then 1 each |

No sample row uses generic `body` part label.

---

## 8. Language Observations

| user_id | Language signal | claim_object | Notes |
|---------|-----------------|--------------|-------|
| user_002 | Hindi | car | Romanized Hindi in chat; labels use English enums |
| user_030 | Hindi | package | Romanized Hindi; torn packaging claim |
| user_006 | English (verbose) | car | Long clarifying dialogue; NEI outcome |
| user_018 | English (verbose) | laptop | "shattered" → `crack` label |
| All others | English | — | Standard support dialogue |

**Implication:** Flash must extract `alleged_parts` and `alleged_issue_types` in ontology enums regardless of chat language. No non-English values appear in output columns.

---

## 9. evidence_standard_met and valid_image

| evidence_standard_met | valid_image | count | user_ids |
|-----------------------|-------------|-------|----------|
| true | true | 16 | majority |
| true | false | 1 | user_008 |
| false | true | 2 | user_002, user_006 |
| false | false | 1 | user_032 |

---

## 10. supporting_image_ids Patterns

| Pattern | count | user_ids |
|---------|-------|----------|
| Single image ID | 11 | most supported + some contradicted |
| Multiple IDs (`;`) | 4 | user_002, user_034, user_003 (img_2 only), etc. |
| none | 5 | user_006, user_032, user_002 is exception with IDs |

**Note:** `user_003` supported with `img_2` only — blurry `img_1` excluded (SI-R04 exclusion).

---

## 11. Co-occurrence Highlights

| Field A | Field B | Observation |
|---------|---------|-------------|
| NEI | severity=unknown | 3/3 (HR-03) |
| contradicted | ESM=true | 5/5 (HR-02) |
| UHR in history | UHR in risk_flags | 6/6 in sample (HR-04) |
| supported | severity=medium | 10/12 |
| contradicted | issue_type=none | 2/5 (absent damage cases) |

---

## 12. Gaps Relative to Test Set

The sample set does **not** include:

- Multi-part claims (present in `claims.csv` test rows)
- Chat prompt injection (test `case_055`)
- Spanish or Chinese chat (mentioned in problem_decomposition)
- `glass_shatter` issue type in any label

These gaps motivate [synthetic_generation_strategy.md](../synthetic_generation_strategy.md).

---

## Cross-Reference

| Document | Role |
|----------|------|
| [class_balance.md](class_balance.md) | Imbalance and weights |
| [hidden_business_rules.md](hidden_business_rules.md) | Empirical rules from this analysis |
| [failure_taxonomy.md](failure_taxonomy.md) | Failure classes |
