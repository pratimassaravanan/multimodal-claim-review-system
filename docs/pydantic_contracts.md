# Pydantic Contracts Specification

**Status:** Normative interface definition (documentation only — no implementation code)  
**Purpose:** Eliminate dictionaries and ambiguous interfaces between modules  
**Aligns with:** [decision_matrix.md](decision_matrix.md) execution order, [architecture_review.md](architecture_review.md) module boundaries, [architect_prompt.md](architect_prompt.md) typed-contract step

---

## Conventions

### Field metadata columns

Every field documents:

| Column | Meaning |
|--------|---------|
| **Type** | Logical type (maps to Pydantic primitives, enums, or nested contracts) |
| **Nullable** | `no` = required; `yes` = optional; `conditional` = required when predicate holds |
| **Source** | Origin module or upstream field (`intake`, `claim_observer`, `image_observer`, `rule_engine`, `derived`) |
| **Confidence** | `none` = no confidence; `required` = must include `ConfidenceLevel`; `min_medium` = decision use requires ≥ medium; `min_high` = authenticity flags require high |

### Shared primitive types

```text
ConfidenceLevel     = "high" | "medium" | "low"
ConfidenceScore     = float in [0.0, 1.0]   # optional numeric backing for ConfidenceLevel
NonEmptyString      = string with length ≥ 1
SemicolonList       = ordered unique strings joined ";" for CSV-compatible output
ISOTimestamp        = ISO-8601 datetime string with timezone
RuleId              = string matching decision_matrix rule IDs (e.g. ESM-R02, CS-R07)
RequirementId       = string from evidence_requirements.csv (e.g. REQ_CAR_BODY_PANEL)
```

### Shared wrapper: `ScoredField<T>`

Used wherever observation models emit values that rules gate on confidence.

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `value` | T | no | model or rule | — |
| `confidence` | ConfidenceLevel | no | model | required |
| `confidence_score` | ConfidenceScore | yes | model | none |
| `source_module` | `"claim_observer"` \| `"image_observer"` \| `"rule_engine"` | no | pipeline | none |
| `source_image_id` | string | yes | image_observer | none — set when value is image-specific |

### Shared enums (output ontology)

```text
ClaimObject = "car" | "laptop" | "package"

ClaimStatus = "supported" | "contradicted" | "not_enough_information"

Severity = "none" | "low" | "medium" | "high" | "unknown"

IssueType = "dent" | "scratch" | "crack" | "glass_shatter" | "broken_part" |
            "missing_part" | "torn_packaging" | "crushed_packaging" | "water_damage" |
            "stain" | "none" | "unknown"

RiskFlag = "none" | "blurry_image" | "cropped_or_obstructed" | "low_light_or_glare" |
           "wrong_angle" | "wrong_object" | "wrong_object_part" | "damage_not_visible" |
           "claim_mismatch" | "possible_manipulation" | "non_original_image" |
           "text_instruction_present" | "user_history_risk" | "manual_review_required"

IssueFamily = "dent_or_scratch" | "crack_broken_missing" | "crushed_torn_seal" |
              "water_stain_label" | "contents_or_item" | "screen_keyboard_trackpad" |
              "hinge_lid_corner_body_port"

ObjectPart = <union per ClaimObject per problem_statement.md>

IdentitySide = "left" | "right" | "front" | "rear"

ClaimedSeverityLanguage = "none" | "low" | "medium" | "high" | "exaggerated"

DamageExtent = "none" | "low" | "medium" | "high" | "unknown"

HistoryFlag = "none" | "user_history_risk" | "manual_review_required"
```

### `ObjectPart` validation by `ClaimObject`

| `claim_object` | Allowed `ObjectPart` values |
|----------------|------------------------------|
| `car` | `front_bumper`, `rear_bumper`, `door`, `hood`, `windshield`, `side_mirror`, `headlight`, `taillight`, `fender`, `quarter_panel`, `body`, `unknown` |
| `laptop` | `screen`, `keyboard`, `trackpad`, `hinge`, `lid`, `corner`, `port`, `base`, `body`, `unknown` |
| `package` | `box`, `package_corner`, `package_side`, `seal`, `label`, `contents`, `item`, `unknown` |

**Validation rule:** `object_part` on any contract MUST belong to the set for the row's `claim_object`, else normalize to `unknown`.

### Pipeline data flow (contract handoff)

```text
ClaimContext
    → EvidenceContext (+ ImageEvidence[], AllegedClaim from Flash)
    → ClaimResolutionContext
    → ConsistencyContext
    → ValidationContext
    → TrustAssessmentContext
    → DecisionContext
    → ClaimDecision
    → RiskContext
    → DecisionTrace (wraps all + rule hits)
    → EvaluationRecord (offline, compares ClaimDecision to gold)
```

---

## 1. ClaimContext

### Purpose

Immutable intake bundle for one claim row. Contains all inputs needed by observation and rule modules. No model verdict fields.

### Producer

`Intake` module

### Consumers

