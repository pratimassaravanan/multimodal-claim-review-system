# Architecture Review

**Reviewers:** Principal AI Architect, Principal Data Scientist, Technical Judge  
**Date:** 2026-06-19  
**Sources:** [problem_decomposition.md](problem_decomposition.md), [architect_prompt.md](architect_prompt.md), [sample_claims.csv](../dataset/sample_claims.csv), [evidence_requirements.csv](../dataset/evidence_requirements.csv)

**Note:** [architecture.md](architecture.md) is still a stub (“To be designed”). `hidden_business_rules.md` does not exist in the repo; hidden rules referenced below were reverse-engineered from the 20 labeled sample rows and are cited by rule ID (e.g., **CS-1**, **ESM-1**, **RF-1**). Those rules should be persisted to `docs/hidden_business_rules.md` before implementation.

---

## 1. Proposed Architecture Under Review

The implicit proposal — derived from the constitution’s model usage policy and problem decomposition — is a **two-observation-engine, multi-rule-layer** pipeline:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ L0  Intake & Context Assembly                                           │
│     claims row + user_history + evidence_requirements + image files     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              ▼                                           ▼
┌──────────────────────────────┐           ┌──────────────────────────────┐
│ L1  Claim Observation        │           │ L2  Visual Observation       │
│     Gemini 2.5 Flash         │           │     Gemini 2.5 Pro / image   │
│     (multilingual extract)   │           │     (per-image structured)   │
└──────────────────────────────┘           └──────────────────────────────┘
              │                                           │
              └─────────────────────┬─────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L3  Ontology Normalization Gate                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L4  Adversarial Sanitizer                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L5  Multi-Image Consistency Engine                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L6  Requirement Mapper + Evidence Sufficiency Engine                    │
│     → evidence_standard_met, evidence_standard_met_reason               │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L7  Image Trust Engine → valid_image                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L8  Verdict Engine → claim_status, issue_type, object_part              │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L9  Risk Flag Aggregator → risk_flags                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L10 Severity Engine → severity                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L11 Supporting Image Selector → supporting_image_ids                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L12 Explanation Composer → reasons & justifications                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ L13 Output Assembler → output.csv row                                   │
└─────────────────────────────────────────────────────────────────────────┘

        ┌──────────────────────────────────────────┐
        │ L14 Evaluation Harness (offline)         │
        │     sample_claims metrics + A/B compare  │
        └──────────────────────────────────────────┘
