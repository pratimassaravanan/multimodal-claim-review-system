# Architecture Gate Review

**Date:** 2026-06-19  
**Reviewers:** Principal AI Architect · Principal Data Scientist · Technical Judge  
**Artifacts reviewed:** [architecture_v2.md](architecture_v2.md), [pydantic_contracts_v2.md](pydantic_contracts_v2.md), [project_structure.md](project_structure.md), [decision_matrix.md](decision_matrix.md)  
**Status:** Final pre-implementation gate

---

## Executive Summary

Architecture v2 is **structurally sound**: module boundaries, contract handoffs, execution order, and constitution alignment (`Models Observe. Rules Decide.`) are coherent and implementable. `project_structure.md` maps modules to contracts and separates concerns correctly.

The gate **does not pass** on companion specifications required by architecture v2 §4 and §8. Critical gaps are concentrated in **evaluation metric definition**, **Data Scientist Mode artifacts**, **synthetic fixture design**, and **operational failure handling** — not in core pipeline topology.

**Verdict:** **CHANGES REQUIRED** (documentation and spec amendments only; no architecture v2 redesign).

---

## 1. Review Scope and Method

| Lens | Question asked |
|------|----------------|
| **Principal AI Architect** | Are modules, contracts, and execution order complete and non-contradictory? |
| **Principal Data Scientist** | Can we measure, compare strategies, and validate hidden rules on n=20? |
| **Technical Judge** | Can the team defend choices in interview and produce a submission-grade eval report? |

**In scope:** Design documents listed above.  
**Out of scope:** Implementation code, runtime performance of Gemini, final prompt content.

---

## 2. What Passes (No Change Required)

| Area | Assessment |
|------|------------|
| **Module topology** | M1–M11 + offline M12/M13 are complete; three decision engines correctly split. |
| **Execution order** | Matches `decision_matrix.md` normative order; hard constraints documented. |
| **Contract graph** | v2 dependency matrix is acyclic; observation vs decision separation enforced. |
| **Multi-part policy** | MP-1..MP-5 + two-pass image observation are specified. |
| **Repository layout** | `project_structure.md` separates orchestration, contracts, providers, prompts, ontology, rules, evaluation, synthetic, testing. |
| **AGENTS.md compliance** | Entry points (`code/main.py`, `code/evaluation/main.py`), `output.csv`, env-var secrets mapped. |
| **Hidden rules in decision matrix** | HR-01..HR-08 encoded in `decision_matrix.md` §9. |
| **Anti-patterns** | Documented in architecture v2, contracts v2, and project structure. |
| **MVP vs competition path** | Phased implementation and test order are actionable. |

---

## 3. Gap Analysis

Severity scale: **Critical** (blocks implementation gate) · **High** (blocks submission quality) · **Medium** (degrades iteration speed) · **Low** (nice-to-have)

Implementation cost: **S** (&lt;2h doc/spec) · **M** (2–8h design + fixtures) · **L** (8h+ implementation)

---

### 3.1 Missing Evaluation Capabilities

