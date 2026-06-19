# Hidden Business Rules

**Status:** Empirical rules derived from labeled data and normative decision logic  
**Sources:** `dataset/sample_claims.csv` (n=20), [decision_matrix.md](../decision_matrix.md) §9, [architecture_review.md](../architecture_review.md)  
**Rule:** No speculation. Every rule cites explicit sample evidence or a normative matrix entry.

---

## Confidence Labels

| Label | Meaning |
|-------|---------|
| **High Confidence** | 100% consistency on sample (n≥3 where applicable) or encoded as hard invariant in decision_matrix |
| **Medium Confidence** | Majority consistency with documented exceptions |
| **Weak Hypothesis** | Single-case or untested pattern — requires synthetic validation before production reliance |

---

## High Confidence Rules

### HR-01 — ESM false implies NEI

| Field | Value |
|-------|-------|
| **Rule ID** | HR-01 |
| **Description** | If `evidence_standard_met = false`, then `claim_status` MUST be `not_enough_information`. |
| **Evidence** | `user_002` (ESM=false, NEI), `user_006` (ESM=false, NEI), `user_032` (ESM=false, NEI) — **3/3** rows with ESM=false are NEI. Zero counterexamples in sample. |
| **Confidence** | High Confidence |
| **Affected Outputs** | `claim_status`, `issue_type`, `object_part`, `severity`, `supporting_image_ids` |
| **Matrix encoding** | CS-R01 in decision_matrix §3.1 |
| **Invariant** | `¬evidence_standard_met ⟹ claim_status = not_enough_information` |

---

### HR-02 — Contradicted implies ESM true

| Field | Value |
|-------|-------|
| **Rule ID** | HR-02 |
| **Description** | If `claim_status = contradicted`, then `evidence_standard_met` MUST be `true`. A contradiction requires sufficient evidence to evaluate the mismatch. |
| **Evidence** | All 5 contradicted rows: `user_005`, `user_008`, `user_020`, `user_033`, `user_034` have `evidence_standard_met=true`. **5/5**. |
| **Confidence** | High Confidence |
| **Affected Outputs** | `evidence_standard_met`, `claim_status` |
| **Matrix encoding** | Implicit precondition of CS-R02..CS-R06 (only evaluated when ESM=true per CS-R01 gate) |
| **Invariant** | `claim_status = contradicted ⟹ evidence_standard_met = true` |

---

### HR-03 — NEI implies severity unknown

| Field | Value |
|-------|-------|
| **Rule ID** | HR-03 |
| **Description** | If `claim_status = not_enough_information`, then `severity` MUST be `unknown`. |
| **Evidence** | `user_002` (NEI, unknown), `user_006` (NEI, unknown), `user_032` (NEI, unknown) — **3/3** NEI rows. |
| **Confidence** | High Confidence |
| **Affected Outputs** | `severity` |
| **Matrix encoding** | SV-R01 in decision_matrix §4 |
| **Invariant** | `claim_status = not_enough_information ⟹ severity = unknown` |

---

### HR-04 — History flag propagates to risk_flags

| Field | Value |
|-------|-------|
| **Rule ID** | HR-04 |
| **Description** | If `user_history.history_flags` contains `user_history_risk`, then output `risk_flags` MUST contain `user_history_risk`. |
| **Evidence** | Six sample users with UHR in history appear in sample labels with UHR in output: `user_005`, `user_008`, `user_020`, `user_031`, `user_033`, `user_034`. Cross-checked against `user_history.csv` — all six have `user_history_risk` in `history_flags`. **6/6**. |
| **Confidence** | High Confidence |
| **Affected Outputs** | `risk_flags` |
| **Matrix encoding** | decision_matrix §6.4 history flags |
| **Invariant** | `history_flags ∋ user_history_risk ⟹ risk_flags ∋ user_history_risk` |

---

### HR-05 — History never alone changes claim_status

| Field | Value |
|-------|-------|
| **Rule ID** | HR-05 |
| **Description** | `user_history_risk` MUST NOT by itself change `claim_status`. History supplements risk flags and justification prose only. |
| **Evidence** | `user_031` has `user_history_risk` in `risk_flags` and `history_flags`, yet `claim_status=supported`. `user_005` is contradicted due to visible evidence (minor scratch vs "pretty bad"), not history alone. Constitution: architect_prompt.md — "Never allow user history to override visible evidence." |
| **Confidence** | High Confidence |
| **Affected Outputs** | `claim_status`, `claim_status_justification` |
| **Matrix encoding** | M9 runs after M7a; risk module MUST NOT mutate verdict (architecture_v2 §5.2) |
| **Invariant** | `risk_flags` and history MUST NOT feed into ClaimDecisionEngine |

