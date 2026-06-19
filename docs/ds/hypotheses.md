# Hypotheses — Experimentation Framework

**Status:** Pre-implementation experimentation design  
**Rule:** No implementation. Each entry defines how a future change would be validated.  
**Companion:** [evaluation_metrics.md](../evaluation_metrics.md), [failure_taxonomy.md](failure_taxonomy.md)

---

## Conventions

| Field | Meaning |
|-------|---------|
| **H-ID** | Unique hypothesis identifier |
| **H0** | Null hypothesis — change has no measurable benefit |
| **H1** | Alternative hypothesis — change improves target metric |
| **Validation** | Dataset and method |
| **Acceptance** | Minimum threshold to adopt change |

All experiments run on `sample_claims.csv` (n=20) plus synthetic fixtures per [synthetic_generation_strategy.md](../synthetic_generation_strategy.md). Never tune on `claims.csv` labels.

---

## Observation Layer

### H-01 — Improved Flash extraction prompt

| Field | Value |
|-------|-------|
| **H-ID** | H-01 |
| **H0** | Prompt v2 does not improve `extraction_score` vs prompt v1 |
| **H1** | Prompt v2 increases mean `extraction_score` by ≥0.05 on sample + synthetic multilingual fixtures |
| **Expected metric impact** | `extraction_score` ↑; downstream `verdict_score` may ↑ if parts/issues were wrong |
| **Validation** | A/B on same images: v1 vs v2 Flash; compare `ClaimObservation` fields to gold-derived expectations |
| **Acceptance** | Δ extraction_score ≥ 0.05 AND no regression on `verdict_score` > 0.02 |

---

### H-02 — Two-pass image analysis (pass 2 after resolution)

| Field | Value |
|-------|-------|
| **H-ID** | H-02 |
| **H0** | Pass-2 primary-part rescoring does not improve `object_part` or ESM accuracy |
| **H1** | Pass-2 improves multi-part synthetic fixture accuracy by ≥1 correct primary part selection |
| **Expected metric impact** | `reconciliation_score` ↑ on multi-part; marginal cost ↑ |
| **Validation** | Synthetic multi-part fixtures only; compare pass-1-only vs pass-1+2 |
| **Acceptance** | Multi-part fixture pass rate ≥ 80% with pass-2 vs < 60% without |

---

### H-03 — Confidence threshold tuning

| Field | Value |
|-------|-------|
| **H-ID** | H-03 |
| **H0** | Adjusting high/medium/low thresholds (decision_matrix §8) does not change weighted score |
| **H1** | Tuned thresholds improve NEI recall on low-confidence fixtures without increasing false NEI on supported rows |
| **Expected metric impact** | NEI recall ↑; `claim_status_acc` neutral or ↑ |
| **Validation** | Synthetic edge_cases + sample; sweep p thresholds {0.80, 0.85, 0.90} for high |
| **Acceptance** | NEI slice recall = 100% on sample; weighted score ≥ baseline |

---

### H-04 — Vision prompt structured JSON schema enforcement

| Field | Value |
|-------|-------|
| **H-ID** | H-04 |
| **H0** | Stricter JSON schema in Pro prompt does not reduce ontology violations |
| **H1** | Schema enforcement reduces `ONTOLOGY_FAILURE` rate on sample rows |
| **Expected metric impact** | `vision_field_F1` ↑; fewer normalize→unknown fallbacks |
| **Validation** | Count invalid enum mappings pre/post on sample image observations |
| **Acceptance** | Ontology failure count = 0 on sample replay |

---

## Reconciliation Layer

### H-05 — Blur exclusion in supporting image selection

| Field | Value |
|-------|-------|
| **H-ID** | H-05 |
| **H0** | SI-R04 blur exclusion already captured in baseline rules |
| **H1** | Explicit blur exclusion test catches regression if vision mislabels blur |
| **Expected metric impact** | `supporting_score` stable at 100% on sample |
| **Validation** | `user_003` fixture must select `img_2` only |
| **Acceptance** | `supporting_image_ids` exact match on user_003 |

---

### H-06 — Identity conflict predicate sensitivity