```

This review challenges every layer. Layers marked **MERGE** or **DROP** below feed into the **Recommended Architecture** in Section 3.

---

## 2. Layer-by-Layer Review

### L0 — Intake & Context Assembly

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Bind one claim row to reference data (`user_history`, `evidence_requirements`) and resolvable image paths. |
| **Hidden rules satisfied** | Enables **RF-1** (history flag lookup), requirement mapping for **ESM-2**, image ID extraction for **SI-2**. |
| **If removed?** | No joins, no images, no requirements → system cannot run. |
| **Failure modes prevented** | Missing files, orphan `user_id`, wrong image roots. |
| **Evaluation metric** | Intake success rate (rows loaded / rows attempted); path resolution errors. |
| **Verdict** | **Required** |

---

### L1 — Claim Observation (Gemini 2.5 Flash)

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Conversation is unstructured, multilingual, noisy, and adversarial. Rules need a normalized **alleged claim**: part(s), issue family, severity language, exclusions, identity hints (color, side). |
| **Hidden rules satisfied** | Prerequisite for **CS-1** (claim vs visual alignment), **ESM-2** (which part to verify), **RF-6** (injection in chat must not reach verdict). |
| **If removed?** | Rules would need regex/heuristics on chat — fails on Hindi (`user_002`), Spanish (test `case_017`), long narratives (`user_006`, `user_018`), and prompt injection (`case_055`). |
| **Failure modes prevented** | Wrong part checked, missed exclusions (“not keyboard, only screen”), injection-driven approvals. |
| **Evaluation metric** | Claim extraction field accuracy vs sample (alleged part, issue family); per-language breakdown; injection-case pass rate. |
| **Verdict** | **Required** (constitution-mandated model role) |

**Challenge:** A single multimodal call per row would be simpler and cheaper. **Rejected** — constitution explicitly assigns Flash to claim understanding only; mixing verdict-adjacent reasoning into one call increases audit risk and violates “Models Observe. Rules Decide.”

---

### L2 — Visual Observation (Gemini 2.5 Pro, per image)

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Images are the primary source of truth. Each image must yield structured observations: object type, visible part, visible damage, quality flags, authenticity cues, in-image text. |
| **Hidden rules satisfied** | **SV-1** (visible severity), **CS-4** (part visible vs damage absent), **VI-3** (quality without invalidating set), **RF-3**/`RF-4` inputs, **SI-2** (per-image usefulness). |
| **If removed?** | No visual grounding → hallucinated verdicts; constitution violation. |
| **Failure modes prevented** | Invented damage, missed identity mismatch, undetected `non_original_image` (`user_008`). |
| **Evaluation metric** | Per-image observation accuracy on sample (part, issue_type, quality flags); flag precision/recall vs labeled `risk_flags`. |
| **Verdict** | **Required** (constitution-mandated) |

**Challenge:** Per-image calls vs one call with all images. **Per-image is required** for **ESM-2** / **REQ_GENERAL_MULTI_IMAGE** (“each submitted image should be considered separately”) and for **SI-2** (select best image, exclude blurry `img_1` in `user_003`).

---

### L3 — Ontology Normalization Gate

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Map model outputs to closed enums; remap unknown labels; enforce `claim_object`-specific `object_part` vocabularies. |
| **Hidden rules satisfied** | Hallucination prevention (constitution); prevents invented issue types/parts/flags. |
| **If removed?** | Invalid CSV values; judge rejection; fabricated labels. |
| **Failure modes prevented** | Ontology violations, cross-object part leaks (car part on laptop row). |
| **Evaluation metric** | Schema compliance rate (100% target); invalid-label rejection count. |
| **Verdict** | **Required** — but implement as a **function inside L1/L2 post-processing**, not a standalone microservice. |

---

### L4 — Adversarial Sanitizer

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Strip or neutralize prompt-injection in chat and ensure in-image instructions affect only `text_instruction_present`, not verdict (**RF-6**, constitution). |
| **Hidden rules satisfied** | **RF-6**; blocks text-based approval (`case_008`, `case_036`, `case_048`, `case_055`). |
| **If removed?** | Model observations may inherit “approve immediately” or in-image notes as facts. |
| **Failure modes prevented** | Instruction-driven false supports. |
| **Evaluation metric** | Adversarial subset accuracy (test injection rows); zero `supported` when only instruction text supports claim. |
| **Verdict** | **Required logic**, **optional as separate layer** — merge into L1/L2 prompts + L9 risk rules. A dedicated layer is only justified if sanitizer rules are complex and independently tested. |

---

### L5 — Multi-Image Consistency Engine

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Detect cross-image conflicts: different vehicles (`user_002`), incompatible contexts. Feeds **ESM-1** gate before verdict. |
| **Hidden rules satisfied** | **ESM-3** (identity failure → `evidence_standard_met=false`); **RF-2** (`manual_review_required` on identity failure without history). |
| **If removed?** | `user_002`-type fraud/confusion missed; may wrongly support or contradict on mismatched close-up/wide shot. |
| **Failure modes prevented** | Multi-image identity failure, false support from unrelated close-up. |
| **Evaluation metric** | Consistency detection recall on multi-image sample rows (`user_002`, `user_003`, `user_010`); false NEI rate on benign multi-image rows. |
| **Verdict** | **Required** (constitution names “Consistency Engine”) |

**Challenge:** Merge with L6? **Logical separation yes; physical separation optional.** Consistency outputs are inputs to evidence sufficiency. Implement as a named submodule with its own tests, not necessarily a separate deployable unit.

---

### L6 — Requirement Mapper + Evidence Sufficiency Engine

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Map alleged claim → `REQ_*` rows in `evidence_requirements.csv`; evaluate whether observations satisfy minimum visual evidence; emit `evidence_standard_met` + reason. |
| **Hidden rules satisfied** | **ESM-1** (sufficiency ≠ support); **ESM-2** (part not visible → false); **CS-1** gate (`false` → NEI in all 3 sample cases). |
| **If removed?** | Cannot distinguish NEI from contradiction; violates problem contract and sample labels. |
| **Failure modes prevented** | Supporting claims without visible part (`user_006`); approving missing-contents without opened box (`user_032`). |
| **Evaluation metric** | `evidence_standard_met` accuracy (sample: 20/20 target); joint accuracy with `claim_status` (NEI ⟺ false, **confidence high**). |
| **Verdict** | **Required** |

**Challenge:** The **Requirement Mapper** is currently implicit. **Add as explicit sub-layer** — mapping table from (claim_object, issue_family, identity_hints) → requirement IDs is ambiguous (problem decomposition §12.2) and must be versioned and tested independently.

---

### L7 — Image Trust Engine (`valid_image`)

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Separate “can we evaluate?” (**ESM**) from “should we trust this set for automation?” Sample: `user_008` has `evidence_standard_met=true`, `valid_image=false`, `contradicted`. |
| **Hidden rules satisfied** | **VI-1**, **VI-2** (`non_original_image`, unreviewable contents); distinct from blur/wrong-angle (**VI-3**). |
| **If removed?** | Conflate trust with sufficiency; wrong automation decisions on screenshots and unreviewable content. |
| **Failure modes prevented** | Auto-approving on `non_original_image`; treating fundamentally broken evidence as merely “insufficient.” |
| **Evaluation metric** | `valid_image` accuracy (2 negative cases in sample); cross-tab vs `evidence_standard_met` (expect 4 combinations, n small). |
| **Verdict** | **Required** — sample proves orthogonality. |

**Challenge:** Merge into L9 risk flags? **No.** `valid_image` is an output column; `non_original_image` is a flag. Trust engine consumes flags + observations; verdict engine may run when `valid_image=false` (`user_008`).

---

### L8 — Verdict Engine (`claim_status`, `issue_type`, `object_part`)

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Core business decision: supported / contradicted / not_enough_information; visible issue and part per **CS-1**, **CS-2**, **CS-4**. |
| **Hidden rules satisfied** | **CS-1** tree; **CS-2** subtypes (severity exaggeration, wrong part/object, absent damage); visible ontology on contradiction (`user_008` hood→`front_bumper`). |
| **If removed?** | No product — this is the claim. |
| **Failure modes prevented** | History-driven verdicts, claim-text approvals, NEI/contradiction confusion. |
| **Evaluation metric** | `claim_status` accuracy (primary); `issue_type` + `object_part` accuracy; contradiction subtype confusion matrix. |
| **Verdict** | **Required** |

**Challenge:** Should `issue_type`/`object_part` be a separate “Visible Evidence” layer? **Optional split for testing**, but same rule pass is acceptable if inputs are clearly “claimed” vs “observed.”

---

### L9 — Risk Flag Aggregator

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Combine per-image signals + claim-visual mismatch + history into semicolon-separated `risk_flags`; add `manual_review_required` per **RF-2**. |
| **Hidden rules satisfied** | **RF-1** (history `user_history_risk` propagation 6/6); **RF-2** (MRR triggers); **RF-3** vs **RF-4** (`claim_mismatch` vs `damage_not_visible`); history never alone changes status (**CS-3**, `user_031`). |
| **If removed?** | Lose audit trail; under-flag risky users and image-quality issues. |
| **Failure modes prevented** | Silent approval of risky history; missing manual review escalation. |
| **Evaluation metric** | Per-flag F1 on sample (sparse); exact set match on `risk_flags`; **RF-1** compliance rate (100% on sample). |
| **Verdict** | **Required** |

**Challenge:** Merge into L8? **Logically separate per constitution** (“Risk Assessment: Rules”). Verdict must be computable without history changing outcome; risk is orthogonal. Implement as second pass over same observations.

---

### L10 — Severity Engine

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Emit visible damage magnitude: `none` / `low` / `medium` / `high` / `unknown`. |
| **Hidden rules satisfied** | **SV-1** (visible not claimed); **SV-2** (`none` on absent damage); **SV-3** (`unknown` on NEI). |
| **If removed?** | Missing required output column; lose exaggeration signal (`user_005` low vs “pretty bad”). |
| **Failure modes prevented** | Severity from claim language alone; `medium` on NEI cases. |
| **Evaluation metric** | `severity` accuracy; NEI→`unknown` rule compliance (3/3 in sample). |
| **Verdict** | **Required** — but **merge implementation with L8** as one deterministic decision matrix with a severity column. Separate “engine” is documentation-only unless independently complex. |

---

### L11 — Supporting Image Selector

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Identify which image IDs substantiate the **decision** (not the user’s story). |
| **Hidden rules satisfied** | **SI-1** (NEI usually `none`, except `user_002` documents conflict); **SI-2** (best image only); **SI-4** (contradiction-supporting images included). |
| **If removed?** | `supporting_image_ids` wrong or always all images; breaks explainability. |
| **Failure modes prevented** | Citing blurry/irrelevant images; omitting images that prove contradiction. |
| **Evaluation metric** | Exact set match on `supporting_image_ids`; subset F1 if partial credit. |
| **Verdict** | **Required logic**; **optional as separate layer** — can be last step of L8/L10 matrix. |

---

### L12 — Explanation Composer

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Produce `evidence_standard_met_reason` and `claim_status_justification` grounded in images; English prose; optional history mention when flagged. |
| **Hidden rules satisfied** | ESM reason cites visibility/identity gap; justification cites image IDs; history only when **RF-1** flags present. |
| **If removed?** | Empty or generic reasons → judge failure, poor auditability. |
| **Failure modes prevented** | History-only justifications; non-English output; justification contradicting verdict. |
| **Evaluation metric** | Template coverage (all branches produce text); optional LLM-judge grounding score on sample; must not use generative model for **decisions**. |
| **Verdict** | **Required** |

**Challenge:** LLM-generated prose? **Unnecessary and risky.** Sample labels follow templated patterns (“The image clearly shows…”, “The submitted images do not reliably support…”). **Recommend deterministic templates** filled from decision trace. Optional: Flash for fluency **only** if templates fail judge review — default to templates.

---

### L13 — Output Assembler

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Enforce 14-column order, passthrough fields, `none` sentinels, semicolon separators. |
| **Hidden rules satisfied** | Contract compliance (AGENTS.md §6). |
| **If removed?** | Unevaluable submission. |
| **Failure modes prevented** | Column drift, wrong enum formatting. |
| **Evaluation metric** | Schema validation pass rate (100%). |
| **Verdict** | **Required** (trivial) |

---

### L14 — Evaluation Harness

| Question | Answer |
|----------|--------|
| **Why does it exist?** | Constitution: “Evaluation Drives Improvement”; README requires metrics, A/B strategies, operational report. |
| **Hidden rules satisfied** | Enables validation of every layer; prevents shipping untested rule changes. |
| **If removed?** | Submission incomplete; no way to justify architecture choices to judge. |
| **Failure modes prevented** | Overfitting to anecdotes; prompt churn without measurement. |
| **Evaluation metric** | Meta — harness itself must run CI-style on `sample_claims.csv`; compare ≥2 strategies. |
| **Verdict** | **Required** (deliverable, not inference hot path) |

---

## 3. Missing Layers (Add These)

### M1 — Primary Claim Resolver (MULTI-PART)

| Question | Answer |
|----------|--------|
| **Why add?** | Test set has rows alleging two parts/issues in one claim (`case_001` bumper+headlight, `case_019` hinge+screen, `case_040` torn+missing). Output allows one `issue_type` + one `object_part`. **No layer in current proposal handles this.** |
| **Hidden rules** | Not observable in sample (single-part rows). Inferred from test `claims.csv`. |
| **If omitted?** | Systematic errors on multi-part test rows. |
| **Failure modes prevented** | Random part choice; double-counting requirements. |
| **Evaluation metric** | Accuracy on synthetic multi-part fixtures; ablation on test rows once labeled. |
| **Verdict** | **Required** (add before L6) |

**Proposed rule (to validate):** Resolve to the **last explicit customer affirmation** in chat, or the part with strongest visual evidence, or NEI if parts conflict — must be decided and versioned.

---

### M2 — Confidence Gate

| Question | Answer |
|----------|--------|
| **Why add?** | Constitution: low confidence → `unknown`, `manual_review_required`, or `not_enough_information`. Observations from L1/L2 need explicit confidence thresholds. |
| **Hidden rules** | **CS-4** boundary (visible part, no damage → contradict not NEI); false certainty failure mode. |
| **If omitted?** | Model hedging ignored; specific labels where `unknown` is correct (`user_006`). |
| **Failure modes prevented** | Over-specific `issue_type` when image ambiguous. |
| **Evaluation metric** | `unknown`/`NEI` recall on low-visibility cases; calibration curve on observation confidence. |
| **Verdict** | **Required** — merge into L3 gate and L6/L8 thresholds. |

---

### M3 — Decision Trace / Audit Record

| Question | Answer |
|----------|--------|
| **Why add?** | Constitution demands auditability, explainability, judge interview readiness. Each output field should map to rule IDs and observation IDs. |
| **Hidden rules** | Supports **RF-6** audits (prove instruction ignored); reproduces **ESM** reasons. |
| **If omitted?** | Cannot debug wrong rows; judge cannot trust “Rules Decide.” |
| **Failure modes prevented** | Opaque verdicts; irreproducible rule changes. |
| **Evaluation metric** | 100% of sample rows have complete trace; trace replay produces identical output. |
| **Verdict** | **Required for production quality**; **optional in hackathon** if templates + unit tests suffice. Recommend lightweight JSON trace per row. |

---

## 4. Components to Drop or Merge

| Proposed component | Recommendation | Rationale |
|--------------------|----------------|-----------|
| L3 as standalone service | **MERGE** into observation post-process | Single responsibility already; no extra runtime boundary. |
| L4 as standalone layer | **MERGE** into L1 prompt + L9 rules | Two injection surfaces; one policy document. |
| L5 + L6 | **Keep logical split; merge physical module** | Consistency feeds sufficiency; one `evidence` module with two functions. |
| L8 + L10 + L11 | **MERGE** into **Decision Matrix** | Same inputs, one ordered rule evaluation; sample shows tight coupling (**SV-3** with NEI). |
| L12 LLM prose | **DROP generative default** | Templates sufficient on sample; safer for determinism. |
| Second multimodal model for “end-to-end” | **DROP** | Violates constitution without strong evidence. |
| Caching layer | **OPTIONAL** | Not in proposal; add only after cost/latency measurement (L14). |
| Synthetic data generator | **OPTIONAL** | Constitution step 7; valuable for M1/multi-part but not blocking for 20-sample MVP. |

---

## 5. Recommended Architecture (Simpler, Constitution-Aligned)

Reduce **14 conceptual layers** to **8 implementable modules** without losing required capabilities:

```text
1. Intake
2. Observe
     2a. ClaimObserver (Flash)
     2b. ImageObserver (Pro, per image)
     2c. Normalize + Confidence Gate