| ID | Gap | Severity | Rationale | Cost | Recommendation |
|----|-----|----------|-----------|------|----------------|
| **E-01** | **Weighted scoring formula not in canonical v2 docs** | Critical | `pydantic_contracts_v2.md` references `architecture_v2 §6 weights` but §6 lists per-module metrics, not numeric weights. Formula exists only in `architecture_review.md` §6. Eval harness cannot be normative without a single source of truth. | S | Add `docs/evaluation_metrics.md` (or § in `project_structure.md`) promoting the v1 formula and defining per-engine `EngineScoreBundle` weights. |
| **E-02** | **`docs/ds/` artifacts missing** | Critical | architecture_v2 §4.2 gate requires `label_analysis.md`, `hidden_business_rules.md`, `hypotheses.md`, `class_balance.md`, `failure_taxonomy.md`. Folder does not exist. Data Scientist Mode gate cannot pass. | M | Create all five files before P0 implementation. Minimum: `hidden_business_rules.md` + `class_balance.md` with weights. |
| **E-03** | **No reconciliation-layer eval plan** | High | architecture_v2 §6 defines ESM, `valid_image`, consistency metrics but `evaluation/metrics.py` only generically references per-engine scores. No spec for evaluating M5a–M5c independently before verdict engines. | S | Extend `evaluation_metrics.md` with M5 slice metrics and pass/fail thresholds on sample. |
| **E-04** | **No observation-layer eval harness design** | High | `ClaimObservation` and `ImageEvidence` are first-class for independent evaluation (architecture_v2 §2.1) but no fixture format, field-level match rules, or F1 definitions exist. | M | Add `code/synthetic/fixtures/observations/README.md` + eval functions in `evaluation/metrics.py` spec: part match, issue family match, per-image flag F1. |
| **E-05** | **Failure taxonomy → test fixture mapping absent** | High | Gate criterion: ≥1 fixture per failure class. `failure_taxonomy.md` missing; `synthetic/fixtures/decision_contexts/` is named but unpopulated and unschema'd. | M | Define failure classes in `docs/ds/failure_taxonomy.md`; map each to a JSON fixture path. |
| **E-06** | **Trace replay determinism eval unspecified** | Medium | `DecisionTrace.deterministic_hash` exists; no requirement that replaying observations + rules reproduces identical output. Judge cannot verify "Rules Decide" reproducibility. | M | Add eval step E1.5: `evaluation/replay.py` spec — hash match on 20 sample traces. |
| **E-07** | **No confusion matrix / slice reporting** | Medium | n=20 with 12/5/3 status imbalance; naive accuracy misleading. `class_balance.md` required but no report format for per-status, per-object-type, per-language slices. | S | Specify slice dimensions in `evaluation_metrics.md`; `evaluation/runner.py` emits CSV/MD tables. |
| **E-08** | **Prose field evaluation undefined** | Medium | `evidence_standard_met_reason` and `claim_status_justification` are output columns. No rule for exact match vs keyword grounding vs qualitative review. | S | Document: exact match not required; automated **grounding checklist** (cites image ID, no history-only for non-UHR rows) per architecture_review L12. |
| **E-09** | **HR compliance tests not in eval harness** | Medium | HR-01..HR-08 are in decision_matrix §9 but no automated invariant checks (e.g. ∀ rows: ¬ESM ⟹ NEI). | S | Add `evaluation/invariants.py` spec — run on every eval pass. |
| **E-10** | **Strategy comparison contract incomplete** | Medium | `compare_strategies.py` named; no spec for statistical significance on n=20, minimum delta to declare winner, or tie-break policy. | S | Document: winner = higher weighted score; if Δ &lt; 0.02, prefer lower cost strategy; no p-values required. |
| **E-11** | **EvaluationRecord v2 drops v1 operational fields** | Low | v1 includes `latency_ms`, `token_input`, `token_output`, `model_calls` per row; v2 changelog omits explicit retention. Operational report may lose row-level attribution. | S | Amend `pydantic_contracts_v2.md` §16 to retain v1 operational optional fields on `EvaluationRecord`. |
| **E-12** | **No `evaluation/metrics_weights.yaml` in project structure** | Low | Weights hardcoded in code risks drift from docs. | S | Add `code/config/metrics_weights.yaml`; load in `evaluation/metrics.py`. |

**Recommended end-to-end score (promote to canonical):**

```text
Score = 0.40 × claim_status_acc
      + 0.20 × evidence_standard_met_acc
      + 0.15 × risk_flags_F1_macro
      + 0.10 × (issue_type_acc + object_part_acc) / 2
      + 0.10 × severity_acc
      + 0.05 × supporting_image_ids_exact_match
```

**Per-engine sub-scores (for `EngineScoreBundle`):**

| Engine | Sub-score | Components |
|--------|-----------|------------|
| Verdict | `verdict_score` | `claim_status` + `issue_type` + `object_part` (equal thirds) |
| Severity | `severity_score` | `severity` exact match |
| Supporting | `supporting_score` | Set equality |
| Extraction | `extraction_score` | `alleged_parts` + primary issue family (optional) |
| Reconciliation | `reconciliation_score` | `evidence_standard_met` + `valid_image` (equal) |

