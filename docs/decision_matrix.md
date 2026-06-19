# Decision Matrix Specification

**Status:** Normative — implement exactly as written  
**Audience:** Engineers implementing deterministic rule layers  
**Sources:** `problem_statement.md`, `evidence_requirements.csv`, `sample_claims.csv` (20 rows), `architect_prompt.md`, `problem_decomposition.md`, `architecture_review.md`  
**Prerequisite inputs:** Structured observations only (no LLM verdict fields). See §0.

This document defines **all** deterministic decision logic. Observation models produce facts; these matrices produce output fields.

---

## 0. Input Vocabulary (Observation Contract)

All matrices consume normalized observations. No matrix may read raw chat text or pixels.

### 0.1 Per-image observations (one record per image ID)

| Field | Type | Values |
|-------|------|--------|
| `image_id` | string | e.g. `img_1` |
| `file_readable` | boolean | File loaded successfully |
| `depicts_claim_object` | boolean | Image shows `claim_object` type |
| `depicts_claim_object_confidence` | enum | `high`, `medium`, `low` |
| `visible_part` | enum | Allowed `object_part` for row's `claim_object`, or `unknown` |
| `visible_part_confidence` | enum | `high`, `medium`, `low` |
| `claimed_primary_part_visible` | boolean | Resolved primary part (§7) is in frame |
| `claimed_primary_part_confidence` | enum | `high`, `medium`, `low` |
| `visible_issue_type` | enum | Allowed `issue_type`, or `unknown` |
| `visible_issue_confidence` | enum | `high`, `medium`, `low` |
| `visible_damage_extent` | enum | `none`, `low`, `medium`, `high`, `unknown` |
| `is_blurry` | boolean | |
| `is_cropped_or_obstructed` | boolean | |
| `is_low_light_or_glare` | boolean | |
| `is_wrong_angle_for_claimed_part` | boolean | Part exists on object but framing prevents inspection |
| `is_non_original_image` | boolean | Screenshot, reshoot of screen, stock photo signal |
| `is_possibly_manipulated` | boolean | |
| `has_instruction_text` | boolean | Text in image instructing reviewer to approve/reject |
| `vehicle_identity_features` | set | e.g. `color:blue`, `body_style:suv` — cars only |
| `package_is_opened` | boolean | Contents area potentially visible |
| `contents_area_visible` | boolean | Inner cavity / items visible |
| `usable_for_automated_review` | boolean | Technically processable; not blank/corrupt |

### 0.2 Claim observations (one record per row, after §7 resolution)

| Field | Type | Values |
|-------|------|--------|
| `primary_object_part` | enum | Resolved single part |
| `primary_issue_family` | enum | See §0.3 |
| `secondary_parts` | list | Other alleged parts (multi-part rows) |
| `identity_constraint_active` | boolean | Claim mentions color, side, orientation, "my blue car", "left door" |
| `identity_color` | string or null | |
| `identity_side` | enum or null | `left`, `right`, `front`, `rear` |
| `claimed_damage_absent` | boolean | User alleges physical damage (not mere condition inquiry) |

### 0.3 Issue family enum (maps to `evidence_requirements.csv`)

| `primary_issue_family` | `claim_object` | Requirement IDs (in addition to universal) |
|------------------------|----------------|---------------------------------------------|
| `dent_or_scratch` | car | `REQ_CAR_BODY_PANEL` |
| `crack_broken_missing` | car | `REQ_CAR_GLASS_LIGHT_MIRROR` |
| `crushed_torn_seal` | package | `REQ_PACKAGE_EXTERIOR` |
| `water_stain_label` | package | `REQ_PACKAGE_LABEL_OR_STAIN` |
| `contents_or_item` | package | `REQ_PACKAGE_CONTENTS` |
| `screen_keyboard_trackpad` | laptop | `REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD` |
| `hinge_lid_corner_body_port` | laptop | `REQ_LAPTOP_BODY_HINGE_PORT` |

**Universal requirements (every row):** `REQ_GENERAL_OBJECT_PART`, `REQ_REVIEW_TRUST`  
**Multi-image rows (image count ≥ 2):** also `REQ_GENERAL_MULTI_IMAGE`  
**Car + `identity_constraint_active = true`:** also `REQ_CAR_IDENTITY_OR_SIDE`

### 0.4 Issue family mapping from alleged issue (deterministic)