3. ResolveClaim (primary part/issue for multi-part rows)     ← NEW
4. ReconcileEvidence
     4a. Consistency (cross-image)
     4b. RequirementMap + Sufficiency (ESM + reason)
     4c. Trust (valid_image)
5. Decide
     5a. Verdict + visible ontology (status, issue_type, object_part)
     5b. Severity
     5c. Supporting image IDs
6. AssessRisk (risk_flags + history propagation)
7. Explain (template composer from decision trace)
8. Emit (CSV row)

Offline: EvaluationHarness + DecisionTrace store
```

**Why simpler is sufficient:** The sample labels show a **strict decision order**:

1. `evidence_standard_met` gates `claim_status` (**CS-1**, 20/20 consistent).
2. `valid_image` is orthogonal (**VI-1**).
3. `risk_flags` never flip status (**CS-3**).
4. `severity` follows status (**SV-3**).

A single **ordered decision matrix** (module 5) replaces three “engines” if rule order is explicit and tested.

**What we do not simplify away:**

- Two Gemini roles (Flash + Pro) — constitution-mandated.
- Separate risk pass after verdict — prevents history leakage.
- Per-image vision — **REQ_GENERAL_MULTI_IMAGE**.
- Explicit requirement mapper — `evidence_requirements.csv` is not machine-readable without it.

---

## 6. Evaluation Strategy per Layer (Judge View)

| Layer | Primary metric | Secondary metric | Sample size caveat |
|-------|----------------|------------------|-------------------|
| L1 Claim extract | Part + issue family match | Per-language accuracy | n=20; 2 Hindi rows |
| L2 Visual observe | Part + issue + flag F1 | Per-object-type breakdown | n=20 images ~25 |
| L3 Normalize | Schema compliance | — | Binary |
| L5 Consistency | `user_002` pattern recall | False NEI on `user_003` | n=1 positive |
| L6 Sufficiency | `evidence_standard_met` acc | NEI ⟺ false joint acc | n=3 NEI |
| L7 Trust | `valid_image` acc | — | n=2 false |
| L8 Verdict | `claim_status` acc | Contradiction subtype acc | Primary hackathon metric |
| L9 Risk | `RF-1` compliance | Exact flag-set match | Sparse flags |
| L10 Severity | Tier accuracy | NEI→`unknown` | n=3 |
| L11 Supporting IDs | Exact set match | — | n=20 |
| L12 Explain | Grounding checklist | — | Qualitative |
| **End-to-end** | Weighted field accuracy | `claim_status` + ESM + risk F1 | Report all 14 fields |

**Recommended primary score for iteration:**

```text
Score = 0.40 × claim_status_acc
      + 0.20 × evidence_standard_met_acc
      + 0.15 × risk_flags_F1
      + 0.10 × (issue_type_acc + object_part_acc) / 2
      + 0.10 × severity_acc
      + 0.05 × supporting_image_ids_exact_match