`weighted_total` = end-to-end score above; engine sub-scores for debugging only unless ablation study needs them.

---

### 3.2 Missing Synthetic Data Capabilities

| ID | Gap | Severity | Rationale | Cost | Recommendation |
|----|-----|----------|-----------|------|----------------|
| **S-01** | **No multi-part synthetic rows with expected outputs** | Critical | Test set has multi-part claims (`case_001`, `case_019`, `case_040`); sample set is single-part. MP policy untestable without synthetic rows. | M | Add `synthetic/fixtures/multi_part/` with ≥3 rows: visibility tie-break, last-mention tie-break, single-part control. |
| **S-02** | **No adversarial / injection fixture catalog** | High | Failure modes include chat injection (`case_055`) and in-image instructions. No frozen `ClaimObservation` + expected sanitizer behavior. | M | Add `synthetic/fixtures/adversarial/` — injection stripped, `injection_detected_in_chat=true`, verdict unchanged by injection text. |
| **S-03** | **No observation JSON schema for fixtures** | High | `synthetic/fixtures/observations/` named but no schema, versioning, or link to `ClaimObservation` / `ImageEvidence` contracts. | S | Add `synthetic/schemas/observation_bundle.schema.json` + README with naming `{row_id}.json`. |
| **S-04** | **No multilingual synthetic claims** | Medium | Only 2 Hindi sample rows; extraction errors are a top failure mode. Cannot test Flash without live API. | M | Add 2–3 synthetic chat transcripts (Hindi, Spanish, EN+Hindi) with expected `alleged_parts` / `alleged_issue_types`. |
| **S-05** | **No identity-conflict augmentation set** | Medium | `user_002` is sole positive; regression risk if vision changes. | S | Clone `user_002` observation with perturbed identity features → expect ESM-R02, SI-R01. |
| **S-06** | **`generate_fixtures.py` spec only** | Medium | Deferred in MVP; without generator spec, fixtures drift from decision_matrix rule IDs. | M | Document generator inputs: rule ID, predicate overrides, expected `VerdictDecision` — even if hand-authored initially. |
| **S-07** | **No observation corruption / robustness suite** | Medium | Rules assume confidence thresholds; no fixtures for low-confidence-only observations forcing CS-R08 / NEI. | M | Add `synthetic/fixtures/edge_cases/`: `user_006`-like (no part visible), low-confidence damage, `user_003`-like blur+clear. |
| **S-08** | **No DecisionContext fixtures per failure class** | High | architecture_v2 §4.2 requires ≥1 fixture per failure class per engine. Directory empty. | M | Populate `synthetic/fixtures/decision_contexts/{verdict,severity,supporting,reconciliation}/` — minimum 8 files aligned to `failure_taxonomy.md`. |
| **S-09** | **No fixture sync with sample golden traces** | Low | `tests/golden/sample_rows/` planned; no spec that golden trace ⊇ `DecisionTrace` contract v2. | S | One JSON trace per sample `user_id`; generated from mock observations matching sample labels. |

---

### 3.3 Missing Operational Capabilities