| Alleged issue keywords / types | `primary_issue_family` |
|--------------------------------|------------------------|
| `dent`, `scratch` | `dent_or_scratch` |
| `crack`, `glass_shatter`, `broken_part`, `missing_part` on glass/light/mirror/headlight/taillight | `crack_broken_missing` |
| `crushed_packaging`, `torn_packaging` on exterior/seal | `crushed_torn_seal` |
| `water_damage`, `stain`, label unreadable | `water_stain_label` |
| `missing_part`, `contents`, `item`, missing product | `contents_or_item` |
| `crack`, `stain`, `glass_shatter` on screen; keyboard/trackpad damage | `screen_keyboard_trackpad` |
| `broken_part`, `dent` on hinge/lid/corner/body/port/base | `hinge_lid_corner_body_port` |

When multiple families apply, use the family of `primary_object_part` per §7.

### 0.5 Set-level derived predicates

| Predicate | Definition |
|-----------|------------|
| `IMAGE_COUNT` | Number of images in row |
| `ANY_FILE_UNREADABLE` | ∃ image: `file_readable = false` |
| `BEST_PART_CONFIDENCE` | max over images of `claimed_primary_part_confidence` (order: high > medium > low) |
| `BEST_PART_IMAGE_SET` | {image_id \| `claimed_primary_part_confidence` = BEST_PART_CONFIDENCE and ≥ medium} |
| `PART_CLEAR` | ∃ image: `claimed_primary_part_visible = true` AND `claimed_primary_part_confidence` ∈ {high, medium} |
| `PART_VISIBLE_LOW_ONLY` | `claimed_primary_part_visible = true` on some image but `BEST_PART_CONFIDENCE = low` |
| `NO_PART_VISIBLE` | ∀ images: `claimed_primary_part_visible = false` OR `claimed_primary_part_confidence = low` |
| `IDENTITY_CONFLICT` | `IMAGE_COUNT ≥ 2` AND `claim_object = car` AND ∃ images I,J: both `depicts_claim_object = true` with confidence ≥ medium, and `vehicle_identity_features` incompatible at confidence high |
| `WRONG_OBJECT_SET` | ∀ images with `depicts_claim_object_confidence ≥ medium`: `depicts_claim_object = false` OR visible object is not a package/car/laptop as claimed |
| `ANY_NON_ORIGINAL_HIGH` | ∃ image: `is_non_original_image = true` AND observation confidence high |
| `CONTENTS_CLAIM` | `primary_issue_family = contents_or_item` |
| `CONTENTS_AREA_CLEAR` | ∃ image: `package_is_opened = true` AND `contents_area_visible = true` AND confidence ≥ medium |
| `ALL_IMAGES_UNUSABLE` | ∀ images: `usable_for_automated_review = false` |

---

# 1. Evidence Sufficiency Matrix

**Outputs:** `evidence_standard_met` (boolean), `evidence_standard_met_reason` (string from template key)

## 1.1 Decision table — `evidence_standard_met`

Evaluate rows **top to bottom**; first matching row wins.

| Rule ID | Condition (ALL must hold if multiple) | `evidence_standard_met` |
|---------|----------------------------------------|-------------------------|
| ESM-R01 | `ANY_FILE_UNREADABLE = true` | `false` |
| ESM-R02 | `IDENTITY_CONFLICT = true` | `false` |
| ESM-R03 | `NO_PART_VISIBLE = true` | `false` |
| ESM-R04 | `CONTENTS_CLAIM = true` AND `CONTENTS_AREA_CLEAR = false` | `false` |
| ESM-R05 | `PART_VISIBLE_LOW_ONLY = true` AND no image with `claimed_primary_part_confidence = high` | `false` |
| ESM-R06 | `PART_CLEAR = false` | `false` |
| ESM-R07 | `identity_constraint_active = true` AND `claim_object = car` AND identity not matchable across `BEST_PART_IMAGE_SET` at confidence ≥ medium | `false` |
| ESM-R08 | Default (none of above) | `true` |

**Sample mapping:** `user_002`→ESM-R02, `user_006`→ESM-R03, `user_032`→ESM-R04, `user_003`→ESM-R08 (blurry compensated by clear image).

## 1.2 Requirement satisfaction sub-checks (informational; folded into rules above)