`ClaimObserver` (Flash), `ImageObserver` (Pro), `ResolveClaim`, `AssessRisk` (history), `Emit`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | intake | none — stable id: `{user_id}:{content_hash}` or CSV line index |
| `user_id` | NonEmptyString | no | intake | none |
| `claim_object` | ClaimObject | no | intake | none |
| `user_claim` | NonEmptyString | no | intake | none — raw chat transcript |
| `image_paths` | list[NonEmptyString] | no | intake | none — ordered as in CSV |
| `image_ids` | list[NonEmptyString] | no | derived | none — basename without extension per path |
| `image_count` | int | no | derived | none — `len(image_ids)`, ≥ 1 |
| `resolved_image_files` | list[NonEmptyString] | no | intake | none — absolute paths verified to exist |
| `history_flags` | list[HistoryFlag] | no | intake | none — parsed from `user_history.history_flags`; `["none"]` if empty |
| `history_summary` | NonEmptyString | yes | intake | none |
| `past_claim_count` | int | no | intake | none — ≥ 0 |
| `accept_claim` | int | no | intake | none — ≥ 0 |
| `manual_review_claim` | int | no | intake | none — ≥ 0 |
| `rejected_claim` | int | no | intake | none — ≥ 0 |
| `last_90_days_claim_count` | int | no | intake | none — ≥ 0 |
| `applicable_requirement_ids` | list[RequirementId] | no | derived | none — universal set precomputed; object-specific filled after issue family known |
| `pipeline_version` | NonEmptyString | no | intake | none — semver of rules + prompts |
| `observed_at` | ISOTimestamp | no | intake | none |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `dataset_split` | `"sample"` \| `"test"` | yes | intake | none |
| `case_folder` | NonEmptyString | yes | derived | none — e.g. `case_001` from path |

### Validation rules

1. `len(image_paths) == len(image_ids) == len(resolved_image_files) == image_count`.
2. Each `resolved_image_file` must exist at intake time or intake fails fast.
3. `claim_object` must be one of `ClaimObject`.
4. If `history_flags` contains only `none`, treat as no history risk flags.
5. `user_claim` must not be empty or whitespace.

### Example instance

```json
{
  "row_id": "user_001:case_001",
  "user_id": "user_001",
  "claim_object": "car",
  "user_claim": "Customer: ... rear bumper area ...",
  "image_paths": ["images/sample/case_001/img_1.jpg"],
  "image_ids": ["img_1"],
  "image_count": 1,
  "resolved_image_files": ["/data/images/sample/case_001/img_1.jpg"],
  "history_flags": ["none"],
  "history_summary": "Low-risk user with prior accepted car damage claims",
  "past_claim_count": 2,
  "accept_claim": 2,
  "manual_review_claim": 0,
  "rejected_claim": 0,
  "last_90_days_claim_count": 1,
  "applicable_requirement_ids": ["REQ_GENERAL_OBJECT_PART", "REQ_REVIEW_TRUST"],
  "pipeline_version": "1.0.0",
  "observed_at": "2026-06-19T21:00:00+05:30",
  "dataset_split": "sample",
  "case_folder": "case_001"
}
```

---

## 2. ClaimResolutionContext

### Purpose

Result of multi-part claim resolution (decision_matrix §7). Selects single `primary_object_part` and `primary_issue_family` for all downstream matrices.

### Producer

`ResolveClaim` module

### Consumers

`ImageObserver` (re-score `claimed_primary_part_visible` per image), `ConsistencyContext` builder, `ValidationContext`, `DecisionContext`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `multi_part_claim` | bool | no | derived | none |
| `primary_object_part` | ObjectPart | no | rule_engine | none — MP-1..MP-5 |
| `primary_issue_family` | IssueFamily | no | rule_engine | none — from §0.4 mapping |
| `secondary_object_parts` | list[ObjectPart] | no | rule_engine | none — may be empty |
| `resolution_method` | `"single_part"` \| `"visibility_score"` \| `"last_mention_tiebreak"` | no | rule_engine | none |
| `alleged_parts` | list[ObjectPart] | no | claim_observer | none — all customer-affirmed parts |
| `identity_constraint_active` | bool | no | claim_observer | none |
| `identity_side` | IdentitySide | yes | claim_observer | none — required if side explicitly claimed |
| `identity_color` | NonEmptyString | yes | claim_observer | none |
| `claimed_damage_absent` | bool | no | claim_observer | none — true when physical damage alleged |
| `claimed_severity_language` | ClaimedSeverityLanguage | no | claim_observer | none — for CS-R06 only |
| `alleged_issue_types` | list[IssueType] | no | claim_observer | none — normalized alleged types |
| `resolution_rule_ids` | list[RuleId] | no | rule_engine | none — e.g. `["MP-2"]` |
| `part_visibility_scores` | map[ObjectPart → int] | no | derived | none — high=3, medium=2, low=1, absent=0 |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `last_customer_message_excerpt` | NonEmptyString | yes | claim_observer | none — for audit tie-break |

### Validation rules

1. `primary_object_part` ∈ alleged_parts when `multi_part_claim = true`.
2. `primary_object_part` must be valid for `claim_object`.
3. `secondary_object_parts` = `alleged_parts \ {primary_object_part}`.
4. `primary_issue_family` must be compatible with `primary_object_part` per §0.3/§0.4.
5. If `identity_constraint_active = true` and `claim_object = car`, append `REQ_CAR_IDENTITY_OR_SIDE` to active requirements (stored in downstream `ValidationContext`).

### Example instance

```json
{
  "row_id": "user_001:case_001",
  "multi_part_claim": false,
  "primary_object_part": "rear_bumper",
  "primary_issue_family": "dent_or_scratch",
  "secondary_object_parts": [],
  "resolution_method": "single_part",
  "alleged_parts": ["rear_bumper"],
  "identity_constraint_active": false,
  "identity_side": null,
  "identity_color": null,
  "claimed_damage_absent": true,
  "claimed_severity_language": "medium",
  "alleged_issue_types": ["dent"],
  "resolution_rule_ids": ["MP-2"],
  "part_visibility_scores": { "rear_bumper": 3 }
}
```

