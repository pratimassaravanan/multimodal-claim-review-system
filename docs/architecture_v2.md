# Architecture v2

**Status:** Approved design revision  
**Supersedes:** [architecture_review.md](architecture_review.md) §5 recommended 8-module merge (partially)  
**Companion:** [pydantic_contracts_v2.md](pydantic_contracts_v2.md), [decision_matrix.md](decision_matrix.md), [architect_prompt.md](architect_prompt.md)

---

## Revision Summary

| Area | v1 (architecture_review) | v2 (this document) |
|------|--------------------------|-------------------|
| Claim text observations | Embedded in `EvidenceContext` | **First-class `ClaimObservation` contract** |
| Decision stage | Single `Decide` module (verdict + severity + supporting IDs merged) | **Three separate engines** |
| Architecture review | Engineer + architect checklist | **+ Data Scientist Mode** |
| Contract count | 12 | **15** (3 new decision outputs + `ClaimObservation`) |

---

## 1. What Changed

### 1.1 `ClaimObservation` promoted to first-class contract

**Before:** Flash output fields (`alleged_parts_unresolved`, `alleged_issue_types`, injection flags, etc.) lived inside `EvidenceContext` alongside images.

**After:** `ClaimObserver` produces a standalone **`ClaimObservation`** contract consumed by `ResolveClaim` and referenced by `EvidenceContext`.

```text
ClaimContext → ClaimObserver → ClaimObservation → ResolveClaim → ClaimResolutionContext
```

### 1.2 Decision engines split (no merge)

**Before:** architecture_review §5 recommended merging verdict, severity, and supporting image selection into one `Decide` / Decision Matrix module.

**After:** Three independent rule modules with distinct contracts:

| Module | Contract output | Decision matrix |
|--------|-----------------|-----------------|
| **ClaimDecisionEngine** | `VerdictDecision` | §3 (`claim_status`, `issue_type`, `object_part`) |
| **SeverityEngine** | `SeverityDecision` | §4 (`severity`) |
| **SupportingImageSelector** | `SupportingImageDecision` | §5 (`supporting_image_ids`) |

`ClaimDecision` remains as a **composition contract** for `Emit` and `EvaluationRecord`, assembled from the three engine outputs plus validation/trust copies.

### 1.3 Data Scientist Mode added to architecture review

**Before:** Review process focused on component necessity, hidden rules from samples, and engineer metrics.

**After:** Formal **Data Scientist Mode** gate runs before architecture sign-off and after each rule-matrix change. See §4.

---

## 2. Why It Changed

### 2.1 `ClaimObservation` separation

| Rationale | Detail |
|-----------|--------|
| Single responsibility | Text parsing (Flash) is a different failure domain than image parsing (Pro). |
| Independent evaluation | Claim extraction accuracy can be measured per-language without running vision. |
| Auditability | Judges can inspect alleged claim vs. resolution vs. verdict as three distinct artifacts. |
| Constitution alignment | architect_prompt.md requires every component to be independently testable and evaluated. |
| Pipeline clarity | `ClaimResolutionContext` should consume explicit `ClaimObservation`, not a grab-bag aggregate. |

### 2.2 Separate decision engines

| Rationale | Detail |
|-----------|--------|
| Reverses premature simplification | architecture_review §5 merged engines for convenience; sample errors cluster by field (status vs. severity vs. supporting IDs). |
| Independent metrics | Each engine gets its own accuracy metric and failure taxonomy (see §6). |
| Isolated failure modes | Severity exaggeration (`user_005`) vs. wrong supporting image (`user_003`) vs. status error are debugged in different modules. |
| Ordered dependency preserved | Severity and supporting IDs still run **after** verdict; no circular coupling. |
| Constitution | “Rules Decide” does not require one monolithic rule function — it requires deterministic, explainable rules. |

### 2.3 Data Scientist Mode

| Rationale | Detail |
|-----------|--------|
| Small labeled set | 20 sample rows require explicit label analysis, not intuition. |
| Hidden rules | Rules like HR-01 (ESM false ⟹ NEI) were discovered empirically; process must be repeatable. |
| Class imbalance | 12 supported / 5 contradicted / 3 NEI biases naive accuracy. |
| Test set risk | 44 test rows lack labels; hypothesis testing on sample is the only validation gate. |