| Requirement ID | Satisfied when |
|----------------|----------------|
| `REQ_GENERAL_OBJECT_PART` | `PART_CLEAR = true` |
| `REQ_GENERAL_MULTI_IMAGE` | `IMAGE_COUNT < 2` OR (∃ image in `BEST_PART_IMAGE_SET`) |
| `REQ_REVIEW_TRUST` | ∃ image: `usable_for_automated_review = true` AND `depicts_claim_object = true` with confidence ≥ medium |
| `REQ_CAR_BODY_PANEL` | `primary_issue_family = dent_or_scratch` AND `PART_CLEAR` |
| `REQ_CAR_GLASS_LIGHT_MIRROR` | `primary_issue_family = crack_broken_missing` AND `PART_CLEAR` |
| `REQ_CAR_IDENTITY_OR_SIDE` | `identity_constraint_active = false` OR identity matchable |
| `REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD` | family `screen_keyboard_trackpad` AND `PART_CLEAR` |
| `REQ_LAPTOP_BODY_HINGE_PORT` | family `hinge_lid_corner_body_port` AND `PART_CLEAR` |
| `REQ_PACKAGE_EXTERIOR` | family `crushed_torn_seal` AND `PART_CLEAR` |
| `REQ_PACKAGE_LABEL_OR_STAIN` | family `water_stain_label` AND `PART_CLEAR` |
| `REQ_PACKAGE_CONTENTS` | `CONTENTS_AREA_CLEAR = true` |

## 1.3 `evidence_standard_met_reason` template keys

| Trigger rule | Template (fill `{part}`, `{detail}`) |
|--------------|----------------------------------------|
| ESM-R02 | `The image set does not satisfy vehicle identity evidence because {detail}.` |
| ESM-R03 | `The image does not show the {part}, so the claimed condition cannot be verified.` |
| ESM-R04 | `The images do not clearly show the expected contents or enough of the opened package to verify whether anything is missing.` |
| ESM-R05 | `The claimed {part} is not visible clearly enough to inspect the claimed condition.` |
| ESM-R06 | `The claimed {part} is not visible clearly enough to evaluate the claim.` |
| ESM-R07 | `The image set does not show enough context to match the claimed vehicle and part.` |
| ESM-R08 + multi-image | `One image is blurry, but the second image clearly shows the {part} {issue_noun}.` OR `{part} is visible and {detail}.` |
| ESM-R08 + single | `The {part} is visible and {detail}.` |

`{issue_noun}` = dent / crack / damage / staining / crushing per visible issue. `{detail}` = one factual clause from observations (no history).

---

# 2. Valid Image Matrix

**Output:** `valid_image` (boolean)

## 2.1 Definition

| Value | Formal definition |
|-------|-------------------|
| `valid_image = true` | `ALL_IMAGES_UNUSABLE = false` AND `ANY_NON_ORIGINAL_HIGH = false` AND NOT (`CONTENTS_CLAIM = true` AND `CONTENTS_AREA_CLEAR = false` AND ∀ images: `is_cropped_or_obstructed = true` with confidence high) |
| `valid_image = false` | Negation of above |

Equivalent decision table:

| Rule ID | Condition | `valid_image` |
|---------|-----------|---------------|
| VI-R01 | `ALL_IMAGES_UNUSABLE = true` | `false` |
| VI-R02 | `ANY_NON_ORIGINAL_HIGH = true` | `false` |
| VI-R03 | `CONTENTS_CLAIM = true` AND `CONTENTS_AREA_CLEAR = false` AND ∀ images: `is_cropped_or_obstructed = true` | `false` |
| VI-R04 | Default | `true` |

## 2.2 Difference from `evidence_standard_met`

| Dimension | `evidence_standard_met` | `valid_image` |
|-----------|-------------------------|---------------|
| Question answered | Can the **claimed condition** be evaluated from images? | Is the image set **trusted/processable** for automated review? |
| Identity conflict (`user_002`) | `false` | `true` |
| Blurry + clear pair (`user_003`) | `true` | `true` |
| Non-original screenshot (`user_008`) | `true` (mismatch evaluable) | `false` |
| Contents not shown (`user_032`) | `false` | `false` |
| Wrong angle, part not in frame (`user_006`) | `false` | `true` |

**Sample justification:** 18/20 rows have `valid_image = true`. The 2 false rows (`user_008`, `user_032`) share untrustworthy or wholly unreviewable evidence, not merely insufficient framing.

---

# 3. Claim Status Matrix

**Outputs:** `claim_status`, `issue_type`, `object_part` (visible ontology)

