# Evaluation Metrics

**Status:** SINGLE SOURCE OF TRUTH for all metrics, thresholds, and strategy comparison  
**Supersedes:** Informal weights in [architecture_review.md](architecture_review.md) §6  
**Aligns with:** [pydantic_contracts_v2.md](pydantic_contracts_v2.md) §16, [architecture_v2.md](architecture_v2.md) §6, [class_balance.md](ds/class_balance.md)

---

## 1. Per-Engine Metrics

Each engine is evaluated independently before end-to-end scoring. Use frozen observations for rule engines; live Gemini for observation engines.

### 1.1 Claim Observation (M2a — Gemini Flash)

| Metric | Definition | Match rule |
|--------|------------|------------|
| `alleged_parts_match` | Primary alleged part set equals gold | Set equality on customer-affirmed parts |
| `alleged_issue_family_match` | Primary issue family correct | Exact match on mapped family |
| `identity_constraint_match` | `identity_constraint_active.value` correct | Boolean match |
| `severity_language_match` | `claimed_severity_language` correct | Exact enum match (CS-R06 input) |
| `injection_detected_match` | Injection flag correct | Boolean match |
| `extraction_score` | Mean of above applicable fields | Float 0.0–1.0 |

**Primary metric:** `extraction_score`  
**Sample size caveat:** n=20; Hindi rows n=2

---

### 1.2 Image Observation (M2b — Gemini Pro)

| Metric | Definition | Match rule |
|--------|------------|------------|
| `part_visibility_acc` | `claimed_primary_part_visible` correct per image | Per-image boolean |
| `visible_part_acc` | `visible_part` correct | Exact enum per image |
| `visible_issue_acc` | `visible_issue_type` correct | Exact enum per image |
| `damage_extent_acc` | `visible_damage_extent` correct | Exact enum per image |
| `blur_flag_f1` | `is_blurry` F1 | Per-image boolean |
| `authenticity_flag_f1` | `is_non_original_image` + `has_instruction_text` F1 | Per-flag |
| `vision_field_F1` | Macro-F1 over all boolean observation flags | Per image, macro over flags |

**Primary metric:** `vision_field_F1`  
**Aggregation:** Mean over all images in evaluated rows

---

### 1.3 Evidence Sufficiency (M5b — SufficiencyEngine)

| Metric | Definition |
|--------|------------|
| `esm_acc` | `evidence_standard_met` exact match |
| `esm_nei_joint_acc` | P(NEI \| ESM=false) on sample — target 1.0 |
| `esm_rule_id_match` | Triggered ESM-R* matches gold trace (optional audit) |

**Primary metric:** `esm_acc`  
**Invariant:** HR-01 automated — `¬ESM ⟹ NEI`

---

### 1.4 Trust Assessment (M5c — TrustEngine)

| Metric | Definition |
|--------|------------|
| `valid_image_acc` | `valid_image` exact match |
| `esm_valid_orthogonality` | No spurious correlation enforced (HR-06) |

**Primary metric:** `valid_image_acc`  
**Sample positives for false:** n=2 (`user_008`, `user_032`)

---

### 1.5 Consistency (M5a — ConsistencyEngine)

| Metric | Definition |
|--------|------------|
| `identity_conflict_recall` | `IDENTITY_CONFLICT` true when gold expects conflict |
| `identity_conflict_precision` | No false conflicts on consistent pairs |
| `consistency_score` | (recall + precision) / 2 for identity predicate |

**Primary metric:** `identity_conflict_recall` on multi-image car rows  
**Sample anchor:** `user_002` must recall = 1.0

---

### 1.6 Verdict (M7a — ClaimDecisionEngine)

| Metric | Definition |
|--------|------------|
| `claim_status_acc` | `claim_status` exact match |
| `issue_type_acc` | `issue_type` exact match |
| `object_part_acc` | `object_part` exact match |
| `verdict_score` | `(claim_status_acc + issue_type_acc + object_part_acc) / 3` |

**Primary metric:** `claim_status_acc`  
**Secondary:** Per-status recall (supported, contradicted, NEI)

