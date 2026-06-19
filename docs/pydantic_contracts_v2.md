# Pydantic Contracts Specification v2

**Status:** Normative interface definition v2 (documentation only — no implementation code)  
**Supersedes:** [pydantic_contracts.md](pydantic_contracts.md) for new development  
**Aligns with:** [architecture_v2.md](architecture_v2.md), [decision_matrix.md](decision_matrix.md), [architect_prompt.md](architect_prompt.md)

---

## Changelog v1 → v2

| Change | v1 | v2 | Why |
|--------|----|----|-----|
| **ClaimObservation** | Flash fields embedded in `EvidenceContext` | Standalone contract #2 | Independent evaluation, auditability, SRP |
| **Decision outputs** | Single `ClaimDecision` from one `Decide` module | `VerdictDecision` + `SeverityDecision` + `SupportingImageDecision` → composed `ClaimDecision` | Separate metrics, failure modes, testability |
| **EvidenceContext** | Included alleged parts, injection flags, model metadata | References `ClaimObservation`; images + claim only | Clear producer boundaries |
| **ClaimResolutionContext** | Consumed implied Flash output | Explicitly consumes `ClaimObservation` | Typed handoff |
| **DecisionTrace stages** | `decide` | `verdict`, `severity`, `supporting`, `compose` | Per-engine audit |
| **EvaluationRecord** | End-to-end field match only | + per-engine sub-scores | Data Scientist Mode |
| **ImageEvidence pass** | Single pass | Pass 1 + optional pass 2 after resolution | `claimed_primary_part_visible` accuracy |

**Unchanged from v1:** Shared enums, `ScoredField<T>`, `ClaimContext`, `ImageEvidence` field schema (except pass-2 note), `ValidationContext`, `TrustAssessmentContext`, `ConsistencyContext`, `RiskContext`, core `DecisionContext` inputs.

---

## Conventions

Same as v1: field metadata columns (**Type**, **Nullable**, **Source**, **Confidence**), shared primitives, `ScoredField<T>`, and enums. See [pydantic_contracts.md](pydantic_contracts.md) §Conventions for full enum lists.

### Pipeline data flow v2

```text
ClaimContext
    → ClaimObservation                    (M2a ClaimObserver)
    → ImageEvidence[]                     (M2b ImageObserver)
    → ClaimResolutionContext              (M3 ResolveClaim)
    → EvidenceContext                     (M4 aggregate)
    → ConsistencyContext
    → ValidationContext
    → TrustAssessmentContext
    → DecisionContext
    → VerdictDecision                     (M7a ClaimDecisionEngine)
    → SeverityDecision                    (M7b SeverityEngine)
    → SupportingImageDecision             (M7c SupportingImageSelector)
    → ClaimDecision                       (M8 ComposeClaimDecision)
    → RiskContext
    → DecisionTrace
    → EvaluationRecord
```

---

## Contract Index

| # | Contract | v1 # | Status |
|---|----------|------|--------|
| 1 | ClaimContext | 1 | Unchanged — see v1 |
| 2 | **ClaimObservation** | — | **NEW** |
| 3 | ClaimResolutionContext | 2 | **Updated** |
| 4 | ImageEvidence | 3 | Minor update (pass-2) |
| 5 | EvidenceContext | 4 | **Updated** |
| 6 | ValidationContext | 5 | Unchanged — see v1 |
| 7 | TrustAssessmentContext | 6 | Unchanged — see v1 |
| 8 | ConsistencyContext | 7 | Unchanged — see v1 |
| 9 | RiskContext | 8 | Unchanged — see v1 |
| 10 | DecisionContext | 9 | **Updated** |
| 11 | **VerdictDecision** | — | **NEW** (split from ClaimDecision) |
| 12 | **SeverityDecision** | — | **NEW** (split from ClaimDecision) |
| 13 | **SupportingImageDecision** | — | **NEW** (split from ClaimDecision) |
| 14 | ClaimDecision | 10 | **Updated** (composition only) |
| 15 | DecisionTrace | 11 | **Updated** |
| 16 | EvaluationRecord | 12 | **Updated** |

---

## 1. ClaimContext