---

### HR-06 — valid_image independent of evidence_standard_met

| Field | Value |
|-------|-------|
| **Rule ID** | HR-06 |
| **Description** | `valid_image` and `evidence_standard_met` are orthogonal dimensions. One can be true while the other is false. |
| **Evidence** | `user_008`: ESM=true, valid_image=false (non-original screenshot but mismatch evaluable). `user_006`: ESM=false, valid_image=true (images processable but headlight not visible). `user_032`: both false. `user_002`: ESM=false, valid_image=true. |
| **Confidence** | High Confidence |
| **Affected Outputs** | `valid_image`, `evidence_standard_met` |
| **Matrix encoding** | Separate matrices §1 (ESM) and §2 (valid_image); architecture_review VI-1 |
| **Invariant** | No cross-field implication between ESM and valid_image |

---

### HR-07 — Severity from visible evidence, not claim text

| Field | Value |
|-------|-------|
| **Rule ID** | HR-07 |
| **Description** | `severity` reflects `visible_damage_extent` on images, not customer severity language in chat. |
| **Evidence** | `user_005`: customer says "pretty bad"; output `severity=low` because visible issue is minor scratch. Claim text would imply high; label is low. |
| **Confidence** | High Confidence |
| **Affected Outputs** | `severity` |
| **Matrix encoding** | SV-R01..SV-R08; `claimed_severity_language` used only in CS-R06 for contradiction, never in SeverityEngine |
| **Invariant** | SeverityEngine MUST NOT read `ClaimObservation.claimed_severity_language` |

---

### HR-08 — Contradiction ontology reflects visible, not claimed

| Field | Value |
|-------|-------|
| **Rule ID** | HR-08 |
| **Description** | On `contradicted`, `issue_type` and `object_part` describe what is **visible** in evidence, not what the customer claimed. |
| **Evidence** | `user_008`: customer claims hood scratch; output `object_part=front_bumper`, `issue_type=broken_part` (visible severe front damage). `user_005`: claimed severe bumper damage; output `issue_type=scratch` (visible minor scratch). |
| **Confidence** | High Confidence |
| **Affected Outputs** | `issue_type`, `object_part`, `claim_status` |
| **Matrix encoding** | decision_matrix §3.2 contradicted row |
| **Invariant** | VerdictDecision visible ontology from best contradiction image |

---

## Medium Confidence Rules

### HR-09 — NEI supporting images mostly none

| Field | Value |
|-------|-------|
| **Rule ID** | HR-09 |
| **Description** | When `claim_status = not_enough_information`, `supporting_image_ids` is usually `none`, except when documenting identity conflict. |
| **Evidence** | `user_006` → `none`, `user_032` → `none`. Exception: `user_002` (NEI, identity conflict) → `img_1;img_2` per SI-R01. **2/3** follow `none`; 1/3 exception documented in matrix. |
| **Confidence** | Medium Confidence |
| **Affected Outputs** | `supporting_image_ids` |
| **Matrix encoding** | SI-R01 (identity conflict exception), SI-R02 (default NEI) |

---

### HR-10 — manual_review_required composite, not history-only

| Field | Value |
|-------|-------|
| **Rule ID** | HR-10 |
| **Description** | `manual_review_required` is set by composite rule MRR-1..MRR-6, not solely by `history_flags` containing `manual_review_required`. |
| **Evidence** | `user_002`: `history_flags=none` but output includes `manual_review_required` (MRR-3 identity conflict). `user_020`: only `user_history_risk` in history but `manual_review_required` present (MRR-2). `user_032`: history has `manual_review_required` (MRR-1). |
| **Confidence** | Medium Confidence |
| **Affected Outputs** | `risk_flags` |
| **Matrix encoding** | decision_matrix §6.5 |

---

### HR-11 — claim_mismatch not equivalent to contradicted

