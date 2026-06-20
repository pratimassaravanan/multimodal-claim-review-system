"""Evidence sufficiency matrix — decision_matrix §1 (ESM-R01..ESM-R08)."""

from __future__ import annotations

from datetime import datetime

from contracts.reconciliation import ConsistencyContext, ValidationContext, ValidationPredicates
from contracts.resolution import ClaimResolutionContext, EvidenceContext
from rules.identity_helpers import identity_constraint_active, identity_matchable_across_best_set
from rules.predicates import compute_all_predicates
from rules.requirements_map import build_active_requirement_ids, evaluate_all_requirements
from rules.types import RuleExecutionRecord, SufficiencyStageResult, TraceField


ESM_REASON_KEYS = {
    "ESM-R01": "esm_r01_unreadable_file",
    "ESM-R02": "esm_r02_identity_conflict",
    "ESM-R03": "esm_r03_no_part_visible",
    "ESM-R04": "esm_r04_contents_not_shown",
    "ESM-R05": "esm_r05_part_low_confidence",
    "ESM-R06": "esm_r06_part_not_clear",
    "ESM-R07": "esm_r07_identity_not_matchable",
    "ESM-R08": "esm_r08_default_met",
}


def _record(
    rule_id: str,
    outcome: bool,
    justification: str,
    *pairs: tuple[str, str],
) -> RuleExecutionRecord:
    return RuleExecutionRecord(
        rule_id=rule_id,
        outcome=outcome,
        justification=justification,
        trace_fields=[TraceField(key=k, value=v) for k, v in pairs],
    )


def _has_high_part_confidence(images: list) -> bool:
    return any(
        img.claimed_primary_part_visible.value
        and img.claimed_primary_part_visible.confidence == "high"
        for img in images
    )


def evaluate_sufficiency(
    evidence: EvidenceContext,
    resolution: ClaimResolutionContext,
    consistency: ConsistencyContext,
    *,
    evaluated_at: datetime,
) -> SufficiencyStageResult:
    _ = consistency
    bundle = compute_all_predicates(evidence.claim, evidence.images, resolution)
    snapshot = bundle.snapshot
    observation = evidence.claim_observation

    identity_active = identity_constraint_active(observation)
    active_requirements = build_active_requirement_ids(
        claim_object=evidence.claim.claim_object,
        primary_issue_family=resolution.primary_issue_family,
        image_count=len(evidence.images),
        identity_constraint_active=identity_active,
    )
    requirement_bundle = evaluate_all_requirements(active_requirements, snapshot, evidence.images)
    requirements_satisfied = {
        result.requirement_id: result.satisfied for result in requirement_bundle.results
    }

    predicates = ValidationPredicates(
        part_clear=snapshot.part_clear,
        no_part_visible=snapshot.no_part_visible,
        part_visible_low_only=snapshot.part_visible_low_only,
        identity_conflict=snapshot.identity_conflict,
        contents_claim=snapshot.contents_claim,
        contents_area_clear=snapshot.contents_area_clear,
        any_file_unreadable=snapshot.any_file_unreadable,
        best_part_confidence=snapshot.best_part_confidence,
        best_part_image_ids=snapshot.best_part_image_ids,
    )

    records: list[RuleExecutionRecord] = []
    triggered_rule_id = "ESM-R08"
    evidence_standard_met = True
    reason_template_key = ESM_REASON_KEYS["ESM-R08"]
    reason_template_vars = {"part": resolution.primary_object_part.value}
    identity_match_detail: str | None = None

    ordered_checks: list[tuple[str, bool, str, tuple[tuple[str, str], ...]]] = [
        (
            "ESM-R01",
            snapshot.any_file_unreadable,
            "Unreadable file prevents evidence evaluation.",
            (("any_file_unreadable", str(snapshot.any_file_unreadable).lower()),),
        ),
        (
            "ESM-R02",
            snapshot.identity_conflict,
            "Vehicle identity conflict across images.",
            (("identity_conflict", str(snapshot.identity_conflict).lower()),),
        ),
        (
            "ESM-R03",
            snapshot.no_part_visible,
            "Claimed part not visible on any image.",
            (("no_part_visible", str(snapshot.no_part_visible).lower()),),
        ),
        (
            "ESM-R04",
            snapshot.contents_claim and not snapshot.contents_area_clear,
            "Contents claim without visible contents area.",
            (
                ("contents_claim", str(snapshot.contents_claim).lower()),
                ("contents_area_clear", str(snapshot.contents_area_clear).lower()),
            ),
        ),
        (
            "ESM-R05",
            snapshot.part_visible_low_only and not _has_high_part_confidence(evidence.images),
            "Part visible only at low confidence without high-confidence image.",
            (("part_visible_low_only", str(snapshot.part_visible_low_only).lower()),),
        ),
        (
            "ESM-R06",
            not snapshot.part_clear,
            "Claimed primary part not clear enough for inspection.",
            (("part_clear", str(snapshot.part_clear).lower()),),
        ),
    ]

    for rule_id, matched, justification, pairs in ordered_checks:
        records.append(_record(rule_id, matched, justification, *pairs))
        if matched:
            triggered_rule_id = rule_id
            evidence_standard_met = False
            reason_template_key = ESM_REASON_KEYS[rule_id]
            if rule_id == "ESM-R02":
                identity_match_detail = "identity_conflict_detected"
            break
    else:
        matchable, detail = identity_matchable_across_best_set(
            observation,
            evidence.images,
            snapshot.best_part_image_ids,
        )
        esm_r07_matched = identity_active and not matchable
        records.append(
            _record(
                "ESM-R07",
                esm_r07_matched,
                "Claimed vehicle identity not matchable across best-part images."
                if esm_r07_matched
                else "Identity constraint satisfied or not active.",
                ("identity_constraint_active", str(identity_active).lower()),
                ("identity_matchable", str(matchable).lower()),
                ("detail", detail),
            )
        )
        if esm_r07_matched:
            triggered_rule_id = "ESM-R07"
            evidence_standard_met = False
            reason_template_key = ESM_REASON_KEYS["ESM-R07"]
            identity_match_detail = detail
        else:
            records.append(
                _record(
                    "ESM-R08",
                    True,
                    "Default evidence sufficiency met; no higher-priority ESM rule matched.",
                    ("evidence_standard_met", "true"),
                )
            )

    validation = ValidationContext(
        row_id=evidence.claim.row_id,
        evidence_standard_met=evidence_standard_met,
        triggered_rule_id=triggered_rule_id,
        reason_template_key=reason_template_key,
        reason_template_vars=reason_template_vars,
        active_requirement_ids=active_requirements,
        requirements_satisfied=requirements_satisfied,
        predicates=predicates,
        evaluated_at=evaluated_at,
        identity_match_detail=identity_match_detail,
    )
    return SufficiencyStageResult(validation=validation, rule_records=records)