**Unchanged from v1.** See [pydantic_contracts.md](pydantic_contracts.md) §1.

| Attribute | Value |
|-----------|-------|
| Producer | `Intake` |
| Consumers | `ClaimObserver`, `ImageObserver`, `ResolveClaim`, `AssessRisk`, `Emit`, `EvaluationRecord` |

---

## 2. ClaimObservation (NEW)

### Purpose

Normalized output of Gemini 2.5 Flash claim understanding. Captures everything extracted from `user_claim` before multi-part resolution. **No verdict fields.**

### Producer

`ClaimObserver` module (Flash + ontology gate + adversarial sanitizer)

### Consumers

`ResolveClaim`, `EvidenceContext` builder, `EvaluationRecord` (claim extraction metrics), `DecisionTrace`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `alleged_parts` | list[ObjectPart] | no | claim_observer | none — customer-affirmed parts, unresolved |
| `alleged_issue_types` | list[IssueType] | no | claim_observer | none — normalized alleged types |
| `alleged_issue_families` | list[IssueFamily] | no | claim_observer | none — mapped per decision_matrix §0.4 |
| `exclusions` | list[NonEmptyString] | no | claim_observer | none — explicit "not X" statements |
| `identity_constraint_active` | ScoredField[bool] | no | claim_observer | required |
| `identity_side` | ScoredField[IdentitySide] | yes | claim_observer | required when side claimed |
| `identity_color` | ScoredField[NonEmptyString] | yes | claim_observer | required when color claimed |
| `claimed_damage_alleged` | ScoredField[bool] | no | claim_observer | required — physical damage alleged |
| `claimed_severity_language` | ScoredField[ClaimedSeverityLanguage] | no | claim_observer | required — for CS-R06 only; never for severity output |
| `multi_part_detected` | bool | no | claim_observer | none — `len(alleged_parts) > 1` |
| `injection_detected_in_chat` | bool | no | claim_observer | none |
| `injection_excerpt` | NonEmptyString | yes | claim_observer | none — redacted if detected |
| `sanitized_claim_excerpt` | NonEmptyString | no | claim_observer | none — injection-stripped summary for audit |
| `model_name` | NonEmptyString | no | claim_observer | none — `gemini-2.5-flash` |
| `prompt_version` | NonEmptyString | no | claim_observer | none |
| `observation_raw_hash` | NonEmptyString | no | claim_observer | none — reproducibility |
| `observed_at` | ISOTimestamp | no | claim_observer | none |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `detected_languages` | list[NonEmptyString] | yes | claim_observer | none |
| `last_customer_message_excerpt` | NonEmptyString | yes | claim_observer | none — for MP tie-break audit |
| `overall_extraction_confidence` | ConfidenceLevel | yes | claim_observer | none |

### Validation rules

1. `row_id` matches `ClaimContext.row_id`.
2. All `alleged_parts` valid for `claim_object`.
3. All `alleged_issue_types` valid `IssueType` values.
4. No field in `claim_status`, `evidence_standard_met`, `risk_flags`, `severity`, `object_part` (resolved), or `issue_type` (visible).
5. If `injection_detected_in_chat = true`, `sanitized_claim_excerpt` must not contain actionable injection text.
6. `claimed_severity_language` MUST NOT be copied to `SeverityDecision` downstream.

### Example instance

```json
{
  "row_id": "user_005:case_005",
  "alleged_parts": ["rear_bumper"],
  "alleged_issue_types": ["dent"],
  "alleged_issue_families": ["dent_or_scratch"],
  "exclusions": [],
  "identity_constraint_active": { "value": false, "confidence": "high", "confidence_score": 0.95, "source_module": "claim_observer", "source_image_id": null },
  "identity_side": null,
  "identity_color": null,
  "claimed_damage_alleged": { "value": true, "confidence": "high", "confidence_score": 0.92, "source_module": "claim_observer", "source_image_id": null },
  "claimed_severity_language": { "value": "exaggerated", "confidence": "medium", "confidence_score": 0.78, "source_module": "claim_observer", "source_image_id": null },
  "multi_part_detected": false,
  "injection_detected_in_chat": false,
  "injection_excerpt": null,
  "sanitized_claim_excerpt": "Customer alleges rear bumper damage described as pretty bad.",
  "model_name": "gemini-2.5-flash",
  "prompt_version": "claim-v1",
  "observation_raw_hash": "sha256:def456...",
  "observed_at": "2026-06-19T21:00:01+05:30",
  "detected_languages": ["en"]
}
```