---

## 3. ImageEvidence

### Purpose

Normalized per-image visual observations from Gemini Pro. One instance per `image_id`. No verdict fields.

### Producer

`ImageObserver` + ontology normalization gate

### Consumers

`ResolveClaim` (visibility scores), `ConsistencyContext` builder, `ValidationContext`, `TrustAssessmentContext`, `DecisionContext`, `RiskContext`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `image_id` | NonEmptyString | no | ClaimContext | none |
| `image_path` | NonEmptyString | no | ClaimContext | none |
| `file_readable` | bool | no | image_observer | none |
| `usable_for_automated_review` | bool | no | image_observer | none |
| `depicts_claim_object` | ScoredField[bool] | no | image_observer | required |
| `visible_part` | ScoredField[ObjectPart] | no | image_observer | required, min_medium for decisions |
| `claimed_primary_part_visible` | ScoredField[bool] | no | image_observer | required — evaluated against `ClaimResolutionContext.primary_object_part` |
| `visible_issue_type` | ScoredField[IssueType] | no | image_observer | required, min_medium for decisions |
| `visible_damage_extent` | ScoredField[DamageExtent] | no | image_observer | required |
| `is_blurry` | ScoredField[bool] | no | image_observer | required, min_medium for risk flags |
| `is_cropped_or_obstructed` | ScoredField[bool] | no | image_observer | required, min_medium |
| `is_low_light_or_glare` | ScoredField[bool] | no | image_observer | required, min_medium |
| `is_wrong_angle_for_claimed_part` | ScoredField[bool] | no | image_observer | required, min_medium |
| `is_non_original_image` | ScoredField[bool] | no | image_observer | required, min_high for trust |
| `is_possibly_manipulated` | ScoredField[bool] | no | image_observer | required, min_high |
| `has_instruction_text` | ScoredField[bool] | no | image_observer | required, min_medium |
| `package_is_opened` | ScoredField[bool] | no | image_observer | required — false non-package |
| `contents_area_visible` | ScoredField[bool] | no | image_observer | required — false non-package |
| `vehicle_identity_features` | list[NonEmptyString] | no | image_observer | none — empty unless car; tokens like `color:blue` |
| `model_name` | NonEmptyString | no | image_observer | none — e.g. `gemini-2.5-pro` |
| `prompt_version` | NonEmptyString | no | image_observer | none |
| `observed_at` | ISOTimestamp | no | image_observer | none |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `observation_raw_hash` | NonEmptyString | yes | image_observer | none — hash of raw model JSON for reproducibility |
| `injection_text_excerpt` | NonEmptyString | yes | image_observer | none — redacted snippet if `has_instruction_text` |

### Validation rules

1. `image_id` must match `ClaimContext.image_ids` entry.
2. If `file_readable = false`, all `ScoredField` confidences must be `low` and bool values false except `file_readable`.
3. `visible_part.value` must be valid for row `claim_object`.
4. `visible_issue_type.value` must be valid `IssueType`.
5. Authenticity flags (`is_non_original_image`, `is_possibly_manipulated`) affect `TrustAssessmentContext` only at `confidence = high`.
6. `vehicle_identity_features` required non-empty when car wide-shot and `depicts_claim_object.value = true` at medium+.

### Example instance

```json
{
  "row_id": "user_001:case_001",
  "image_id": "img_1",
  "image_path": "images/sample/case_001/img_1.jpg",
  "file_readable": true,
  "usable_for_automated_review": true,
  "depicts_claim_object": { "value": true, "confidence": "high", "confidence_score": 0.96, "source_module": "image_observer", "source_image_id": "img_1" },
  "visible_part": { "value": "rear_bumper", "confidence": "high", "confidence_score": 0.94, "source_module": "image_observer", "source_image_id": "img_1" },
  "claimed_primary_part_visible": { "value": true, "confidence": "high", "confidence_score": 0.94, "source_module": "image_observer", "source_image_id": "img_1" },
  "visible_issue_type": { "value": "dent", "confidence": "high", "confidence_score": 0.91, "source_module": "image_observer", "source_image_id": "img_1" },
  "visible_damage_extent": { "value": "medium", "confidence": "high", "confidence_score": 0.88, "source_module": "image_observer", "source_image_id": "img_1" },
  "is_blurry": { "value": false, "confidence": "high", "confidence_score": 0.99, "source_module": "image_observer", "source_image_id": "img_1" },
  "is_cropped_or_obstructed": { "value": false, "confidence": "high", "confidence_score": 0.98, "source_module": "image_observer", "source_image_id": "img_1" },
  "is_low_light_or_glare": { "value": false, "confidence": "high", "confidence_score": 0.97, "source_module": "image_observer", "source_image_id": "img_1" },
  "is_wrong_angle_for_claimed_part": { "value": false, "confidence": "high", "confidence_score": 0.95, "source_module": "image_observer", "source_image_id": "img_1" },
  "is_non_original_image": { "value": false, "confidence": "high", "confidence_score": 0.92, "source_module": "image_observer", "source_image_id": "img_1" },
  "is_possibly_manipulated": { "value": false, "confidence": "medium", "confidence_score": 0.75, "source_module": "image_observer", "source_image_id": "img_1" },
  "has_instruction_text": { "value": false, "confidence": "high", "confidence_score": 0.99, "source_module": "image_observer", "source_image_id": "img_1" },
  "package_is_opened": { "value": false, "confidence": "high", "confidence_score": 0.99, "source_module": "image_observer", "source_image_id": "img_1" },
  "contents_area_visible": { "value": false, "confidence": "high", "confidence_score": 0.99, "source_module": "image_observer", "source_image_id": "img_1" },
  "vehicle_identity_features": ["color:silver", "body_style:sedan"],
  "model_name": "gemini-2.5-pro",
  "prompt_version": "vision-v1",
  "observed_at": "2026-06-19T21:00:01+05:30"
}
```