**Precondition:** Compute `evidence_standard_met` first (§1).

## 3.1 `claim_status` decision table

| Rule ID | Condition | `claim_status` |
|---------|-----------|----------------|
| CS-R01 | `evidence_standard_met = false` | `not_enough_information` |
| CS-R02 | `WRONG_OBJECT_SET = true` AND ∃ image with `visible_damage_extent` ≥ low at confidence ≥ medium | `contradicted` |
| CS-R03 | `PART_CLEAR = true` AND `primary_object_part` visible AND `visible_issue_type = none` at confidence ≥ medium on `BEST_PART_IMAGE_SET` | `contradicted` |
| CS-R04 | `PART_CLEAR = true` AND `visible_part` ≠ `primary_object_part` at confidence ≥ medium on best image | `contradicted` |
| CS-R05 | `PART_CLEAR = true` AND issue family mismatch at confidence ≥ medium (claimed crack, visible stain only, etc.) | `contradicted` |
| CS-R06 | `PART_CLEAR = true` AND `visible_damage_extent` = low AND claimed severity language ∈ {high, exaggerated} | `contradicted` |
| CS-R07 | `PART_CLEAR = true` AND `visible_issue_type` matches claimed issue family AND `visible_part` = `primary_object_part` at confidence ≥ medium AND NOT CS-R03..CS-R06 | `supported` |
| CS-R08 | `evidence_standard_met = true` AND none of CS-R02..CS-R07 match | `not_enough_information` |

**Issue family match:** Use mapping table §0.4 — `visible_issue_type` must belong to same family as `primary_issue_family`.

**Claimed severity language** is an observation from claim parser only; used **only** in CS-R06; never used for `severity` output field.

## 3.2 `issue_type` and `object_part` assignment (same pass as status)

| `claim_status` | `object_part` | `issue_type` |
|----------------|---------------|--------------|
| `not_enough_information` | If `primary_object_part` in frame with confidence ≥ medium: `primary_object_part`; else if any part confident: `visible_part` on best image; else `unknown` | If damage assessment impossible: `unknown`. If part visible, damage not: `unknown` (`user_006`). |
| `contradicted` | `visible_part` on image selected for contradiction at highest confidence; if `WRONG_OBJECT_SET`: `unknown` (`user_033`) | Visible issue on that image; if no damage: `none` (`user_020`, `user_034`); if wrong object: `unknown` |
| `supported` | `primary_object_part` | `visible_issue_type` on supporting image at confidence ≥ medium |

## 3.3 Contradiction subtype reference (sample)

| Sample | Rule | Mechanism |
|--------|------|-----------|
| `user_005` | CS-R06 | Severity exaggeration — scratch visible, "pretty bad" claimed |
| `user_008` | CS-R04 | Part mismatch — hood claimed, bumper damage visible |
| `user_020` | CS-R03 | Absent damage — trackpad visible, no damage |
| `user_033` | CS-R02 | Wrong object |
| `user_034` | CS-R03 | Seal visible, not torn |

## 3.4 Confidence gates within status matrix

| Observation confidence | Effect |
|------------------------|--------|
| `high` | Eligible for CS-R02..CS-R07 match |
| `medium` | Eligible for CS-R02..CS-R07 match |
| `low` | Do not assert match or contradiction on that signal → prefer CS-R08 or CS-R01 |

---

# 4. Severity Matrix

**Output:** `severity` — **visible evidence only**; ignore claim wording except CS-R06 already consumed.

| Rule ID | Condition | `severity` |
|---------|-----------|------------|
| SV-R01 | `claim_status = not_enough_information` | `unknown` |
| SV-R02 | `issue_type = none` | `none` |
| SV-R03 | `visible_damage_extent = high` on supporting image | `high` |
| SV-R04 | `visible_damage_extent = low` on supporting image | `low` |
| SV-R05 | `visible_damage_extent = medium` on supporting image | `medium` |
| SV-R06 | `visible_damage_extent = none` | `none` |
| SV-R07 | `visible_damage_extent = unknown` AND `claim_status = supported` | `medium` |
| SV-R08 | `visible_damage_extent = unknown` AND `claim_status = contradicted` AND `issue_type ≠ none` | `low` |

## 4.1 Mapping observation `visible_damage_extent` (from vision model)