---

## 3. ClaimResolutionContext (UPDATED)

### Purpose

Output of `ResolveClaim` (decision_matrix §7). Selects single primary part and issue family for downstream matrices.

### Producer

`ResolveClaim` module

### Consumers

`ImageObserver` (pass 2), `ConsistencyContext` builder, `ValidationContext`, `DecisionContext`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `claim_observation_ref` | NonEmptyString | no | ClaimObservation | none — `observation_raw_hash` for audit link |
| `multi_part_claim` | bool | no | derived | none — equals `ClaimObservation.multi_part_detected` after MP rules |
| `primary_object_part` | ObjectPart | no | rule_engine | none |
| `primary_issue_family` | IssueFamily | no | rule_engine | none |
| `secondary_object_parts` | list[ObjectPart] | no | rule_engine | none |
| `resolution_method` | `"single_part"` \| `"visibility_score"` \| `"last_mention_tiebreak"` | no | rule_engine | none |
| `resolution_rule_ids` | list[RuleId] | no | rule_engine | none — MP-1..MP-5 |
| `part_visibility_scores` | map[ObjectPart → int] | no | derived | none — high=3, medium=2, low=1, absent=0 |
| `resolved_at` | ISOTimestamp | no | rule_engine | none |

### Removed from v1 (moved to ClaimObservation)

`alleged_parts`, `identity_constraint_active`, `identity_side`, `identity_color`, `claimed_damage_absent`, `claimed_severity_language`, `alleged_issue_types`

### Validation rules

1. `primary_object_part` ∈ `ClaimObservation.alleged_parts` when `multi_part_claim = true`.
2. `primary_issue_family` compatible with `primary_object_part` per decision_matrix §0.3.
3. `secondary_object_parts` = `alleged_parts \ {primary_object_part}`.

### Example instance

```json
{
  "row_id": "user_001:case_001",
  "claim_observation_ref": "sha256:abc...",
  "multi_part_claim": false,
  "primary_object_part": "rear_bumper",
  "primary_issue_family": "dent_or_scratch",
  "secondary_object_parts": [],
  "resolution_method": "single_part",
  "resolution_rule_ids": ["MP-2"],
  "part_visibility_scores": { "rear_bumper": 3 },
  "resolved_at": "2026-06-19T21:00:01+05:30"
}
```

---

## 4. ImageEvidence (MINOR UPDATE)

**Base schema unchanged from v1** — see [pydantic_contracts.md](pydantic_contracts.md) §3.

### v2 addition

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `observation_pass` | `1` \| `2` | no | image_observer | none — pass 2 after `ClaimResolutionContext` |

### Validation rule (v2)

- Pass 1: `claimed_primary_part_visible` scored against all `ClaimObservation.alleged_parts`.
- Pass 2: rescored only for `ClaimResolutionContext.primary_object_part` when `multi_part_claim = true`.

---

## 5. EvidenceContext (UPDATED)

### Purpose

Aggregate after observation. **Does not duplicate claim text fields.**

### Producer

`Observe` module (M4)

### Consumers

`ConsistencyContext` builder, `ResolveClaim` (pass-2 trigger), `EvaluationRecord`, `DecisionTrace`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `claim` | ClaimContext | no | intake | none |
| `claim_observation` | ClaimObservation | no | claim_observer | none |
| `images` | list[ImageEvidence] | no | image_observer | none |
| `observation_complete` | bool | no | derived | none |
| `aggregated_at` | ISOTimestamp | no | derived | none |

### Removed from v1

`claim_observation_model`, `claim_observation_prompt_version`, `claim_observation_at`, `alleged_parts_unresolved`, `alleged_issue_types`, `exclusions`, `injection_detected_in_chat`, `injection_excerpt`, `detected_languages` — all live on `ClaimObservation`.

### Validation rules

1. `len(images) == claim.image_count`.
2. `claim_observation.row_id == claim.row_id`.
3. No verdict fields on this contract.