| Field | Value |
|-------|-------|
| **H-ID** | H-06 |
| **H0** | Loosening identity feature mismatch threshold does not change `user_002` outcome |
| **H1** | Tighter threshold increases identity conflict recall on synthetic car pairs |
| **Expected metric impact** | `reconciliation_score` on CONSISTENCY_FAILURE ↓ false negatives |
| **Validation** | `user_002` + synthetic identity augmentation set |
| **Acceptance** | `user_002` remains NEI + ESM false; synthetic conflict pairs detected ≥ 90% |

---

## Decision Layer

### H-07 — CS-R06 severity exaggeration threshold

| Field | Value |
|-------|-------|
| **H-ID** | H-07 |
| **H0** | `claimed_severity_language` extraction quality does not affect `user_005` verdict |
| **H1** | Improved Flash severity language extraction increases contradicted recall on exaggeration fixtures |
| **Expected metric impact** | `verdict_score` on exaggeration slice ↑ |
| **Validation** | `user_005` + synthetic exaggeration claims |
| **Acceptance** | `user_005` → contradicted; exaggeration fixture pass ≥ 80% |

---

### H-08 — SV-R07 default medium for unknown extent

| Field | Value |
|-------|-------|
| **H-ID** | H-08 |
| **H0** | Changing SV-R07 default does not affect supported rows with `visible_damage_extent=unknown` |
| **H1** | SV-R07 `medium` default matches HR-12 pattern on supported unknown-extent cases |
| **Expected metric impact** | `severity_score` ↑ on edge cases |
| **Validation** | Supported rows with unknown extent in synthetic set |
| **Acceptance** | No regression on sample severity; synthetic pass ≥ 75% |

---

## Risk Layer

### H-09 — MRR composite completeness

| Field | Value |
|-------|-------|
| **H-ID** | H-09 |
| **H0** | All MRR-1..MRR-6 sub-rules are already correctly encoded |
| **H1** | Missing any MRR sub-rule reduces `risk_flags_F1` on affected sample rows |
| **Validation** | Ablate each MRR sub-rule; compare to gold risk_flags |
| **Acceptance** | Macro-F1 = 1.0 on sample after full MRR implementation |

---

## Operational

### H-10 — Response caching by image hash

| Field | Value |
|-------|-------|
| **H-ID** | H-10 |
| **H0** | Caching does not change weighted score (determinism) |
| **H1** | Caching reduces cost ≥ 30% on second identical run with zero score delta |
| **Expected metric impact** | Cost ↓; weighted score unchanged |
| **Validation** | Two full sample runs with cache on; compare outputs and `deterministic_hash` |
| **Acceptance** | 100% row match; cost reduction documented |

---

### H-11 — Image resize to 1024px before Pro

| Field | Value |
|-------|-------|
| **H-ID** | H-11 |
| **H0** | Resizing does not change observation fields on sample |
| **H1** | Resizing reduces token cost ≥ 15% with weighted score drop ≤ 0.02 |
| **Validation** | Full sample A/B: original vs resized |
| **Acceptance** | Δ weighted score ≤ 0.02; cost savings documented |

---

## Process Hypotheses

### H-12 — Per-engine ablation before end-to-end tuning

| Field | Value |
|-------|-------|
| **H-ID** | H-12 |
| **H0** | End-to-end prompt tuning without per-engine isolation does not improve debuggability |
| **H1** | Fixing reconciliation layer first yields higher weighted score than tuning Flash alone |
| **Validation** | Compare iteration order: (A) Flash-first vs (B) rules-first with frozen gold observations |
| **Acceptance** | Document winning order for README; rules-first must reach 100% on frozen-observation sample |

---

## Hypothesis Log Template

When implementing any change, append to this file:

```text
## H-XX Result — [date]
Strategy: <id>
H0 rejected: yes/no
Weighted score: baseline X → new Y (Δ)
Decision: adopt / reject / defer
```

---

## Cross-Reference

| Document | Role |
|----------|------|
| [evaluation_metrics.md](../evaluation_metrics.md) | Metrics and thresholds |
| [architecture_v2.md](../architecture_v2.md) §4 | Data Scientist Mode gate |
| [synthetic_generation_strategy.md](../synthetic_generation_strategy.md) | Fixture categories for validation |