| Visual signal | `visible_damage_extent` |
|---------------|-------------------------|
| No mark, intact surface | `none` |
| Hairline scratch, small scuff, minor corner deformation | `low` |
| Standard crack, dent, stain, crush, tear covering local area | `medium` |
| Structural break, shattered glass, detached part, large deformation | `high` |
| Cannot assess | `unknown` |

**Sample mapping:** `user_012`→low, most supported→medium, `user_008`→high, `user_005`/`user_033`→low, `user_020`/`user_034`→none, NEI→unknown.

---

# 5. Supporting Image Selection Matrix

**Output:** `supporting_image_ids` — semicolon-separated IDs, or `none`

## 5.1 Decision table

| Rule ID | `claim_status` | Condition | `supporting_image_ids` |
|---------|----------------|-----------|------------------------|
| SI-R01 | `not_enough_information` | `IDENTITY_CONFLICT = true` | All `image_id` in row (document conflict) |
| SI-R02 | `not_enough_information` | Otherwise | `none` |
| SI-R03 | `supported` | Single-image row | That `image_id` if `PART_CLEAR` on it |
| SI-R04 | `supported` | Multi-image | Minimal subset of `BEST_PART_IMAGE_SET` where claimed issue visible at confidence ≥ medium; if one suffices, list one only (`user_003`→`img_2`, `user_010`→`img_1`) |
| SI-R05 | `contradicted` | Part mismatch or absent damage | `image_id` of image proving contradiction (`user_008`→`img_1`) |
| SI-R06 | `contradicted` | Wrong object | `image_id` showing wrong object (`user_033`→`img_1`) |
| SI-R07 | `contradicted` | Seal/intact contradiction on multiple angles | All images where claimed part visible (`user_034`→`img_1;img_2`) |

## 5.2 Exclusion rules (apply before finalizing)

| Exclusion | Action |
|-----------|--------|
| `is_blurry = true` AND another image satisfies same rule | Exclude blurry image |
| `claimed_primary_part_visible = false` | Exclude |
| `depicts_claim_object = false` at confidence ≥ medium | Exclude unless SI-R01 identity conflict case |

---

# 6. Risk Flag Matrix

**Output:** `risk_flags` — semicolon-separated allowed flags, or `none`  
Evaluate **all** rows below; collect every flag whose conditions hold. Sort alphabetically. Deduplicate.

### 6.1 Image-quality flags (per image; flag at row level if ANY image triggers)

| Flag | Trigger condition | Min confidence | Sample |
|------|-------------------|----------------|--------|
| `blurry_image` | ∃ image: `is_blurry = true` | medium | `user_003` |
| `cropped_or_obstructed` | ∃ image: `is_cropped_or_obstructed = true` | medium | `user_032` |
| `low_light_or_glare` | ∃ image: `is_low_light_or_glare = true` | medium | — |
| `wrong_angle` | ∃ image: `is_wrong_angle_for_claimed_part = true` AND `claimed_primary_part_visible = false` | medium | `user_006` |

### 6.2 Evidence mismatch flags

| Flag | Trigger condition | Min confidence | Sample |
|------|-------------------|----------------|--------|
| `wrong_object` | `WRONG_OBJECT_SET = true` OR `IDENTITY_CONFLICT = true` | medium | `user_002`, `user_033` |
| `wrong_object_part` | `PART_CLEAR` AND `visible_part` ≠ `primary_object_part` | medium | `user_008` (use instead of or with `claim_mismatch`) |
| `damage_not_visible` | (`NO_PART_VISIBLE` OR (`PART_CLEAR` AND `visible_issue_type = none`)) AND `claimed_damage_absent = true` | medium | `user_006`, `user_020`, `user_034` |
| `claim_mismatch` | `claim_status = contradicted` AND (CS-R04 OR CS-R05 OR CS-R06) | medium | `user_005`, `user_008`, `user_033` |

**Precedence:** If `wrong_object` triggered, also evaluate `claim_mismatch` for contradictions.

### 6.3 Authenticity flags

| Flag | Trigger condition | Min confidence | Sample |
|------|-------------------|----------------|--------|
| `non_original_image` | ∃ image: `is_non_original_image = true` | high | `user_008` |
| `possible_manipulation` | ∃ image: `is_possibly_manipulated = true` | high | — |
| `text_instruction_present` | ∃ image: `has_instruction_text = true` | medium | `user_034` |

### 6.4 History flags (from `user_history.history_flags` only)