---

## 6–9. ValidationContext, TrustAssessmentContext, ConsistencyContext, RiskContext

**Unchanged from v1.** See [pydantic_contracts.md](pydantic_contracts.md) §5–§8.

---

## 10. DecisionContext (UPDATED)

### Purpose

Immutable snapshot for decision engines M7a–M7c. **Contains no rule outputs.**

### Producer

`DecisionContext` builder (M6)

### Consumers

`ClaimDecisionEngine`, `SeverityEngine`, `SupportingImageSelector`, `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `claim` | ClaimContext | no | intake | none |
| `claim_observation` | ClaimObservation | no | claim_observer | none |
| `resolution` | ClaimResolutionContext | no | ResolveClaim | none |
| `images` | list[ImageEvidence] | no | image_observer | none |
| `consistency` | ConsistencyContext | no | consistency | none |
| `validation` | ValidationContext | no | sufficiency | none |
| `trust` | TrustAssessmentContext | no | trust | none |
| `evidence_standard_met` | bool | no | ValidationContext | none — copy |
| `valid_image` | bool | no | TrustAssessmentContext | none — copy |
| `aggregated_at` | ISOTimestamp | no | derived | none |

### Validation rules

1. No `VerdictDecision`, `SeverityDecision`, `SupportingImageDecision`, `RiskContext` at construction.
2. `claim_observation` must be present (v2 requirement — not optional).

---

## 11. VerdictDecision (NEW)

### Purpose

Output of **ClaimDecisionEngine** (decision_matrix §3). Owns status and visible ontology only.

### Producer

`ClaimDecisionEngine` (M7a)

### Consumers

`SeverityEngine`, `SupportingImageSelector`, `ComposeClaimDecision`, `AssessRisk` (read-only), `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `claim_status` | ClaimStatus | no | rule_engine | none |
| `claim_status_rule_id` | RuleId | no | rule_engine | none — CS-R01..CS-R08 |
| `issue_type` | IssueType | no | rule_engine | none |
| `object_part` | ObjectPart | no | rule_engine | none |
| `contradiction_subtype` | enum or null | yes | rule_engine | none — see v1 ClaimDecision |
| `decided_at` | ISOTimestamp | no | rule_engine | none |

### Validation rules

1. HR-01: `evidence_standard_met = false` ⟹ `claim_status = not_enough_information` (reads from `DecisionContext.validation`).
2. HR-02: `claim_status = contradicted` ⟹ `evidence_standard_met = true`.
3. `object_part` valid for `claim_object`.
4. MUST NOT contain `severity`, `supporting_image_ids`, `risk_flags`.

### Example instance

```json
{
  "row_id": "user_005:case_005",
  "claim_status": "contradicted",
  "claim_status_rule_id": "CS-R06",
  "issue_type": "scratch",
  "object_part": "rear_bumper",
  "contradiction_subtype": "severity_exaggeration",
  "decided_at": "2026-06-19T21:00:03+05:30"
}
```

---

## 12. SeverityDecision (NEW)

### Purpose

Output of **SeverityEngine** (decision_matrix §4). Visible damage magnitude only.

### Producer

`SeverityEngine` (M7b)

### Consumers