| ID | Gap | Severity | Rationale | Cost | Recommendation |
|----|-----|----------|-----------|------|----------------|
| **O-01** | **No API failure / degradation policy** | Critical | 44 test rows × multiple images × Pro calls = high API exposure. No spec for retry, fallback to `unknown` observations, or fail-fast vs partial output. | M | Add `docs/operations.md`: 3 retries with backoff; on persistent failure emit row with `claim_status=not_enough_information`, log error, continue batch. |
| **O-02** | **No `RunManifest` / telemetry contract** | High | problem_decomposition §9 requires model calls, tokens, latency in eval report. No structured aggregate contract — only optional fields on `EvaluationRecord`. | M | Add `contracts/telemetry.py`: `RunManifest` (total_calls, tokens, cost_estimate, wall_time, errors, pipeline_version). |
| **O-03** | **No pre-flight validation** | High | Missing images, malformed CSV, or invalid enums could fail mid-batch. | S | `orchestration/pipeline.py` validates `ClaimContext` before any Gemini call; collect all intake errors upfront. |
| **O-04** | **No output schema validator before write** | Medium | Unevaluable submission if column order or enum drifts. | S | `modules/emit.py` validates against `OutputRowSnapshot` + 14-column order; fail CI if invalid. |
| **O-05** | **Trace storage gitignored by default** | Medium | `.traces/` gitignored aids repo size but loses audit trail for judge unless eval report embeds summaries. | S | Write per-row trace summary to `evaluation/traces_summary.json` (committed in report run, not full images). |
| **O-06** | **No rules-only / dry-run CLI mode** | Medium | Developers need `main.py --mode=rules --fixtures=synthetic/` without API key for CI. | S | Document in `code/README.md` and `config/pipeline.yaml` feature flag `provider=mock`. |
| **O-07** | **No structured logging schema** | Medium | Debugging 44 rows requires row_id-stamped logs; not in project structure. | S | Add `config/logging.yaml`; standard fields: `row_id`, `stage`, `rule_id`, `duration_ms`. |
| **O-08** | **No `.env.example`** | Low | AGENTS.md requires env vars; onboarding friction. | S | Add `code/.env.example` with `GEMINI_API_KEY`, paths, optional cache dir. |
| **O-09** | **No batch resume / checkpoint** | Low | Long runs interrupted lose progress. Acceptable for hackathon if batch &lt;30 min. | L | Optional `orchestration/checkpoint.py` — defer to competition-grade unless runtime exceeds 45 min. |

---

### 3.4 Missing Cost Optimization Capabilities

| ID | Gap | Severity | Rationale | Cost | Recommendation |
|----|-----|----------|-----------|------|----------------|
| **C-01** | **No image preprocessing policy** | High | Pro per-image is dominant cost. No max dimension, format normalization, or skip-if-unreadable rules. | S | Add to `operations.md`: resize to max 1024px long edge; JPEG re-encode; skip corrupt files with `file_readable=false`. |
| **C-02** | **No cost budget / kill switch** | Medium | Unbounded spend on test rerun during iteration. | S | `config/pipeline.yaml`: `max_cost_usd`, `max_calls_per_run`; provider checks before each call. |
| **C-03** | **Cache key and invalidation policy undefined** | Medium | `providers/cache.py` named; key = hash + prompt version stated but no TTL, no invalidation on ontology change. | S | Key = `sha256(image_bytes) + prompt_version + model_name`; invalidate on `pipeline_version` bump. |
| **C-04** | **Pass-2 vision cost not bounded** | Medium | architecture_v2 §5.3 allows pass-2 re-score only for primary part — good — but no spec that pass-2 is **prompt delta only** (no full re-inference). | S | Document: pass-2 sends single-field JSON patch prompt, not full vision schema. |
| **C-05** | **Parallelism vs RPM tradeoff unspecified** | Medium | `batch_runner.py` parallelism without shared `rate_limit.py` risks 429 storms. | M | Central rate limiter in providers; default `max_workers=2` for Pro image calls. |
| **C-06** | **No pre-run cost estimator** | Medium | Eval report requires stated pricing assumptions; no dry-run counter. | S | `evaluation/operational_report.py` includes `--estimate` mode: count images × Pro + rows × Flash before live run. |
| **C-07** | **No observation replay for dev** | Low | `providers/fixture_replay.py` in extensibility only. Saves cost during rule iteration. | S | Promote to `providers/mock/replay.py` in competition-grade checklist. |

**Rough cost model (document in eval report):**

```text
calls_flash  = num_rows
calls_pro    = num_images + num_multi_part_rows   # pass-2
cost_usd     = calls_flash × flash_price + (tokens_pro_in + tokens_pro_out) × pro_price
```