---

## 3. Expected Benefits

| Benefit | Mechanism |
|---------|-----------|
| Faster debugging | Trace points to `ClaimObservation` vs. `VerdictDecision` vs. `SeverityDecision` directly. |
| Targeted prompt iteration | Flash prompts optimized against `ClaimObservation` fields only. |
| Per-module CI | Unit tests per engine with frozen observation fixtures. |
| Judge interview readiness | Clear story: “models observe; three rule engines decide different columns.” |
| Reduced regression risk | Severity rule change cannot break supporting-image logic. |
| Scientific iteration | Data Scientist Mode produces documented hypotheses before code changes. |

---

## 4. Data Scientist Mode (Architecture Review Process)

Data Scientist Mode is a **mandatory review phase** alongside Principal Architect and Principal Engineer review. It runs:

1. **Before implementation** (after decision_matrix.md, before coding).
2. **After any decision-matrix or observation-prompt change.**
3. **Before final `output.csv` submission.**

### 4.1 Activities

| Activity | Output artifact | Purpose |
|----------|-----------------|---------|
| **Label analysis** | `docs/ds/label_analysis.md` | Per-field distributions, co-occurrence tables, language/object-type breakdown |
| **Hidden rule discovery** | `docs/ds/hidden_business_rules.md` | Empirical rules with sample evidence (replaces ad-hoc chat analysis) |
| **Hypothesis testing** | `docs/ds/hypotheses.md` | Each rule change stated as H0/H1 with pass/fail on sample |
| **Class imbalance analysis** | `docs/ds/class_balance.md` | `claim_status`, `severity`, flag sparsity; weighted metrics justification |
| **Failure pattern discovery** | `docs/ds/failure_taxonomy.md` | Confusion clusters per engine (verdict vs. severity vs. supporting IDs) |

### 4.2 Gate criteria (must pass to approve architecture version)

| Criterion | Threshold |
|-----------|-------------|
| All high-confidence hidden rules (HR-01..HR-08) encoded in decision_matrix | 100% |
| Weighted evaluation score defined per engine + end-to-end | Documented |
| Per-engine failure taxonomy has ≥1 test fixture per failure class | Minimum |
| Class imbalance acknowledged in metric weights | Documented |
| No architecture change without corresponding hypothesis entry | Process |

### 4.3 Integration with existing review

```text
Problem decomposition
    → Data Scientist Mode (label + hidden rules)
    → Architecture review (component necessity)
    → Decision matrix
    → Data Scientist Mode (hypothesis test on sample)
    → Pydantic contracts v2
    → Implementation
    → Per-engine evaluation
    → Data Scientist Mode (failure patterns on sample)
    → Test inference
```

---

## 5. System Architecture v2

### 5.1 Module diagram

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ M1  Intake → ClaimContext                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ├──────────────────────────────┬──────────────────────────────────────
         ▼                              ▼
┌─────────────────────┐    ┌─────────────────────┐
│ M2a ClaimObserver   │    │ M2b ImageObserver   │
│     (Gemini Flash)  │    │     (Gemini Pro)    │
└─────────┬───────────┘    └──────────┬──────────┘
          ▼                             ▼
┌─────────────────────┐    ┌─────────────────────┐
│ ClaimObservation    │    │ ImageEvidence[]     │
└─────────┬───────────┘    └──────────┬──────────┘
          │                             │
          └──────────────┬──────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ M3  ResolveClaim → ClaimResolutionContext                                   │