| Flag | Trigger condition | Sample |
|------|-------------------|--------|
| `user_history_risk` | `history_flags` contains `user_history_risk` | `user_005`, `user_008`, `user_020`, `user_031`, `user_033`, `user_034` |
| `manual_review_required` | See §6.5 | multiple |

### 6.5 `manual_review_required` composite rule

Set `manual_review_required` if **any**:

| Sub-rule | Condition |
|----------|-----------|
| MRR-1 | `history_flags` contains `manual_review_required` |
| MRR-2 | `history_flags` contains `user_history_risk` |
| MRR-3 | `IDENTITY_CONFLICT = true` |
| MRR-4 | `claim_mismatch` flag set |
| MRR-5 | `non_original_image` flag set |
| MRR-6 | `claim_status = not_enough_information` AND `CONTENTS_CLAIM = true` |

**Sample:** `user_002` MRR-3 (history none); `user_032` MRR-1; `user_031` MRR-2 on supported claim.

### 6.6 `none`

If zero flags collected after evaluation, output `none`.

---

# 7. Multi-Part Claim Resolution Policy

**Problem:** Output allows one `issue_type` and one `object_part`. Test rows allege multiple parts (e.g. bumper + headlight).

## 7.1 Detection

`MULTI_PART_CLAIM = true` when claim observation extracts ≥ 2 distinct `object_part` values with explicit customer affirmation.

## 7.2 Resolution algorithm (deterministic)

Execute in order:

| Step | Action |
|------|--------|
| MP-1 | Collect all parts **explicitly affirmed** by customer after agent clarification (ignore agent suggestions not confirmed). |
| MP-2 | If count = 1, set `primary_object_part` to that part; stop. |
| MP-3 | Compute `visibility_score(part)` = max over images of part-confidence score (high=3, medium=2, low=1, absent=0). |
| MP-4 | Select `primary_object_part` = argmax `visibility_score`; tie-break by **last** part mentioned in final customer message. |
| MP-5 | Remaining parts → `secondary_parts` (not used for primary verdict fields). |

## 7.3 Effect on other matrices

| Matrix | Behavior |
|--------|----------|
| Evidence sufficiency (§1) | Evaluate **primary part only**. Secondary part failure does not force `evidence_standard_met = false`. |
| Claim status (§3) | Compare observations to **primary part** only. |
| Multi-part with both visible | Status reflects primary part only; if primary supported but secondary not visible, still `supported` on primary. |
| Multi-part both contradicted | If primary contradicted, `contradicted`; do not upgrade to NEI because secondary unverifiable. |

## 7.4 Justification

- Schema constraint requires single part output.
- Sample rows are all single-part; policy optimized for test set patterns (`case_001`, `case_010`, `case_019`).
- Visibility-first tie-break avoids NEI when one part has clear evidence.
- Last-mention tie-break resolves symmetric claims without model judgment.

---

# 8. Confidence Threshold Policy

## 8.1 Levels

| Level | Numeric range (if model supplies probability) | Operational meaning |
|-------|-----------------------------------------------|---------------------|
| `high` | p ≥ 0.85 | May drive supported/contradicted |
| `medium` | 0.60 ≤ p < 0.85 | May drive supported/contradicted |
| `low` | p < 0.60 | May not assert positive damage/part match |

## 8.2 Mandatory outputs by confidence

| Situation | Required output |
|-----------|-----------------|
| `visible_issue_type` confidence low | `issue_type = unknown` |
| `visible_part` confidence low AND `claim_status` ≠ `not_enough_information` | `object_part = unknown` unless `primary_object_part` visible at medium+ |
| `BEST_PART_CONFIDENCE = low` | `evidence_standard_met = false` (ESM-R05) |
| `BEST_PART_CONFIDENCE = medium` AND damage confidence low | `claim_status = not_enough_information` (CS-R08) |
| Any authenticity flag at low confidence only | Do not set `non_original_image` / `possible_manipulation` |

## 8.3 `unknown` vs `not_enough_information` vs `manual_review_required`

| Output field | When |
|--------------|------|
| `issue_type = unknown` | Part or damage not classifiable at medium+ confidence |
| `object_part = unknown` | Part not localizable at medium+ confidence |
| `severity = unknown` | `claim_status = not_enough_information` (SV-R01) |
| `claim_status = not_enough_information` | `evidence_standard_met = false` OR CS-R08 |
| `manual_review_required` | §6.5 — never changes `claim_status` by itself |