---

### 3.5 Missing Judge-Interview Capabilities

| ID | Gap | Severity | Rationale | Cost | Recommendation |
|----|-----|----------|-----------|------|----------------|
| **J-01** | **No judge-facing narrative document** | High | problem_decomposition §10: interview on approach, models, eval, AI-assisted dev. No `docs/judge_brief.md` or equivalent. | M | Create `docs/judge_brief.md`: 1-page architecture, constitution compliance, strategy winner, known limitations. |
| **J-02** | **Hidden rules not in persistent DS artifact** | High | Empirical rules discovered in chat; `hidden_business_rules.md` missing. Judge will ask for evidence behind HR-01..HR-08. | M | Populate `docs/ds/hidden_business_rules.md` with row citations from `sample_claims.csv`. |
| **J-03** | **No exemplar row walkthroughs** | High | Best defense is tracing 3 rows: supported (`user_001`), NEI (`user_006`), contradicted (`user_005`). | M | Add `docs/judge_walkthroughs.md` with stage → contract → rule ID for each. |
| **J-04** | **No constitution compliance checklist** | Medium | architect_prompt.md has 7 principles; no submission-facing mapping. | S | Section in `judge_brief.md`: principle → module → test proving it. |
| **J-05** | **No strategy selection rationale template** | Medium | README must document which strategy produced `output.csv`; no required sections. | S | `code/README.md` template: Strategy A vs B table, winner, cost/accuracy tradeoff. |
| **J-06** | **No live demo script** | Medium | "Models observe; rules decide" is architectural headline — no 5-minute demo flow. | S | `judge_brief.md` §Demo: open trace for `user_008`, show Flash output ≠ verdict, show CS-R04. |
| **J-07** | **Architecture one-pager still stub** | Medium | `docs/architecture.md` says "To be designed"; judges may read wrong doc. | S | Replace with pointer to architecture_v2 + mermaid diagram export. |
| **J-08** | **AI-assisted development story** | Low | Separate submission artifact (`log.txt`); cross-link in README. | S | Note in `judge_brief.md`: development log path per AGENTS.md §10. |

---

## 4. architecture_v2 §8 Checklist Status

| Check | Owner | Status |
|-------|-------|--------|
| `ClaimObservation` contract defined | Architect | **PASS** |
| Three decision engines separated | Architect | **PASS** |
| Per-engine metrics in evaluation plan | Data Scientist | **FAIL** — weights not canonical (E-01) |
| Hidden rules document exists | Data Scientist | **FAIL** — `docs/ds/` missing (E-02) |
| Class imbalance reflected in weights | Data Scientist | **FAIL** — `class_balance.md` missing (E-02) |
| decision_matrix execution order preserved | Engineer | **PASS** |
| No verdict fields in observation contracts | Engineer | **PASS** |
| Trace records all engine stages | Engineer | **PASS** (spec); replay eval missing (E-06) |

**Score: 5/8 PASS** — Data Scientist Mode gate not satisfied.

---

## 5. Required Changes Before Implementation

### Blocking (must complete before P0 code)

| Priority | Change | Owner | Delivers |
|----------|--------|-------|----------|
| **B1** | Create `docs/ds/hidden_business_rules.md` + `class_balance.md` | Data Scientist | E-02, J-02 |
| **B2** | Create `docs/evaluation_metrics.md` with weighted formula + slices | Data Scientist | E-01, E-07 |
| **B3** | Create `docs/ds/failure_taxonomy.md` + fixture mapping | Data Scientist | E-05, S-08 |
| **B4** | Add `docs/operations.md` (API failure, image prep, rate limits) | Engineer | O-01, C-01, C-05 |
| **B5** | Define `synthetic/schemas/` + minimum fixture set (multi-part, adversarial, 3 decision_contexts) | Engineer + DS | S-01, S-02, S-03, S-08 |
| **B6** | Update `docs/architecture.md` → pointer to v2 | Architect | J-07 |

### Non-blocking (complete during P7–P10)