`ComposeClaimDecision`, `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `severity` | Severity | no | rule_engine | none |
| `severity_rule_id` | RuleId | no | rule_engine | none — SV-R01..SV-R08 |
| `visible_damage_extent_source` | DamageExtent | no | rule_engine | none — from supporting image observation |
| `source_image_id` | NonEmptyString | yes | rule_engine | none — image extent read from |
| `verdict_ref` | NonEmptyString | no | VerdictDecision | none — hash or `decided_at` link |
| `decided_at` | ISOTimestamp | no | rule_engine | none |

### Validation rules

1. MUST read `VerdictDecision` — HR-03: `claim_status = not_enough_information` ⟹ `severity = unknown`.
2. SV-02: `issue_type = none` ⟹ `severity = none` (from `VerdictDecision.issue_type`).
3. MUST NOT read `ClaimObservation.claimed_severity_language` for `severity` value.
4. MUST NOT run before `VerdictDecision` exists.

### Example instance

```json
{
  "row_id": "user_005:case_005",
  "severity": "low",
  "severity_rule_id": "SV-R04",
  "visible_damage_extent_source": "low",
  "source_image_id": "img_1",
  "verdict_ref": "user_005:case_005:verdict:2026-06-19T21:00:03+05:30",
  "decided_at": "2026-06-19T21:00:03+05:30"
}
```

---

## 13. SupportingImageDecision (NEW)

### Purpose

Output of **SupportingImageSelector** (decision_matrix §5). Identifies images substantiating the **decision**.

### Producer

`SupportingImageSelector` (M7c)

### Consumers

`ComposeClaimDecision`, `SeverityEngine` (optional extent lookup), `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `supporting_image_ids` | list[NonEmptyString] | no | rule_engine | none — empty → CSV `none` |
| `supporting_image_rule_id` | RuleId | no | rule_engine | none — SI-R01..SI-R07 |
| `excluded_image_ids` | list[NonEmptyString] | no | rule_engine | none — audit blur/irrelevant exclusions |
| `selection_rationale` | NonEmptyString | no | rule_engine | none — short deterministic reason |
| `verdict_ref` | NonEmptyString | no | VerdictDecision | none |
| `decided_at` | ISOTimestamp | no | rule_engine | none |

### Validation rules

1. MUST read `VerdictDecision.claim_status`.
2. `supporting_image_ids` ⊆ `ClaimContext.image_ids`.
3. SI-R01: identity conflict NEI → all image IDs allowed.
4. MUST NOT run before `VerdictDecision` exists.
5. Blurry images excluded when another image satisfies same rule (§5.2).

### Example instance

```json
{
  "row_id": "user_003:case_007",
  "supporting_image_ids": ["img_2"],
  "supporting_image_rule_id": "SI-R04",
  "excluded_image_ids": ["img_1"],
  "selection_rationale": "img_1 blurry; img_2 shows door dent clearly",
  "verdict_ref": "user_003:case_007:verdict:...",
  "decided_at": "2026-06-19T21:00:03+05:30"
}
```

---

## 14. ClaimDecision (UPDATED — composition only)

### Purpose

Final composed decision for `Emit` and end-to-end evaluation. **Produced only by `ComposeClaimDecision` — no rules execute here.**

### Producer

`ComposeClaimDecision` (M8)

### Consumers