---

## 4. EvidenceContext

### Purpose

Aggregate bundle after claim and image observation, before deterministic reconciliation. Single object passed into resolution and consistency layers.

### Producer

`Observe` module (composes intake + Flash output + ImageEvidence list)

### Consumers

`ResolveClaim`, `ConsistencyContext` builder, `EvaluationRecord` (observation quality)

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `claim` | ClaimContext | no | intake | none |
| `images` | list[ImageEvidence] | no | image_observer | none — length = `claim.image_count` |
| `claim_observation_model` | NonEmptyString | no | claim_observer | none |
| `claim_observation_prompt_version` | NonEmptyString | no | claim_observer | none |
| `claim_observation_at` | ISOTimestamp | no | claim_observer | none |
| `alleged_parts_unresolved` | list[ObjectPart] | no | claim_observer | none — before MP resolution |
| `alleged_issue_types` | list[IssueType] | no | claim_observer | none |
| `exclusions` | list[NonEmptyString] | no | claim_observer | none — e.g. "not keyboard" |
| `injection_detected_in_chat` | bool | no | claim_observer | none — adversarial sanitizer |
| `injection_excerpt` | NonEmptyString | yes | claim_observer | none — if detected |
| `observation_complete` | bool | no | derived | none — all images readable or failed explicitly |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `detected_languages` | list[NonEmptyString] | yes | claim_observer | none — e.g. `["en"]`, `["hi","en"]` |

### Validation rules

1. `len(images) == claim.image_count`.
2. Image `row_id` must equal `claim.row_id`.
3. No field in `EvidenceContext` may contain `claim_status`, `evidence_standard_met`, `risk_flags`, or `severity`.
4. If `injection_detected_in_chat = true`, downstream rules must ignore injected directives (document in `DecisionTrace`).

### Example instance

```json
{
  "claim": { "...": "ClaimContext for user_001" },
  "images": [{ "...": "ImageEvidence img_1" }],
  "claim_observation_model": "gemini-2.5-flash",
  "claim_observation_prompt_version": "claim-v1",
  "claim_observation_at": "2026-06-19T21:00:01+05:30",
  "alleged_parts_unresolved": ["rear_bumper"],
  "alleged_issue_types": ["dent"],
  "exclusions": [],
  "injection_detected_in_chat": false,
  "injection_excerpt": null,
  "observation_complete": true,
  "detected_languages": ["en"]
}
```

---

## 5. ValidationContext

### Purpose

Output of evidence sufficiency matrix (§1). Encodes `evidence_standard_met` and requirement satisfaction audit.

### Producer

`ReconcileEvidence` / sufficiency submodule

### Consumers

`TrustAssessmentContext` builder, `DecisionContext`, `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `evidence_standard_met` | bool | no | rule_engine | none |
| `triggered_rule_id` | RuleId | no | rule_engine | none — ESM-R01..ESM-R08 |
| `reason_template_key` | NonEmptyString | no | rule_engine | none — §1.3 key |
| `reason_template_vars` | map[string → string] | no | rule_engine | none — `{part, detail, issue_noun}` |
| `active_requirement_ids` | list[RequirementId] | no | rule_engine | none |
| `requirements_satisfied` | map[RequirementId → bool] | no | rule_engine | none |
| `predicates` | ValidationPredicates | no | derived | none — see nested contract below |
| `evaluated_at` | ISOTimestamp | no | rule_engine | none |

### Nested: `ValidationPredicates`

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `part_clear` | bool | no | derived | none |
| `no_part_visible` | bool | no | derived | none |
| `part_visible_low_only` | bool | no | derived | none |
| `identity_conflict` | bool | no | derived | none |
| `contents_claim` | bool | no | derived | none |
| `contents_area_clear` | bool | no | derived | none |
| `any_file_unreadable` | bool | no | derived | none |
| `best_part_confidence` | ConfidenceLevel | no | derived | none |
| `best_part_image_ids` | list[NonEmptyString] | no | derived | none |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `identity_match_detail` | NonEmptyString | yes | rule_engine | none — for ESM-R02/R07 reasons |

### Validation rules

1. If `triggered_rule_id` in `ESM-R01`..`ESM-R07` then `evidence_standard_met = false`; if `ESM-R08` then `true`.
2. `requirements_satisfied` must include every id in `active_requirement_ids`.
3. `predicates.identity_conflict = true` implies `triggered_rule_id = ESM-R02` when no higher-priority ESM rule matches.
4. HR-01: `evidence_standard_met = false` must not pair with downstream `claim_status` other than `not_enough_information` (enforced in `DecisionContext`).

### Example instance

```json
{
  "row_id": "user_001:case_001",
  "evidence_standard_met": true,
  "triggered_rule_id": "ESM-R08",
  "reason_template_key": "ESM-R08_SINGLE",
  "reason_template_vars": { "part": "rear_bumper", "detail": "the dent can be verified from the submitted image" },
  "active_requirement_ids": ["REQ_GENERAL_OBJECT_PART", "REQ_REVIEW_TRUST", "REQ_CAR_BODY_PANEL"],
  "requirements_satisfied": { "REQ_GENERAL_OBJECT_PART": true, "REQ_REVIEW_TRUST": true, "REQ_CAR_BODY_PANEL": true },
  "predicates": {
    "part_clear": true,
    "no_part_visible": false,
    "part_visible_low_only": false,
    "identity_conflict": false,
    "contents_claim": false,
    "contents_area_clear": false,
    "any_file_unreadable": false,
    "best_part_confidence": "high",
    "best_part_image_ids": ["img_1"]
  },
  "evaluated_at": "2026-06-19T21:00:02+05:30"
}
```

---

## 6. TrustAssessmentContext

### Purpose

Output of valid image matrix (§2). Separates automation trust from evaluative sufficiency.

### Producer

`ReconcileEvidence` / trust submodule

### Consumers

`DecisionContext`, `RiskContext`, `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `valid_image` | bool | no | rule_engine | none |
| `triggered_rule_id` | RuleId | no | rule_engine | none — VI-R01..VI-R04 |
| `all_images_unusable` | bool | no | derived | none |
| `any_non_original_high` | bool | no | derived | none |
| `contents_unreviewable` | bool | no | derived | none — VI-R03 predicate |
| `trust_failure_image_ids` | list[NonEmptyString] | no | derived | none — may be empty |
| `evaluated_at` | ISOTimestamp | no | rule_engine | none |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `trust_failure_reason` | NonEmptyString | yes | rule_engine | none — human-readable |