| Priority | Change | Target phase |
|----------|--------|----------------|
| **N1** | `docs/judge_brief.md` + `judge_walkthroughs.md` | P9 |
| **N2** | `contracts/telemetry.py` + `RunManifest` | P10 |
| **N3** | `evaluation/invariants.py` + `replay.py` | P9 |
| **N4** | `config/metrics_weights.yaml` | P9 |
| **N5** | Remaining `docs/ds/` files (`label_analysis.md`, `hypotheses.md`) | P8 |

---

## 6. What Does NOT Require Change

- Module split (M7a/M7b/M7c) — correct for debuggability and metrics.
- `ClaimObservation` as first-class contract — correct.
- `decision_matrix.md` rule logic — no amendments needed for gate.
- `project_structure.md` directory layout — add files per gaps above, not restructure.
- Two-pass image observation design — sound; document pass-2 cost bound (C-04).

---

## 7. Risk Register (Post-Gate)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Overfit to 20 sample rows | High | High | Synthetic fixtures + invariant tests; do not tune on `claims.csv` |
| Multi-part test rows fail | Medium | High | S-01 fixtures before test inference |
| API cost overrun | Medium | Medium | C-02 budget, C-06 estimator, cache |
| Judge asks "why not one LLM?" | High | Low | J-03 walkthroughs + constitution checklist |
| Observation errors cascade to wrong verdict | Medium | High | E-04 observation eval; confidence gates in decision_matrix §8 |

---

## 8. Gate Decision

### **CHANGES REQUIRED**

**Justification:**

1. **Data Scientist Mode gate fails 3/8 checklist items** (E-02, E-01, E-05). architecture_v2 explicitly requires DS artifacts before implementation sign-off.
2. **Evaluation is specified conceptually but not normatively** — weighted score, per-engine bundles, and reconciliation-layer metrics lack a canonical document implementers can code against.
3. **Synthetic data design is incomplete** for the highest-risk test patterns (multi-part, adversarial injection) that the sample set does not cover.
4. **Operational failure handling is unspecified** — a 44-row Gemini batch without retry/degradation policy is not submission-safe.

**What is approved:**

- Architecture v2 module topology, contract graph, and execution order.
- `project_structure.md` repository layout and implementation phasing.
- `decision_matrix.md` as the single source of deterministic truth.
- `pydantic_contracts_v2.md` as the interface specification (minor amendment for E-11 optional).

**Re-gate condition:**

Proceed to **P0 implementation** when **B1–B6** are complete. Re-run this checklist; expected outcome **APPROVED FOR IMPLEMENTATION** with 8/8 §8 checks passing.

---

## 9. Document Map (Post-Review)

| Document | Action |
|----------|--------|
| [architecture_v2.md](architecture_v2.md) | No change — canonical |
| [pydantic_contracts_v2.md](pydantic_contracts_v2.md) | Minor: retain operational fields on EvaluationRecord |
| [project_structure.md](project_structure.md) | Add paths: `evaluation_metrics.md`, `operations.md`, `synthetic/schemas/`, `config/metrics_weights.yaml` |
| [decision_matrix.md](decision_matrix.md) | No change |
| **`docs/evaluation_metrics.md`** | **CREATE** |
| **`docs/operations.md`** | **CREATE** |
| **`docs/ds/*`** | **CREATE** (5 files) |
| **`docs/judge_brief.md`** | **CREATE** (non-blocking) |
| [architecture.md](architecture.md) | **UPDATE** → redirect to v2 |

---

## 10. Sign-Off Template

```text
Architecture topology:     APPROVED
Contracts v2:              APPROVED (minor amendment)
Decision matrix:           APPROVED
Project structure:         APPROVED (additive files)
Data Scientist Mode:       NOT APPROVED — pending docs/ds/
Evaluation specification:  NOT APPROVED — pending evaluation_metrics.md
Synthetic data design:     NOT APPROVED — pending fixtures
Operations specification:  NOT APPROVED — pending operations.md

OVERALL GATE:              CHANGES REQUIRED
```
