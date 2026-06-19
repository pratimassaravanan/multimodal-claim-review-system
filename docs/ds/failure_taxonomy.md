# Failure Taxonomy

**Status:** Complete failure catalog for multimodal claim review  
**Aligns with:** [architecture_v2.md](../architecture_v2.md) §6, [failure_taxonomy.md](failure_taxonomy.md) → synthetic fixtures  
**Companion:** [synthetic_generation_strategy.md](../synthetic_generation_strategy.md)

---

## Taxonomy Overview

```text
Observation failures     → CLAIM_EXTRACTION, ONTOLOGY, VISION
Reconciliation failures  → VALIDATION, CONSISTENCY
Decision failures        → VERDICT, SEVERITY, SUPPORTED_IMAGE_SELECTION
Post-decision failures   → RISK_DETECTION
```

Each class maps to a module, detection method, and synthetic fixture path (to be materialized under `code/synthetic/fixtures/` during implementation).

---

## CLAIM_EXTRACTION_FAILURE

### Definition

Gemini Flash or post-processing fails to produce a correct `ClaimObservation` from `user_claim` chat. Alleged parts, issue types, identity constraints, or severity language are wrong or missing.

### Causes

- Multilingual chat (Hindi, Spanish) misread
- Multi-part claim: only first part extracted
- Agent suggestions mistaken for customer affirmation
- `claimed_severity_language` not detected for CS-R06 cases
- Prompt injection conflated with legitimate claim text

### Detection Method

| Signal | Check |
|--------|-------|
| `extraction_score` | `alleged_parts` ≠ gold; `alleged_issue_families` mismatch |
| Row-level | `user_005` exaggeration language missed → wrong CS path |
| Language slice | Hindi rows `user_002`, `user_030` part extraction |

### Mitigation

- Versioned Flash prompts with ontology examples per `claim_object`
- Adversarial sanitizer strips injection before extraction
- `last_customer_message_excerpt` for MP tie-break audit

### Evaluation Coverage

- `evaluation_metrics.md` → Claim Observation engine metrics
- Per-language slice on sample + synthetic multilingual fixtures

### Synthetic Test Coverage

| Fixture category | Path (planned) |
|------------------|----------------|
| Hindi car claim | `synthetic/fixtures/observations/lang_hindi_car.json` |
| Spanish package claim | `synthetic/fixtures/observations/lang_spanish_pkg.json` |
| Prompt injection chat | `synthetic/fixtures/adversarial/chat_injection.json` |
| Multi-part affirmation | `synthetic/fixtures/multi_part/two_part_car.json` |

**Sample anchor:** `user_002` (Hindi), `user_030` (Hindi)

---

## ONTOLOGY_FAILURE

### Definition

Model output or normalization produces invalid enum values, or maps valid concepts to wrong ontology tokens.

### Causes

- Free-text issue ("shattered") not mapped to `crack`
- Part name outside allowed set for `claim_object`
- Invented issue types not in closed vocabulary
- `glass_shatter` vs `crack` confusion (HR-13)

### Detection Method

| Signal | Check |
|--------|-------|
| Pydantic validation | Contract reject on invalid enum |
| `ontology/normalize.py` | Fallback to `unknown` count |
| Label compare | `issue_type` not in allowed set for object |

### Mitigation

- Closed vocabulary in prompts
- `normalize.py` maps synonyms; unknown → `unknown` enum
- Never pass raw model strings to rules

### Evaluation Coverage

- `tests/ontology/` — enum rejection
- Count of `unknown` fallbacks per run

### Synthetic Test Coverage

| Fixture category | Path (planned) |
|------------------|----------------|
| Shatter → crack | `synthetic/fixtures/ontology/shatter_to_crack.json` |
| Invalid part for object | `synthetic/fixtures/ontology/invalid_part_laptop.json` |
| Synonym mapping | `synthetic/fixtures/ontology/scrape_to_scratch.json` |

**Sample anchor:** `user_018` (shattered → crack)

---

## VISION_FAILURE

### Definition

Gemini Pro produces incorrect `ImageEvidence` — wrong part visibility, damage extent, blur flags, or authenticity signals.

### Causes

- Hallucinated damage not visible
- Missed blur, glare, or obstruction
- False negative on `is_non_original_image`
- Wrong `visible_part` attribution
- `claimed_primary_part_visible` wrong before/after pass-2

### Detection Method

| Signal | Check |
|--------|-------|
| Per-field F1 | `visible_issue_type`, `visible_damage_extent`, `is_blurry` vs gold observations |
| Downstream | ESM false when images are actually clear (`user_003` risk) |
| Flag detection | `non_original_image` missed on `user_008` pattern |

### Mitigation

- Structured JSON schema in vision prompt
- Pass-2 rescoring for `claimed_primary_part_visible`
- Confidence gates: low confidence → no positive damage assertion

### Evaluation Coverage

- Image Observation engine metrics in evaluation_metrics.md
- Per-object-type vision F1 slices

### Synthetic Test Coverage