---

### 1.7 Severity (M7b — SeverityEngine)

| Metric | Definition |
|--------|------------|
| `severity_acc` | `severity` exact match |
| `nei_unknown_compliance` | HR-03: NEI → unknown (100% on sample) |
| `none_severity_compliance` | `issue_type=none` → `severity=none` |

**Primary metric:** `severity_acc`

---

### 1.8 Supporting Image Selection (M7c — SupportingImageSelector)

| Metric | Definition |
|--------|------------|
| `supporting_exact_match` | Predicted set = gold set (order-independent) |
| `supporting_score` | 1.0 if exact match else 0.0 per row |

**Primary metric:** `supporting_exact_match` rate  
**Normalization:** Split `;`, sort, compare sets; `none` = empty set

---

### 1.9 Risk Assessment (M9 — AssessRisk)

| Metric | Definition |
|--------|------------|
| `risk_flags_exact_match` | Full set equality per row |
| `risk_flags_f1_macro` | Macro-averaged F1 over all flag types |
| `uhr_propagation_acc` | HR-04: history UHR → output UHR |
| `verdict_independence` | HR-05: status unchanged when only history differs (fixture test) |

**Primary metric:** `risk_flags_f1_macro`

---

### 1.10 Reconciliation Composite

| Metric | Definition |
|--------|------------|
| `reconciliation_score` | `(esm_acc + valid_image_acc) / 2` | 

Used for M5 layer reporting; not in end-to-end weighted formula directly.

---

### 1.11 EngineScoreBundle (EvaluationRecord)

```text
engine_scores.verdict_score       = verdict_score
engine_scores.severity_score      = severity_acc (per row, aggregated mean)
engine_scores.supporting_score    = supporting_score (per row mean)
engine_scores.extraction_score    = extraction_score (optional)
engine_scores.reconciliation_score = reconciliation_score
engine_scores.weighted_total      = end-to-end Score (§2.3)
```

---

## 2. End-to-End Metrics

Computed on full pipeline output vs `sample_claims.csv` gold labels.

### 2.1 Field-Level Accuracy

| Metric | Definition |
|--------|------------|
| `field_acc` | Mean of per-column exact matches across 11 predicted label columns |
| `field_matches` | Map `column → bool` per row (EvaluationRecord) |

**Label columns evaluated:** `evidence_standard_met`, `risk_flags`, `issue_type`, `object_part`, `claim_status`, `supporting_image_ids`, `valid_image`, `severity`  
**Prose columns (separate):** `evidence_standard_met_reason`, `claim_status_justification` — grounding checklist only (§2.6)

---

### 2.2 Precision, Recall, F1 (claim_status)

Treat `claim_status` as 3-class classification:

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| supported | TP_s / pred_s | TP_s / gold_s | harmonic mean |
| contradicted | TP_c / pred_c | TP_c / gold_c | harmonic mean |
| not_enough_information | TP_n / pred_n | TP_n / gold_n | harmonic mean |

**Macro-F1:** Mean of three class F1 scores  
**Report:** Confusion matrix 3×3

---

### 2.3 Weighted Score (Primary Iteration Metric)

```text
Score = 0.40 × claim_status_acc
      + 0.20 × evidence_standard_met_acc
      + 0.15 × risk_flags_F1_macro
      + 0.10 × (issue_type_acc + object_part_acc) / 2
      + 0.10 × severity_acc
      + 0.05 × supporting_image_ids_exact_match
```

| Component | Weight | Rationale |
|-----------|--------|-----------|
| claim_status | 0.40 | Primary business outcome; 60% class imbalance |
| evidence_standard_met | 0.20 | Gates verdict; NEI path |
| risk_flags F1 | 0.15 | Sparse multi-label |
| issue_type + object_part | 0.10 | Visible ontology |
| severity | 0.10 | Derivative of vision + verdict |
| supporting_image_ids | 0.05 | Exact set; partially redundant with verdict |

**Range:** 0.0–1.0  
**Implementation:** `code/config/metrics_weights.yaml` (must match this document)

---

### 2.4 False Support Rate