```

Justification: matches judge priorities (verdict correctness first) while forcing sufficiency and risk quality. Weights should be validated against sample ablations.

---

## 7. Summary Verdict Table

| Layer | Required | Optional | Unnecessary |
|-------|----------|----------|-------------|
| L0 Intake | ✓ | | |
| L1 Claim Observer (Flash) | ✓ | | |
| L2 Image Observer (Pro) | ✓ | | |
| L3 Ontology gate | ✓ (as function) | | |
| L4 Adversarial sanitizer | | ✓ (merge) | |
| L5 Consistency engine | ✓ | | |
| L6 Evidence sufficiency + mapper | ✓ | | |
| L7 Trust / valid_image | ✓ | | |
| L8 Verdict engine | ✓ | | |
| L9 Risk aggregator | ✓ | | |
| L10 Severity | ✓ (merge w/ L8) | | |
| L11 Supporting IDs | ✓ (merge w/ L8) | | |
| L12 Explanation | ✓ (templates) | LLM prose | |
| L13 Output assembler | ✓ | | |
| L14 Evaluation harness | ✓ | | |
| **M1 Primary claim resolver** | **✓ ADD** | | |
| **M2 Confidence gate** | **✓ ADD** | | |
| **M3 Decision trace** | | **✓ ADD** | |
| End-to-end multimodal LLM verdict | | | **✓ REJECT** |
| Extra model beyond Flash+Pro | | | **✓ REJECT** |

---

## 8. Critical Risks Remaining After Architecture Approval

1. **Requirement mapper ambiguity** — `applies_to` strings are informal; mapper must be codified and tested before L6 is trustworthy.
2. **Multi-part claims** — M1 is mandatory for test set; sample labels do not validate it.
3. **`valid_image` boundary** — only 2 negative examples; rules will be fragile without synthetic cases.
4. **Severity rubric** — **SV-4** (default `medium`) is weak; decision matrix needs explicit tier definitions.
5. **`hidden_business_rules.md` missing** — architecture review depends on sample-derived rules that are not yet a repo artifact; **create before implementation**.

---

## 9. Approval Recommendation

**Conditionally approve** the constitution-backed architecture with these modifications:

1. Adopt the **8-module simplified structure** (Section 5).
2. **Add M1 Primary Claim Resolver** and **M2 Confidence Gate** before evidence/decision modules.
3. **Merge** L8+L10+L11 into one tested Decision Matrix; keep L9 Risk as a separate pass.
4. **Persist** hidden business rules to `docs/hidden_business_rules.md`.
5. **Replace** `architecture.md` stub with the approved diagram after this review is accepted.

No code should be written until the requirement mapper table and multi-part resolution policy are documented as decision matrices (constitution step 3).