│     (may trigger M2b re-pass for primary-part visibility — see §5.3)      │
└─────────────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ M4  EvidenceContext = ClaimContext + ClaimObservation + ImageEvidence[]  │
└─────────────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ M5  ReconcileEvidence                                                        │
│     M5a ConsistencyEngine   → ConsistencyContext                            │
│     M5b SufficiencyEngine   → ValidationContext                             │
│     M5c TrustEngine         → TrustAssessmentContext                        │
└─────────────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ M6  DecisionContext (aggregator — no rules)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│ M7a Claim    │ │ M7b Severity │ │ M7c SupportingImage  │
│ DecisionEng  │ │ Engine       │ │ Selector             │
│ → Verdict    │ │ → Severity   │ │ → SupportingImage    │
│   Decision   │ │   Decision   │ │   Decision           │
└──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘
       │                │                     │
       └────────────────┼─────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ M8  ComposeClaimDecision → ClaimDecision (for emit)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ M9 AssessRisk│ │ M10 Explain│ │ M11 Emit     │
│ → RiskContext│ │ templates  │ │ output.csv   │
└──────────────┘ └──────────┘ └──────────────┘

Offline: M12 EvaluationHarness → EvaluationRecord (per-engine + e2e)
         M13 DecisionTrace (all contracts + rule hits per stage)