| Fixture category | Path (planned) |
|------------------|----------------|
| Blur + clear pair | `synthetic/fixtures/observations/user_003_pattern.json` |
| Non-original screenshot | `synthetic/fixtures/observations/user_008_pattern.json` |
| Wrong angle | `synthetic/fixtures/observations/user_006_pattern.json` |
| Low-confidence damage | `synthetic/fixtures/edge_cases/low_conf_damage.json` |

**Sample anchors:** `user_003`, `user_006`, `user_008`

---

## VALIDATION_FAILURE

### Definition

`SufficiencyEngine` or `TrustEngine` produces wrong `evidence_standard_met` or `valid_image`.

### Causes

- ESM-R02 identity conflict not triggered
- ESM-R03 no-part-visible not triggered when headlight absent
- Confusing ESM with `valid_image` (HR-06 violation)
- Contents claim without opened package (ESM-R04)

### Detection Method

| Signal | Check |
|--------|-------|
| `reconciliation_score` | ESM + valid_image match per row |
| HR invariants | HR-01, HR-06 automated checks |
| Rule ID | `evidence_standard_met_reason` template key wrong |

### Mitigation

- Pure predicate functions in `rules/sufficiency.py`, `rules/trust.py`
- Unit tests per ESM-R01..R08, VI-R01..R04

### Evaluation Coverage

- Reconciliation engine metrics
- `evaluation/invariants.py` HR-01, HR-06

### Synthetic Test Coverage

| Fixture category | Path (planned) |
|------------------|----------------|
| Identity conflict NEI | `synthetic/fixtures/decision_contexts/reconciliation/user_002.json` |
| Part not visible | `synthetic/fixtures/decision_contexts/reconciliation/user_006.json` |
| Contents not shown | `synthetic/fixtures/decision_contexts/reconciliation/user_032.json` |
| Blur compensated | `synthetic/fixtures/decision_contexts/reconciliation/user_003.json` |

**Sample anchors:** `user_002`, `user_006`, `user_032`, `user_003`

---

## CONSISTENCY_FAILURE

### Definition

`ConsistencyEngine` misses cross-image contradictions or incorrectly sets identity predicates.

### Causes

- `IDENTITY_CONFLICT` false negative on mismatched cars
- `vehicle_identity_features` incompatible but not flagged
- `WRONG_OBJECT_SET` not computed across images

### Detection Method

| Signal | Check |
|--------|-------|
| `IDENTITY_CONFLICT` predicate | Must be true on `user_002` |
| Downstream | ESM should be false when conflict true |
| Multi-image slice | accuracy on 2-image car rows |

### Mitigation

- Explicit cross-image comparison in `rules/consistency.py`
- Require confidence ≥ medium on both images for conflict

### Evaluation Coverage

- Consistency engine recall on `user_002`
- Synthetic identity augmentation set

### Synthetic Test Coverage

| Fixture category | Path (planned) |
|------------------|----------------|
| Two different cars | `synthetic/fixtures/decision_contexts/consistency/identity_conflict.json` |
| Consistent pair | `synthetic/fixtures/decision_contexts/consistency/consistent_pair.json` |

**Sample anchor:** `user_002`

---

## VERDICT_FAILURE

### Definition

`ClaimDecisionEngine` produces wrong `claim_status`, `issue_type`, or `object_part`.

### Causes

- NEI vs contradicted swap (CS-R01 vs CS-R03..R06)
- Visible ontology uses claimed not visible part (HR-08 violation)
- CS-R06 exaggeration not triggered
- CS-R08 fallback NEI when evidence exists

### Detection Method

| Signal | Check |
|--------|-------|
| `verdict_score` | status + issue_type + object_part |
| Confusion matrix | NEI ↔ contradicted swaps |
| HR-01, HR-02 | Invariant violations |

### Mitigation

- Strict decision_matrix evaluation order
- Confidence gates §8 before asserting supported/contradicted

### Evaluation Coverage

- Verdict engine metrics (40% weight component)
- Per-status recall slices

### Synthetic Test Coverage

| Fixture category | Path (planned) |
|------------------|----------------|
| Exaggeration | `synthetic/fixtures/decision_contexts/verdict/exaggeration.json` |
| Part mismatch | `synthetic/fixtures/decision_contexts/verdict/part_mismatch.json` |
| Absent damage | `synthetic/fixtures/decision_contexts/verdict/absent_damage.json` |
| Wrong object | `synthetic/fixtures/decision_contexts/verdict/wrong_object.json` |

**Sample anchors:** `user_005`, `user_008`, `user_020`, `user_033`, `user_034`

---

## SEVERITY_FAILURE

### Definition

`SeverityEngine` assigns wrong `severity` tier given verdict and visible damage extent.

### Causes

- Using claim text instead of visible extent (HR-07 violation)
- NEI row not `unknown` (HR-03 violation)
- `issue_type=none` not mapped to `severity=none`
- Supported row defaulting wrong tier (HR-12)

### Detection Method

| Signal | Check |
|--------|-------|
| `severity_score` | Exact match |
| HR-03 | Automated invariant |
| `user_005` | Must be `low` not medium/high |

### Mitigation

- SeverityEngine reads only `ImageEvidence.visible_damage_extent` + `VerdictDecision`
- Block `claimed_severity_language` in severity module imports