```text
false_support_rate = FP_supported / (FP_supported + TN_supported)
```

Where **false support** = predicted `supported` but gold ≠ `supported`.

**Interpretation:** Safety metric — constitution "Evidence Overrides Claims"  
**Sample baseline:** To be measured on first pipeline run

---

### 2.5 False Contradiction Rate

```text
false_contradiction_rate = FP_contradicted / (FP_contradicted + TN_contradicted)
```

Where **false contradiction** = predicted `contradicted` but gold ≠ `contradicted`.

**Interpretation:** User harm metric — wrongly rejecting valid claims

---

### 2.6 Prose Grounding Checklist (Non-Exact Match)

For `evidence_standard_met_reason` and `claim_status_justification`:

| Check | Pass criterion |
|-------|----------------|
| Image citation | If `supporting_image_ids ≠ none`, prose mentions at least one ID |
| No history-only | If `user_history_risk` ∉ risk_flags, justification must not cite history as primary reason |
| No injection echo | Prose must not repeat adversarial instruction text |
| Factual tone | No LLM-generated verdict language ("I approve", "definitely") |

**Score:** `prose_grounding_pass_rate` = passing rows / total (qualitative; not in weighted Score)

---

### 2.7 Hidden Rule Invariant Suite

Run on every evaluation pass (`evaluation/invariants.py`):

| ID | Invariant |
|----|-----------|
| HR-01 | `¬ESM ⟹ status=NEI` |
| HR-02 | `status=contradicted ⟹ ESM=true` |
| HR-03 | `status=NEI ⟹ severity=unknown` |
| HR-04 | `history UHR ⟹ risk UHR` |
| HR-06 | No assertion ESM ↔ valid_image correlation |

**Pass:** 100% invariant satisfaction on sample

---

### 2.8 Trace Replay Determinism

| Metric | Definition |
|--------|------------|
| `trace_replay_match` | Re-run rules on frozen `DecisionTrace` observations → identical `deterministic_hash` |

**Target:** 100% on 20 sample rows with mock or live observations frozen

---

## 3. Slice Metrics

Always report alongside aggregate Score.

### 3.1 By claim_object

| Slice | Metrics reported |
|-------|------------------|
| car | claim_status_acc, weighted Score |
| laptop | claim_status_acc, weighted Score |
| package | claim_status_acc, weighted Score |

**Known gap:** No NEI laptop rows in sample — laptop NEI slice unavailable.

---

### 3.2 By language

| Slice | Rows | Metrics |
|-------|------|---------|
| English | 18 | extraction_score, claim_status_acc |
| Hindi | 2 | extraction_score, claim_status_acc |
| Spanish | 0 | N/A — use synthetic |

Detect via `ClaimObservation.detected_languages` or chat heuristic.

---

### 3.3 By image_count

| Slice | Metrics |
|-------|---------|
| 1 image | supporting_exact_match, claim_status_acc |
| 2+ images | identity_conflict_recall, supporting_exact_match |

---

### 3.4 By claim_status (gold)

| Slice | Metrics |
|-------|---------|
| supported (n=12) | severity_acc, false_support_rate |
| contradicted (n=5) | issue_type_acc, false_contradiction_rate |
| NEI (n=3) | esm_acc, supporting_exact_match |

---

### 3.5 By risk category

| Slice | Definition | Metrics |
|-------|------------|---------|
| has_risk_flags | any flag ≠ none | risk_flags_f1_macro |
| no_risk_flags | none only | spurious flag rate |
| has_UHR | user_history_risk | uhr_propagation_acc |
| has_MRR | manual_review_required | MRR rule coverage |

---

## 4. Evaluation Thresholds

### 4.1 Minimum Acceptable Scores (sample_claims.csv)

| Metric | Minimum | Phase |
|--------|---------|-------|
| Weighted Score | ≥ 0.85 | MVP (mock observations) |
| Weighted Score | ≥ 0.90 | Competition submission |
| claim_status_acc | ≥ 0.85 | MVP |
| claim_status_acc | ≥ 0.90 | Competition |
| HR invariant suite | 100% | Always |
| trace_replay_match | 100% | Competition |
| esm_acc | ≥ 0.95 | MVP |
| valid_image_acc | ≥ 0.95 | MVP |
| risk_flags_f1_macro | ≥ 0.80 | Competition |