### Validation rules

1. `any_non_original_high = true` implies `valid_image = false` and `triggered_rule_id = VI-R02`.
2. `valid_image` may be `false` while `ValidationContext.evidence_standard_met = true` (see `user_008`).
3. Trust assessment MUST NOT read `RiskContext` or `ClaimDecision`.

### Example instance

```json
{
  "row_id": "user_008:case_008",
  "valid_image": false,
  "triggered_rule_id": "VI-R02",
  "all_images_unusable": false,
  "any_non_original_high": true,
  "contents_unreviewable": false,
  "trust_failure_image_ids": ["img_1"],
  "evaluated_at": "2026-06-19T21:00:02+05:30",
  "trust_failure_reason": "non_original_image at high confidence"
}
```

---

## 7. ConsistencyContext

### Purpose

Cross-image reconciliation predicates consumed by sufficiency, status, and risk modules.

### Producer

`ReconcileEvidence` / consistency submodule

### Consumers

`ValidationContext` builder, `DecisionContext`, `RiskContext`, `DecisionTrace`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `image_count` | int | no | ClaimContext | none |
| `identity_conflict` | bool | no | rule_engine | none |
| `identity_conflict_image_pairs` | list[ImagePairConflict] | no | rule_engine | none — empty if no conflict |
| `wrong_object_set` | bool | no | rule_engine | none |
| `consistent_vehicle_features` | bool | no | rule_engine | none — cars only; true if N/A |
| `best_part_image_ids` | list[NonEmptyString] | no | derived | none |
| `evaluated_at` | ISOTimestamp | no | rule_engine | none |

### Nested: `ImagePairConflict`

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `image_id_a` | NonEmptyString | no | rule_engine | none |
| `image_id_b` | NonEmptyString | no | rule_engine | none |
| `conflicting_features` | list[NonEmptyString] | no | rule_engine | none |
| `confidence` | ConfidenceLevel | no | rule_engine | required, min_high for identity_conflict=true |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `consistency_notes` | NonEmptyString | yes | rule_engine | none |

### Validation rules

1. `identity_conflict = true` only if `image_count ≥ 2` and `claim_object = car`.
2. `identity_conflict_image_pairs` non-empty when `identity_conflict = true`.
3. `wrong_object_set` and `identity_conflict` may both be true.

### Example instance

```json
{
  "row_id": "user_002:case_002",
  "image_count": 2,
  "identity_conflict": true,
  "identity_conflict_image_pairs": [
    {
      "image_id_a": "img_1",
      "image_id_b": "img_2",
      "conflicting_features": ["color:silver", "color:red"],
      "confidence": "high"
    }
  ],
  "wrong_object_set": false,
  "consistent_vehicle_features": false,
  "best_part_image_ids": ["img_1"],
  "evaluated_at": "2026-06-19T21:00:02+05:30"
}
```

---

## 8. RiskContext

### Purpose

Output of risk flag matrix (§6). Produced **after** `ClaimDecision`. Must not influence verdict fields.

### Producer

`AssessRisk` module

### Consumers