```

### 5.2 Execution order (normative)

Matches [decision_matrix.md](decision_matrix.md) with explicit engine boundaries:

| Step | Module | Output |
|------|--------|--------|
| 1 | Intake | `ClaimContext` |
| 2a | ClaimObserver | `ClaimObservation` |
| 2b | ImageObserver (pass 1) | `ImageEvidence[]` |
| 3 | ResolveClaim | `ClaimResolutionContext` |
| 2b′ | ImageObserver (pass 2, if needed) | Updated `claimed_primary_part_visible` |
| 4 | Observe aggregate | `EvidenceContext` |
| 5a | ConsistencyEngine | `ConsistencyContext` |
| 5b | SufficiencyEngine | `ValidationContext` |
| 5c | TrustEngine | `TrustAssessmentContext` |
| 6 | DecisionContext builder | `DecisionContext` |
| 7a | **ClaimDecisionEngine** | `VerdictDecision` |
| 7b | **SeverityEngine** | `SeverityDecision` |
| 7c | **SupportingImageSelector** | `SupportingImageDecision` |
| 8 | ComposeClaimDecision | `ClaimDecision` |
| 9 | AssessRisk | `RiskContext` |
| 10 | Explain | prose fields on `ClaimDecision` |
| 11 | Emit | CSV row |
| — | Trace | `DecisionTrace` |
| — | Evaluation | `EvaluationRecord` |

**Hard constraints:**

- M7b and M7c MUST read `VerdictDecision`; MUST NOT run before M7a.
- M9 AssessRisk MUST run after M8 `ClaimDecision` is composed.
- M9 MUST NOT influence M7a/M7b/M7c.

### 5.3 Two-pass image observation (new in v2)

`ImageEvidence.claimed_primary_part_visible` depends on `ClaimResolutionContext.primary_object_part`.

| Pass | When | Input |
|------|------|-------|
| Pass 1 | Before ResolveClaim | `ClaimObservation.alleged_parts` (all affirmed parts) |
| Pass 2 | After ResolveClaim | `ClaimResolutionContext.primary_object_part` |

If `multi_part_claim = false`, pass 2 is skipped. If true, pass 2 re-scores primary-part visibility only (not full vision re-inference).

---

## 6. Per-Module Responsibilities, Metrics, and Failure Modes

### 6.1 Observation layer

| Module | Responsibility | Primary metric | Failure modes |
|--------|----------------|----------------|---------------|
| ClaimObserver | Parse chat → `ClaimObservation` | Part + issue extraction accuracy | Multilingual miss, injection not stripped, wrong part from narrative |
| ImageObserver | Parse pixels → `ImageEvidence` | Per-field observation F1 | Hallucinated damage, missed blur, false non-original |

### 6.2 Reconciliation layer

| Module | Responsibility | Primary metric | Failure modes |
|--------|----------------|----------------|---------------|
| ResolveClaim | Multi-part → primary | MP policy accuracy on synthetic multi-part | Wrong primary on tie-break |
| ConsistencyEngine | Cross-image predicates | Identity conflict recall | Missed `user_002` pattern |
| SufficiencyEngine | `evidence_standard_met` | ESM accuracy; NEI ⟺ false | False NEI on blurry+clear |
| TrustEngine | `valid_image` | Valid-image accuracy | Confuse with ESM |

### 6.3 Decision layer (split)

| Module | Contract | Fields owned | Primary metric | Failure modes |
|--------|----------|--------------|----------------|---------------|
| **ClaimDecisionEngine** | `VerdictDecision` | `claim_status`, `issue_type`, `object_part`, `claim_status_rule_id` | `claim_status` accuracy | NEI/contradiction swap, wrong ontology on contradiction |
| **SeverityEngine** | `SeverityDecision` | `severity`, `severity_rule_id` | Severity tier accuracy | Uses claim text; NEI not `unknown` |
| **SupportingImageSelector** | `SupportingImageDecision` | `supporting_image_ids`, `supporting_image_rule_id` | Exact set match | Includes blurry image; misses identity-conflict pair |

### 6.4 Post-decision layer

| Module | Responsibility | Primary metric | Failure modes |
|--------|----------------|----------------|---------------|
| ComposeClaimDecision | Merge engine outputs | Schema compliance | Field mismatch |
| AssessRisk | `risk_flags` | RF-1 compliance; flag F1 | History flips status (forbidden) |
| Explain | Template prose | Grounding checklist | History-only justification |

---

## 7. Implementation Impact

| Area | Impact | Severity |
|------|--------|----------|
| **New files / modules** | 3 decision engine modules + 1 composer + `ClaimObservation` schema | Medium |
| **Pipeline orchestrator** | Sequential M7a→M7b→M7c instead of single `decide()` | Low |
| **Tests** | Per-engine unit tests with frozen `DecisionContext` fixtures | Medium — more tests, easier isolation |
| **Evaluation harness** | `EvaluationRecord` extended with per-engine sub-scores | Medium |
| **DecisionTrace** | `RuleHit.stage` adds `verdict`, `severity`, `supporting` (replaces monolithic `decide`) | Low |
| **ImageObserver** | Optional pass-2 for multi-part rows | Low |
| **EvidenceContext** | Refactored to reference `ClaimObservation` by value | Low |
| **Breaking change from v1 contracts** | `ClaimDecision` no longer produced by single module; `EvidenceContext` field layout changes | High for any prototype on v1 |
| **decision_matrix.md** | No rule changes required — only module boundaries | None |
| **Data Scientist artifacts** | New `docs/ds/` folder expected before submission | Medium — documentation workload |

### 7.1 Migration from v1 contracts

| v1 | v2 |
|----|-----|
| Flash fields on `EvidenceContext` | `ClaimObservation` |
| `ClaimDecision` from one `Decide` module | `VerdictDecision` + `SeverityDecision` + `SupportingImageDecision` → `ClaimDecision` |
| `RuleHit.stage = "decide"` | `verdict` \| `severity` \| `supporting` |
| architecture_review §5 8-module merge | 11 runtime modules + 2 offline |

### 7.2 What does NOT change

- Gemini Flash + Pro model policy (architect_prompt.md)
- decision_matrix.md rule IDs and logic
- Risk assessment after verdict
- Deterministic template explanations
- 14-column `output.csv` schema

---

## 8. Architecture Approval Checklist v2

| Check | Owner |
|-------|-------|
| `ClaimObservation` contract defined | Architect |
| Three decision engines separated in contracts | Architect |
| Per-engine metrics in evaluation plan | Data Scientist |
| Hidden rules document exists | Data Scientist |
| Class imbalance reflected in weights | Data Scientist |
| decision_matrix execution order preserved | Engineer |
| No verdict fields in observation contracts | Engineer |
| Trace records all engine stages | Engineer |

---

## 9. Document Map

| Document | Role |
|----------|------|
| [problem_decomposition.md](problem_decomposition.md) | What the system must do |
| [decision_matrix.md](decision_matrix.md) | Deterministic rules (unchanged) |
| [pydantic_contracts_v2.md](pydantic_contracts_v2.md) | Typed interfaces v2 |
| [architecture_review.md](architecture_review.md) | v1 review history (superseded §5 merge recommendation) |
| **architecture_v2.md** | **This document — canonical architecture** |
| `docs/ds/*` | Data Scientist Mode artifacts (to be created) |