`AssessRisk`, `Explain`, `Emit`, `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `verdict` | VerdictDecision | no | ClaimDecisionEngine | none |
| `severity_decision` | SeverityDecision | no | SeverityEngine | none |
| `supporting_decision` | SupportingImageDecision | no | SupportingImageSelector | none |
| `evidence_standard_met` | bool | no | ValidationContext | none — copy |
| `evidence_standard_met_reason` | NonEmptyString | no | rule_engine | none — rendered at compose from ValidationContext |
| `valid_image` | bool | no | TrustAssessmentContext | none — copy |
| `claim_status_justification` | NonEmptyString | no | explain | none — template at M10 |
| `composed_at` | ISOTimestamp | no | compose | none |

### Convenience accessors (derived, not stored separately)

| Output column | Source |
|---------------|--------|
| `claim_status` | `verdict.claim_status` |
| `issue_type` | `verdict.issue_type` |
| `object_part` | `verdict.object_part` |
| `severity` | `severity_decision.severity` |
| `supporting_image_ids` | `supporting_decision.supporting_image_ids` joined `;` or `none` |

### Validation rules

1. Cross-field HR rules enforced at compose time (HR-01..03, SV-02).
2. `ComposeClaimDecision` MUST NOT re-run decision_matrix rules; only validates consistency and renders templates.

### Removed from v1 ClaimDecision

Direct ownership of `claim_status_rule_id`, `severity_rule_id`, `supporting_image_rule_id` at top level — now on sub-decisions.

---

## 15. DecisionTrace (UPDATED)

### Purpose

Full audit record. v2 adds `claim_observation` and per-engine rule hits.

### Producer

Pipeline orchestrator

### Required fields (additions/changes from v1)

| Field | Type | Nullable | Source |
|-------|------|----------|--------|
| `claim_observation` | ClaimObservation | no | claim_observer |
| `verdict` | VerdictDecision | no | ClaimDecisionEngine |
| `severity_decision` | SeverityDecision | no | SeverityEngine |
| `supporting_decision` | SupportingImageDecision | no | SupportingImageSelector |
| `decision` | ClaimDecision | no | ComposeClaimDecision |

### RuleHit.stage enum (v2)

```text
"observe_claim" | "observe_image" | "resolve" | "consistency" | "validation" | "trust"
| "verdict" | "severity" | "supporting" | "compose" | "risk" | "explain"
```

**Removed:** monolithic `"decide"`.

### Validation rules

1. At least one `RuleHit` with `stage = verdict`, `severity`, `supporting` when decision path completes.
2. `claim_observation` included in `deterministic_hash`.

All other fields unchanged from v1 §11.

---

## 16. EvaluationRecord (UPDATED)

### Purpose

Offline evaluation with **per-engine sub-scores** (Data Scientist Mode).

### Producer

`EvaluationHarness`

### Required fields (additions from v1)

| Field | Type | Nullable | Source |
|-------|------|----------|--------|
| `verdict_match` | bool | yes | evaluation |
| `severity_match` | bool | yes | evaluation |
| `supporting_ids_match` | bool | yes | evaluation |
| `claim_observation_part_match` | bool | yes | evaluation — optional extraction metric |
| `engine_scores` | EngineScoreBundle | yes | evaluation |

### Nested: `EngineScoreBundle`

| Field | Type | Description |
|-------|------|-------------|
| `verdict_score` | float | 1.0 if `claim_status` + `issue_type` + `object_part` match |
| `severity_score` | float | 1.0 if `severity` matches |
| `supporting_score` | float | 1.0 if exact set match |
| `extraction_score` | float | Optional alleged part match |
| `weighted_total` | float | Per architecture_v2 §6 weights |

All other fields unchanged from v1 §12.

---

## Contract Dependency Matrix v2

| Contract | Depends on | Must not depend on |
|----------|------------|-------------------|
| ClaimObservation | ClaimContext | ClaimResolutionContext, any decision output |
| ClaimResolutionContext | ClaimContext, ClaimObservation, ImageEvidence[] | ValidationContext, any decision output |
| EvidenceContext | ClaimContext, ClaimObservation, ImageEvidence[] | Decision outputs |
| VerdictDecision | DecisionContext | SeverityDecision, SupportingImageDecision, RiskContext |
| SeverityDecision | DecisionContext, VerdictDecision | SupportingImageDecision, RiskContext |
| SupportingImageDecision | DecisionContext, VerdictDecision | SeverityDecision, RiskContext |
| ClaimDecision | VerdictDecision, SeverityDecision, SupportingImageDecision, ValidationContext, TrustAssessmentContext | RiskContext (at compose time) |
| RiskContext | ClaimDecision, EvidenceContext, ConsistencyContext, ClaimContext | — |

---

## Anti-Patterns v2 (additions)

1. Passing Flash output as untyped dict instead of `ClaimObservation`.
2. Computing `severity` inside `ClaimDecisionEngine`.
3. Selecting `supporting_image_ids` inside `SeverityEngine`.
4. Skipping `VerdictDecision` and writing directly to `ClaimDecision`.
5. Using `claimed_severity_language` in `SeverityEngine`.

---

## Versioning

| Field | Location | Rule |
|-------|----------|------|
| `pipeline_version` | ClaimContext | Bump on contract v2 validation change |
| `contracts_version` | DecisionTrace | Set to `"2.0"` for this spec |
| `deterministic_hash` | DecisionTrace | Includes `ClaimObservation.observation_raw_hash` + all three decision refs |

---

## Implementation Impact Summary

| Task | Effort |
|------|--------|
| Add `ClaimObservation` model + Flash mapper | Medium |
| Split `Decide` into 3 engines + composer | Medium |
| Update `EvidenceContext` assembly | Low |
| Add pass-2 image observation hook | Low |
| Extend `DecisionTrace` stages | Low |
| Per-engine evaluation metrics | Medium |
| Migrate from v1 if prototype exists | High |

See [architecture_v2.md](architecture_v2.md) §7 for full impact analysis.