`Explain`, `Emit`, `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `risk_flags` | list[RiskFlag] | no | rule_engine | none — sorted unique; `["none"]` if empty |
| `flag_rule_hits` | list[FlagRuleHit] | no | rule_engine | none — audit per flag |
| `manual_review_required` | bool | no | rule_engine | none — derived from MRR-1..MRR-6 |
| `manual_review_rule_ids` | list[RuleId] | no | rule_engine | none |
| `history_flags_input` | list[HistoryFlag] | no | ClaimContext | none |
| `evaluated_at` | ISOTimestamp | no | rule_engine | none |

### Nested: `FlagRuleHit`

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `flag` | RiskFlag | no | rule_engine | none |
| `rule_id` | NonEmptyString | no | rule_engine | none — e.g. `blurry_image`, `MRR-2` |
| `trigger_image_ids` | list[NonEmptyString] | no | rule_engine | none |
| `min_confidence_met` | bool | no | rule_engine | none |

### Validation rules

1. `risk_flags` must not contain `none` alongside other flags.
2. If list empty after evaluation, set `risk_flags = ["none"]`.
3. `user_history_risk` present iff `history_flags_input` contains `user_history_risk` (HR-04).
4. `manual_review_required` in flags iff `manual_review_required = true`.
5. Risk module MUST NOT mutate `ClaimDecision` fields.

### Example instance

```json
{
  "row_id": "user_005:case_005",
  "risk_flags": ["claim_mismatch", "manual_review_required", "user_history_risk"],
  "flag_rule_hits": [
    { "flag": "claim_mismatch", "rule_id": "CS-R06", "trigger_image_ids": ["img_1"], "min_confidence_met": true },
    { "flag": "user_history_risk", "rule_id": "RF-1", "trigger_image_ids": [], "min_confidence_met": true },
    { "flag": "manual_review_required", "rule_id": "MRR-2", "trigger_image_ids": [], "min_confidence_met": true }
  ],
  "manual_review_required": true,
  "manual_review_rule_ids": ["MRR-2", "MRR-4"],
  "history_flags_input": ["user_history_risk"],
  "evaluated_at": "2026-06-19T21:00:03+05:30"
}
```

---

## 9. DecisionContext

### Purpose

Immutable input snapshot for the `Decide` module (status, severity, supporting IDs). Aggregates all upstream contexts required by §3–§5.

### Producer

`Decide` module preprocessor (aggregator)

### Consumers

`Decide` (verdict/severity/supporting), `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `claim` | ClaimContext | no | intake | none |
| `resolution` | ClaimResolutionContext | no | ResolveClaim | none |
| `images` | list[ImageEvidence] | no | image_observer | none |
| `consistency` | ConsistencyContext | no | consistency | none |
| `validation` | ValidationContext | no | sufficiency | none |
| `trust` | TrustAssessmentContext | no | trust | none |
| `evidence_standard_met` | bool | no | ValidationContext | none — copied for convenience |
| `valid_image` | bool | no | TrustAssessmentContext | none — copied for convenience |
| `aggregated_at` | ISOTimestamp | no | derived | none |

### Validation rules

1. All nested `row_id` values must match.
2. `evidence_standard_met` must equal `validation.evidence_standard_met`.
3. `valid_image` must equal `trust.valid_image`.
4. No `RiskContext` or `ClaimDecision` present at construction (prevents circular dependency).

### Example instance

```json
{
  "row_id": "user_001:case_001",
  "claim": { "...": "ClaimContext" },
  "resolution": { "...": "ClaimResolutionContext" },
  "images": [{ "...": "ImageEvidence" }],
  "consistency": { "...": "ConsistencyContext" },
  "validation": { "...": "ValidationContext" },
  "trust": { "...": "TrustAssessmentContext" },
  "evidence_standard_met": true,
  "valid_image": true,
  "aggregated_at": "2026-06-19T21:00:02+05:30"
}
```

---

## 10. ClaimDecision

### Purpose

All deterministic verdict outputs from §3–§5 before risk and prose composition. Maps directly to `output.csv` prediction columns (excluding passthrough and `risk_flags`).

### Producer

`Decide` module

### Consumers

`AssessRisk`, `Explain`, `Emit`, `DecisionTrace`, `EvaluationRecord`

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `claim_status` | ClaimStatus | no | rule_engine | none |
| `claim_status_rule_id` | RuleId | no | rule_engine | none — CS-R01..CS-R08 |
| `issue_type` | IssueType | no | rule_engine | none |
| `object_part` | ObjectPart | no | rule_engine | none |
| `severity` | Severity | no | rule_engine | none |
| `severity_rule_id` | RuleId | no | rule_engine | none — SV-R01..SV-R08 |
| `supporting_image_ids` | list[NonEmptyString] | no | rule_engine | none — empty list means output `none` |
| `supporting_image_rule_id` | RuleId | no | rule_engine | none — SI-R01..SI-R07 |
| `evidence_standard_met` | bool | no | ValidationContext | none — copy |
| `evidence_standard_met_reason` | NonEmptyString | no | rule_engine | none — rendered template |
| `valid_image` | bool | no | TrustAssessmentContext | none — copy |
| `claim_status_justification` | NonEmptyString | no | rule_engine | none — rendered template |
| `decided_at` | ISOTimestamp | no | rule_engine | none |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `contradiction_subtype` | `"wrong_object"` \| `"wrong_part"` \| `"absent_damage"` \| `"severity_exaggeration"` \| `"issue_family_mismatch"` | yes | rule_engine | none — audit only |

### Validation rules

1. HR-01: `evidence_standard_met = false` ⟹ `claim_status = not_enough_information`.
2. HR-02: `claim_status = contradicted` ⟹ `evidence_standard_met = true`.
3. HR-03: `claim_status = not_enough_information` ⟹ `severity = unknown`.
4. SV-02: `issue_type = none` ⟹ `severity = none`.
5. `object_part` valid for `claim_object`.
6. `supporting_image_ids` subset of `ClaimContext.image_ids`.
7. If `supporting_image_ids` empty, CSV emitter writes `none`.

### Example instance

```json
{
  "row_id": "user_001:case_001",
  "claim_status": "supported",
  "claim_status_rule_id": "CS-R07",
  "issue_type": "dent",
  "object_part": "rear_bumper",
  "severity": "medium",
  "severity_rule_id": "SV-R05",
  "supporting_image_ids": ["img_1"],
  "supporting_image_rule_id": "SI-R03",
  "evidence_standard_met": true,
  "evidence_standard_met_reason": "The rear bumper is visible and the dent can be verified from the submitted image.",
  "valid_image": true,
  "claim_status_justification": "The image clearly shows a dent on the rear bumper and the user history does not add risk.",
  "decided_at": "2026-06-19T21:00:03+05:30"
}
```