| Field | Value |
|-------|-------|
| **Rule ID** | HR-11 |
| **Description** | `claim_mismatch` flag is NOT present on every contradicted row. Some contradictions use `damage_not_visible` instead. |
| **Evidence** | Contradicted without `claim_mismatch`: `user_020` (`damage_not_visible`), `user_034` (`damage_not_visible`, `text_instruction_present`). Contradicted with `claim_mismatch`: `user_005`, `user_008`, `user_033`. |
| **Confidence** | Medium Confidence |
| **Affected Outputs** | `risk_flags` |
| **Matrix encoding** | §6.2 — `claim_mismatch` requires CS-R04 OR CS-R05 OR CS-R06; CS-R03 uses `damage_not_visible` |

---

### HR-12 — Supported default severity medium

| Field | Value |
|-------|-------|
| **Rule ID** | HR-12 |
| **Description** | Most supported claims receive `severity=medium` when visible damage is present at standard extent. |
| **Evidence** | 11 of 12 supported rows have `severity=medium`. Exception: `user_012` → `low` (minor corner dent). |
| **Confidence** | Medium Confidence |
| **Affected Outputs** | `severity` |
| **Matrix encoding** | SV-R05 default path for `visible_damage_extent=medium` |

---

## Weak Hypotheses (Not Rules — Require Validation)

### HR-13 — glass_shatter unused; crack preferred

| Field | Value |
|-------|-------|
| **Rule ID** | HR-13 |
| **Description** | Shattered-screen language maps to `issue_type=crack`, not `glass_shatter`. |
| **Evidence** | `user_018`: customer says "shattered"; label `issue_type=crack`. No sample row uses `glass_shatter`. |
| **Confidence** | Weak Hypothesis |
| **Affected Outputs** | `issue_type` |
| **Validation** | Synthetic + test set rows with shatter language |

---

### HR-14 — broken_part over scratch when damage severe

| Field | Value |
|-------|-------|
| **Rule ID** | HR-14 |
| **Description** | When claimed scratch but visible damage is severe, output may use `broken_part`. |
| **Evidence** | `user_002`: customer claims "scratch"; NEI row has `issue_type=broken_part` in output (identity conflict case). Single ambiguous case. |
| **Confidence** | Weak Hypothesis |
| **Affected Outputs** | `issue_type` |

---

### HR-15 — identity_constraint from explicit color/side only

| Field | Value |
|-------|-------|
| **Rule ID** | HR-15 |
| **Description** | `identity_constraint_active` triggers only when customer explicitly claims color, side, or "my blue car". |
| **Evidence** | No sample row has `identity_constraint_active=true` in labels. `user_002` identity conflict is cross-image, not single-claim color constraint. **Not tested in sample.** |
| **Confidence** | Weak Hypothesis |
| **Affected Outputs** | `ClaimObservation`, ESM-R07, REQ_CAR_IDENTITY_OR_SIDE |

---

## Normative Rules (from decision_matrix, not empirically disputed)

These are encoded in decision_matrix.md and confirmed by sample traces in Appendix A:

| Rule ID | Statement | Sample trace |
|---------|-----------|--------------|
| ESM-R02 | Identity conflict → ESM false | `user_002` |
| ESM-R03 | No part visible → ESM false | `user_006` |
| ESM-R04 | Contents not shown → ESM false | `user_032` |
| ESM-R08 | Default sufficient | `user_003` (blurry + clear compensates) |
| CS-R06 | Severity exaggeration → contradicted | `user_005` |
| CS-R03 | Visible part, no damage → contradicted | `user_020`, `user_034` |
| CS-R04 | Part mismatch → contradicted | `user_008` |
| CS-R02 | Wrong object → contradicted | `user_033` |
| VI-R02 | Non-original high confidence → valid_image false | `user_008` |
| VI-R03 | Contents obstructed → valid_image false | `user_032` |

---

## Rule Coverage Matrix

| Output field | Governing hidden rules |
|--------------|------------------------|
| `evidence_standard_met` | HR-01, HR-02, HR-06, ESM-R* |
| `valid_image` | HR-06, VI-R* |
| `claim_status` | HR-01, HR-02, HR-05, CS-R* |
| `severity` | HR-03, HR-07, HR-12, SV-R* |
| `issue_type`, `object_part` | HR-08, HR-13, HR-14 |
| `supporting_image_ids` | HR-09, SI-R* |
| `risk_flags` | HR-04, HR-10, HR-11, RF-* |

---

## Cross-Reference

| Document | Role |
|----------|------|
| [decision_matrix.md](../decision_matrix.md) | Normative implementation |
| [failure_taxonomy.md](failure_taxonomy.md) | Failure classes when rules violated |
| [hypotheses.md](hypotheses.md) | Experiments to promote weak hypotheses |