---

### 4.2 Warning Thresholds

Trigger review but do not block submission:

| Condition | Action |
|-----------|--------|
| Weighted Score drops ≥ 0.03 from prior strategy | Require hypothesis log entry |
| NEI recall < 1.0 on sample | Review ESM + verdict rules |
| false_support_rate > 0.0 | Safety review — constitution violation |
| extraction_score < 0.80 on Hindi slice | Flash prompt iteration |

---

### 4.3 Regression Thresholds (CI)

| Check | Threshold |
|-------|-----------|
| Weighted Score vs frozen baseline | Δ ≥ −0.02 |
| Per-engine verdict_score | Δ ≥ −0.05 |
| HR invariants | 0 failures |
| Schema validation | 100% output rows valid |

Baseline file: `code/evaluation/baselines/sample_baseline.json` (created at first green run)

---

## 5. Strategy Comparison Rules

### 5.1 A/B Protocol

1. Run strategy A and B on identical `sample_claims.csv` rows
2. Record `EvaluationRecord` per row per `strategy_id`
3. Aggregate Weighted Score, per-engine scores, operational metrics
4. Document in `evaluation/evaluation_report.md`

**Minimum:** 2 strategies (e.g. `prompt-v1` vs `prompt-v2`)

---

### 5.2 Winner Selection

| Step | Rule |
|------|------|
| 1 | Higher Weighted Score wins |
| 2 | If Δ Score < **0.02** → **cost-aware tie-break** (§5.3) |
| 3 | If still tied → prefer fewer model calls |
| 4 | If still tied → prefer strategy with higher NEI recall |

**No p-values required** (n=20 too small for statistical significance).

---

### 5.3 Cost-Aware Tie-Break

When |Score_A − Score_B| < 0.02:

```text
winner = argmin(estimated_cost_usd)
```

Report both scores as "statistically equivalent" in evaluation report.

**Cost model:**

```text
calls_flash = num_rows
calls_pro   = num_images + num_multi_part_rows  # pass-2
cost_usd    = calls_flash × flash_unit_cost + token_pro_total × pro_unit_cost
```

Document pricing assumptions in evaluation report.

---

### 5.4 Regression Guard for Strategy Promotion

A strategy replaces production only if:

1. Weighted Score ≥ incumbent − 0.02
2. false_support_rate ≤ incumbent
3. HR invariants 100%
4. No regression > 0.05 on any single engine sub-score

---

## 6. Operational Metrics (Evaluation Report)

Required in `code/evaluation/evaluation_report.md` per problem_decomposition §9:

| Metric | Source |
|--------|--------|
| Total model calls (Flash + Pro) | RunManifest / pipeline counters |
| Input / output tokens | Provider telemetry |
| Images processed | Sum of image_count |
| Wall-clock latency | Batch runner timer |
| Estimated cost USD | Cost model §5.3 |
| TPM/RPM strategy | operations.md (when available) |
| Cache hit rate | providers/cache.py |

---

## 7. Implementation Mapping

| Spec section | Code path |
|--------------|-----------|
| Weighted Score | `code/evaluation/metrics.py` |
| Weights config | `code/config/metrics_weights.yaml` |
| Strategy compare | `code/evaluation/compare_strategies.py` |
| Invariants | `code/evaluation/invariants.py` |
| Runner | `code/evaluation/runner.py` |
| Entry point | `code/evaluation/main.py` |

---

## Cross-Reference

| Document | Role |
|----------|------|
| [class_balance.md](ds/class_balance.md) | Imbalance justification for weights |
| [failure_taxonomy.md](ds/failure_taxonomy.md) | Per-engine failure classes |
| [hypotheses.md](ds/hypotheses.md) | Experiment acceptance criteria |
| [architecture_gate_review.md](architecture_gate_review.md) | Gate that required this document |