---

## 11. DecisionTrace

### Purpose

Complete audit record for one claim row. Enables reproducibility, explainability, and judge interview. One trace per pipeline run.

### Producer

Pipeline orchestrator (accumulates rule hits from all modules)

### Consumers

`Explain` (debug), `EvaluationRecord`, optional trace export, judge interview

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `pipeline_version` | NonEmptyString | no | ClaimContext | none |
| `claim` | ClaimContext | no | intake | none |
| `evidence` | EvidenceContext | no | observe | none |
| `resolution` | ClaimResolutionContext | no | ResolveClaim | none |
| `consistency` | ConsistencyContext | no | consistency | none |
| `validation` | ValidationContext | no | sufficiency | none |
| `trust` | TrustAssessmentContext | no | trust | none |
| `decision` | ClaimDecision | no | Decide | none |
| `risk` | RiskContext | no | AssessRisk | none |
| `rule_hits_ordered` | list[RuleHit] | no | rule_engine | none — chronological |
| `started_at` | ISOTimestamp | no | pipeline | none |
| `completed_at` | ISOTimestamp | no | pipeline | none |
| `deterministic_hash` | NonEmptyString | no | derived | none — hash of all rule inputs + outputs |

### Nested: `RuleHit`

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `sequence` | int | no | pipeline | none |
| `stage` | `"resolve"` \| `"consistency"` \| `"validation"` \| `"trust"` \| `"decide"` \| `"risk"` \| `"explain"` | no | pipeline | none |
| `rule_id` | RuleId | no | rule_engine | none |
| `matched` | bool | no | rule_engine | none |
| `inputs_snapshot` | map[string → string] | no | rule_engine | none — stringified predicate values |
| `outputs_snapshot` | map[string → string] | no | rule_engine | none |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `model_call_counts` | map[string → int] | yes | pipeline | none — `flash_calls`, `pro_calls` |
| `token_usage` | map[string → int] | yes | pipeline | none — input/output tokens |

### Validation rules

1. `completed_at >= started_at`.
2. `deterministic_hash` must change if any observation or rule version changes.
3. Trace must contain at least one `RuleHit` per stage executed.
4. Secrets and raw image bytes must not appear in trace.

### Example instance

```json
{
  "row_id": "user_001:case_001",
  "pipeline_version": "1.0.0",
  "claim": { "...": "ClaimContext" },
  "evidence": { "...": "EvidenceContext" },
  "resolution": { "...": "ClaimResolutionContext" },
  "consistency": { "...": "ConsistencyContext" },
  "validation": { "...": "ValidationContext" },
  "trust": { "...": "TrustAssessmentContext" },
  "decision": { "...": "ClaimDecision" },
  "risk": { "...": "RiskContext" },
  "rule_hits_ordered": [
    { "sequence": 1, "stage": "resolve", "rule_id": "MP-2", "matched": true, "inputs_snapshot": { "alleged_parts_count": "1" }, "outputs_snapshot": { "primary_object_part": "rear_bumper" } },
    { "sequence": 2, "stage": "validation", "rule_id": "ESM-R08", "matched": true, "inputs_snapshot": { "part_clear": "true" }, "outputs_snapshot": { "evidence_standard_met": "true" } }
  ],
  "started_at": "2026-06-19T21:00:00+05:30",
  "completed_at": "2026-06-19T21:00:03+05:30",
  "deterministic_hash": "sha256:abc123...",
  "model_call_counts": { "flash_calls": 1, "pro_calls": 1 }
}
```

---

## 12. EvaluationRecord

### Purpose

Offline comparison of system output against labeled `sample_claims.csv` (or holdout). Supports strategy A/B and operational reporting.

### Producer

`EvaluationHarness` module

### Consumers

`evaluation_report.md` generator, CI, judge review

### Required fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `record_id` | NonEmptyString | no | evaluation | none |
| `row_id` | NonEmptyString | no | ClaimContext | none |
| `strategy_id` | NonEmptyString | no | evaluation | none — e.g. `baseline-v1`, `vision-v2` |
| `predicted` | OutputRowSnapshot | no | Emit | none |
| `expected` | OutputRowSnapshot | yes | sample_claims | none — null for test split |
| `field_matches` | map[string → bool] | yes | evaluation | none — per output column |
| `claim_status_match` | bool | yes | evaluation | none |
| `evidence_standard_met_match` | bool | yes | evaluation | none |
| `risk_flags_f1` | float | yes | evaluation | none — 0.0..1.0 per row |
| `weighted_score` | float | yes | evaluation | none — per architecture_review weights |
| `trace_hash` | NonEmptyString | no | DecisionTrace | none |
| `evaluated_at` | ISOTimestamp | no | evaluation | none |

### Nested: `OutputRowSnapshot`

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `evidence_standard_met` | bool | no | ClaimDecision | none |
| `evidence_standard_met_reason` | NonEmptyString | no | ClaimDecision | none |
| `risk_flags` | SemicolonList | no | RiskContext | none |
| `issue_type` | IssueType | no | ClaimDecision | none |
| `object_part` | ObjectPart | no | ClaimDecision | none |
| `claim_status` | ClaimStatus | no | ClaimDecision | none |
| `claim_status_justification` | NonEmptyString | no | ClaimDecision | none |
| `supporting_image_ids` | SemicolonList | no | ClaimDecision | none |
| `valid_image` | bool | no | ClaimDecision | none |
| `severity` | Severity | no | ClaimDecision | none |