### Evaluation Coverage

- Severity engine metrics (10% weight)
- SV-R01..R08 unit tests

### Synthetic Test Coverage

| Fixture category | Path (planned) |
|------------------|----------------|
| NEI → unknown | `synthetic/fixtures/decision_contexts/severity/nei_unknown.json` |
| None damage | `synthetic/fixtures/decision_contexts/severity/issue_none.json` |
| Low visible | `synthetic/fixtures/decision_contexts/severity/exaggeration_low.json` |
| High visible | `synthetic/fixtures/decision_contexts/severity/severe_damage.json` |

**Sample anchors:** `user_002`, `user_005`, `user_008`, `user_020`, `user_034`

---

## SUPPORTED_IMAGE_SELECTION_FAILURE

### Definition

`SupportingImageSelector` returns wrong `supporting_image_ids` set.

### Causes

- Blurry image included when clear alternative exists
- NEI row lists images when should be `none` (HR-09)
- Identity conflict fails to list all images (SI-R01)
- Contradiction image not identified (SI-R05..R07)

### Detection Method

| Signal | Check |
|--------|-------|
| `supporting_score` | Exact set match (order-independent) |
| `user_003` | Must be `{img_2}` only |
| `user_002` | Must be `{img_1, img_2}` |

### Mitigation

- SI-R exclusion rules §5.2 before finalize
- Verdict-dependent rule table §5.1

### Evaluation Coverage

- Supporting engine metrics (5% weight)
- Set equality with semicolon normalization

### Synthetic Test Coverage

| Fixture category | Path (planned) |
|------------------|----------------|
| Blur exclude | `synthetic/fixtures/decision_contexts/supporting/blur_exclude.json` |
| Identity all images | `synthetic/fixtures/decision_contexts/supporting/identity_conflict.json` |
| NEI none | `synthetic/fixtures/decision_contexts/supporting/nei_none.json` |
| Multi-angle contradiction | `synthetic/fixtures/decision_contexts/supporting/seal_both_angles.json` |

**Sample anchors:** `user_002`, `user_003`, `user_006`, `user_034`

---

## RISK_DETECTION_FAILURE

### Definition

`AssessRisk` produces wrong `risk_flags` set — missing flags, spurious flags, or history propagation errors.

### Causes

- HR-04: `user_history_risk` not propagated from history
- HR-05: history incorrectly influences verdict (forbidden — cross-module)
- MRR composite incomplete (HR-10)
- `claim_mismatch` vs `damage_not_visible` wrong choice (HR-11)
- Image-quality flags missed at medium confidence

### Detection Method

| Signal | Check |
|--------|-------|
| `risk_flags_F1_macro` | Per-flag precision/recall |
| HR-04, HR-05 | Invariant tests |
| Exact set | 9 non-none rows in sample |

### Mitigation

- Evaluate all flag rules; collect all matches; sort alphabetically
- Risk module after compose; read-only on verdict

### Evaluation Coverage

- Risk engine metrics (15% weight)
- Per-flag slice table

### Synthetic Test Coverage

| Fixture category | Path (planned) |
|------------------|----------------|
| History UHR only | `synthetic/fixtures/decision_contexts/risk/history_uhr.json` |
| Non-original | `synthetic/fixtures/decision_contexts/risk/non_original.json` |
| Instruction text | `synthetic/fixtures/decision_contexts/risk/text_instruction.json` |
| Wrong object flag | `synthetic/fixtures/decision_contexts/risk/wrong_object.json` |

**Sample anchors:** `user_005`, `user_008`, `user_020`, `user_031`, `user_034`

---

## Failure Class → Module → Fixture Matrix

| Failure class | Module | Min fixtures | Sample row |
|---------------|--------|--------------|------------|
| CLAIM_EXTRACTION_FAILURE | M2a ClaimObserver | 4 | user_002, user_030 |
| ONTOLOGY_FAILURE | ontology/normalize | 3 | user_018 |
| VISION_FAILURE | M2b ImageObserver | 4 | user_003, user_006, user_008 |
| VALIDATION_FAILURE | M5b/M5c | 4 | user_002, user_006, user_032 |
| CONSISTENCY_FAILURE | M5a | 2 | user_002 |
| VERDICT_FAILURE | M7a | 4 | user_005, user_008, user_020, user_033 |
| SEVERITY_FAILURE | M7b | 4 | user_005, user_008, user_020 |
| SUPPORTED_IMAGE_SELECTION_FAILURE | M7c | 4 | user_002, user_003, user_034 |
| RISK_DETECTION_FAILURE | M9 | 4 | user_008, user_020, user_031 |

**Gate requirement:** ≥1 fixture per class before competition-grade submission (architecture_v2 §4.2).

---

## Cross-Reference

| Document | Role |
|----------|------|
| [hidden_business_rules.md](hidden_business_rules.md) | Rules that prevent failures |
| [hypotheses.md](hypotheses.md) | Experiments targeting failure classes |
| [synthetic_generation_strategy.md](../synthetic_generation_strategy.md) | Category definitions |