---

# 9. Hidden Rule Validation

Re-evaluation of rules inferred from `sample_claims.csv` (n=20).

| Rule ID | Statement | Supporting evidence | Contradictory evidence | Label |
|---------|-----------|---------------------|------------------------|-------|
| HR-01 | `evidence_standard_met = false` ⟹ `claim_status = not_enough_information` | `user_002`, `user_006`, `user_032` (3/3) | None in sample | **High Confidence Rule** |
| HR-02 | `claim_status = contradicted` ⟹ `evidence_standard_met = true` | 5/5 contradicted rows | None | **High Confidence Rule** |
| HR-03 | `claim_status = not_enough_information` ⟹ `severity = unknown` | 3/3 NEI rows | None | **High Confidence Rule** |
| HR-04 | `history_flags` has `user_history_risk` ⟹ output contains `user_history_risk` | 6/6 users | None | **High Confidence Rule** |
| HR-05 | `user_history_risk` never alone changes `claim_status` | `user_031` supported with UHR | None | **High Confidence Rule** |
| HR-06 | `valid_image` independent of `evidence_standard_met` | `user_008` (true/false), `user_006` (true/false) | None | **High Confidence Rule** |
| HR-07 | Severity reflects visible damage not claim text | `user_005` low not "bad" | None | **High Confidence Rule** |
| HR-08 | `issue_type`/`object_part` on contradiction reflect visible not claimed | `user_008` bumper not hood | None | **High Confidence Rule** |
| HR-09 | NEI → `supporting_image_ids = none` except identity conflict | `user_006`, `user_032` none; `user_002` exception | `user_002` lists both images | **Medium Confidence Rule** |
| HR-10 | `manual_review_required` iff history contains it | — | `user_002` (none→MRR), `user_020` (UHR only→MRR) | **Medium Confidence Rule** — use §6.5 instead |
| HR-11 | `claim_mismatch` iff contradicted | `user_020`, `user_034` contradicted without CM | Uses `damage_not_visible` | **Medium Confidence Rule** |
| HR-12 | Supported default severity `medium` | 11/12 supported | `user_012` low | **Medium Confidence Rule** |
| HR-13 | `glass_shatter` never used; crack used for shattered language | `user_018` | No shatter example | **Weak Hypothesis** |
| HR-14 | `broken_part` preferred over `scratch` when damage severe | `user_002` scratch claimed → `broken_part` | Single case | **Weak Hypothesis** |
| HR-15 | `identity_constraint_active` always from explicit color/side | — | Not tested in sample | **Weak Hypothesis** |

---

## Execution Order (normative)

Matrices MUST be evaluated in this order:

```text
1. Multi-part resolution (§7) → primary_object_part
2. Evidence sufficiency (§1)
3. Valid image (§2)
4. Claim status + issue_type + object_part (§3)
5. Severity (§4)
6. Supporting image IDs (§5)
7. Risk flags (§6)
8. Reason templates (§1.3) + justification templates (downstream doc)
```

`claim_status` MUST NOT be computed before `evidence_standard_met`.  
`risk_flags` MUST NOT influence `claim_status`.  
`severity` MUST be computed after `claim_status` and `issue_type`.

---

## Appendix A: Sample Row Trace (abbreviated)

| user_id | ESM rule | valid rule | CS rule | severity | supporting |
|---------|----------|------------|---------|----------|------------|
| user_001 | R08 | R04 | R07 | SV-R05 | SI-R03 |
| user_002 | R02 | R04 | R01 | SV-R01 | SI-R01 |
| user_005 | R08 | R04 | R06 | SV-R04 | SI-R05 |
| user_006 | R03 | R04 | R01 | SV-R01 | SI-R02 |
| user_008 | R08 | R02 | R04 | SV-R03 | SI-R05 |
| user_020 | R08 | R04 | R03 | SV-R02 | SI-R05 |
| user_032 | R04 | R03 | R01 | SV-R01 | SI-R02 |
| user_033 | R08 | R04 | R02 | SV-R04 | SI-R06 |
| user_034 | R08 | R04 | R03 | SV-R02 | SI-R07 |

---

## Appendix B: Reason and justification (template keys only)

Justifications MUST cite image IDs when `supporting_image_ids ≠ none`. History MAY appear only when `user_history_risk` ∈ `risk_flags`. Full prose templates are derived from rule IDs; no generative model required.