### Optional fields

| Field | Type | Nullable | Source | Confidence |
|-------|------|----------|--------|------------|
| `failure_categories` | list[NonEmptyString] | yes | evaluation | none — e.g. `status_wrong`, `flag_missing` |
| `latency_ms` | int | yes | pipeline | none |
| `model_calls` | int | yes | pipeline | none |
| `token_input` | int | yes | pipeline | none |
| `token_output` | int | yes | pipeline | none |

### Validation rules

1. `expected` required when `dataset_split = sample`.
2. `weighted_score` computed only when `expected` present.
3. `predicted.risk_flags` derived from `RiskContext`, not `ClaimDecision`.
4. Multiple `EvaluationRecord` rows may share `row_id` with different `strategy_id` (A/B comparison).

### Example instance

```json
{
  "record_id": "eval-user_001-baseline-v1",
  "row_id": "user_001:case_001",
  "strategy_id": "baseline-v1",
  "predicted": {
    "evidence_standard_met": true,
    "evidence_standard_met_reason": "The rear bumper is visible and the dent can be verified from the submitted image.",
    "risk_flags": "none",
    "issue_type": "dent",
    "object_part": "rear_bumper",
    "claim_status": "supported",
    "claim_status_justification": "The image clearly shows a dent on the rear bumper and the user history does not add risk.",
    "supporting_image_ids": "img_1",
    "valid_image": true,
    "severity": "medium"
  },
  "expected": {
    "evidence_standard_met": true,
    "evidence_standard_met_reason": "The rear bumper is visible and the dent can be verified from the submitted image.",
    "risk_flags": "none",
    "issue_type": "dent",
    "object_part": "rear_bumper",
    "claim_status": "supported",
    "claim_status_justification": "The image clearly shows a dent on the rear bumper and the user history does not add risk.",
    "supporting_image_ids": "img_1",
    "valid_image": true,
    "severity": "medium"
  },
  "field_matches": {
    "claim_status": true,
    "evidence_standard_met": true,
    "severity": true,
    "risk_flags": true,
    "supporting_image_ids": true
  },
  "claim_status_match": true,
  "evidence_standard_met_match": true,
  "risk_flags_f1": 1.0,
  "weighted_score": 1.0,
  "trace_hash": "sha256:abc123...",
  "evaluated_at": "2026-06-19T21:05:00+05:30"
}
```

---

## Contract Dependency Matrix

| Contract | Depends on | Must not depend on |
|----------|------------|-------------------|
| ClaimContext | — | any model output |
| EvidenceContext | ClaimContext | ValidationContext, ClaimDecision |
| ClaimResolutionContext | EvidenceContext, ImageEvidence[] | ValidationContext, ClaimDecision |
| ImageEvidence | ClaimContext, ClaimResolutionContext (for primary part fields) | ClaimDecision |
| ConsistencyContext | EvidenceContext, ClaimResolutionContext | ClaimDecision, RiskContext |
| ValidationContext | ConsistencyContext, ClaimResolutionContext, ImageEvidence[] | ClaimDecision, RiskContext |
| TrustAssessmentContext | ImageEvidence[], ClaimResolutionContext | ClaimDecision, RiskContext |
| DecisionContext | all upstream through Trust | RiskContext, ClaimDecision |
| ClaimDecision | DecisionContext | RiskContext |
| RiskContext | ClaimDecision, EvidenceContext, ConsistencyContext, ClaimContext | — (terminal for flags) |
| DecisionTrace | all contracts | — |
| EvaluationRecord | ClaimDecision, RiskContext, DecisionTrace, gold label | — |

---

## Execution Order Enforcement

Modules MUST construct contracts in this order (matches [decision_matrix.md](decision_matrix.md)):

| Step | Module | Output contract |
|------|--------|-----------------|
| 1 | Intake | `ClaimContext` |
| 2 | Observe | `EvidenceContext`, `ImageEvidence[]` |
| 3 | ResolveClaim | `ClaimResolutionContext` |
| 4 | Reconcile / Consistency | `ConsistencyContext` |
| 5 | Reconcile / Sufficiency | `ValidationContext` |
| 6 | Reconcile / Trust | `TrustAssessmentContext` |
| 7 | Aggregate | `DecisionContext` |
| 8 | Decide | `ClaimDecision` |
| 9 | AssessRisk | `RiskContext` |
| 10 | Orchestrator | `DecisionTrace` |
| 11 | Evaluation (offline) | `EvaluationRecord` |

---

## Anti-Patterns (Forbidden)

1. Passing `dict[str, Any]` between modules — use contracts above.
2. Storing `claim_status` or `risk_flags` inside `ImageEvidence` or `EvidenceContext`.
3. Reading `RiskContext` before `ClaimDecision` is finalized.
4. Using `claimed_severity_language` in `ClaimDecision.severity`.
5. Omitting `confidence` on any `ScoredField` used by decision rules.
6. Writing `risk_flags` into `ClaimDecision` — flags live only in `RiskContext`.

---

## Versioning

| Field | Location | Rule |
|-------|----------|------|
| `pipeline_version` | ClaimContext | Bump when any rule matrix or contract validation changes |
| `prompt_version` | ImageEvidence, EvidenceContext | Bump when observation prompts change |
| `deterministic_hash` | DecisionTrace | Must incorporate `pipeline_version` + `prompt_version` + observations + rule hits |
