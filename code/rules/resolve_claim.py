"""Multi-part claim resolution — decision_matrix §7 (MP-1..MP-5)."""

from __future__ import annotations

from datetime import datetime

from contracts.enums import ClaimObject, IssueFamily, IssueType, ObjectPart, ResolutionMethod
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.resolution import ClaimResolutionContext
from ontology.issue_families import map_issue_type_to_family
from rules.confidence import CONFIDENCE_RANK
from rules.types import ResolveClaimStageResult, RuleExecutionRecord, TraceField


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


def _visibility_score(part: ObjectPart, images: list[ImageEvidence]) -> int:
    best = 0
    for image in images:
        if image.visible_part.value == part:
            best = max(best, CONFIDENCE_RANK[image.visible_part.confidence])
    return best


def _last_mention_tiebreak(parts: list[ObjectPart], excerpt: str | None) -> ObjectPart:
    if not excerpt or len(parts) < 2:
        return parts[0]
    lower = excerpt.lower()
    last_index = -1
    winner = parts[0]
    for part in parts:
        token = part.value.replace("_", " ")
        index = lower.rfind(token)
        if index > last_index:
            last_index = index
            winner = part
    return winner


def _select_primary_issue_family(
    claim_object: ClaimObject,
    primary_part: ObjectPart,
    alleged_issue_types: list[IssueType],
) -> IssueFamily:
    return map_issue_type_to_family(alleged_issue_types[0], claim_object, primary_part)


def resolve_claim(
    claim: ClaimContext,
    observation: ClaimObservation,
    images: list[ImageEvidence],
    *,
    evaluated_at: datetime,
) -> ResolveClaimStageResult:
    records: list[RuleExecutionRecord] = []
    affirmed_parts = list(observation.alleged_parts)

    records.append(
        _record(
            "MP-1",
            True,
            "Collected customer-affirmed parts from claim observation.",
            ("affirmed_parts", ",".join(p.value for p in affirmed_parts)),
            ("part_count", str(len(affirmed_parts))),
        )
    )

    if len(affirmed_parts) == 1:
        primary_part = affirmed_parts[0]
        secondary_parts: list[ObjectPart] = []
        records.append(
            _record(
                "MP-2",
                True,
                "Single affirmed part selected as primary.",
                ("primary_object_part", primary_part.value),
            )
        )
        resolution_method = ResolutionMethod.SINGLE_PART
        resolution_rule_ids = ["MP-1", "MP-2"]
    else:
        records.append(
            _record(
                "MP-2",
                False,
                "Multiple affirmed parts require visibility scoring.",
                ("affirmed_part_count", str(len(affirmed_parts))),
            )
        )
        scores = {part: _visibility_score(part, images) for part in affirmed_parts}
        records.append(
            _record(
                "MP-3",
                True,
                "Computed visibility score per affirmed part.",
                *(("score_" + part.value, str(score)) for part, score in scores.items()),
            )
        )
        max_score = max(scores.values())
        leaders = [part for part, score in scores.items() if score == max_score]
        if len(leaders) == 1:
            primary_part = leaders[0]
            records.append(
                _record(
                    "MP-4",
                    True,
                    "Selected primary part by visibility score.",
                    ("primary_object_part", primary_part.value),
                    ("visibility_score", str(max_score)),
                )
            )
            resolution_method = ResolutionMethod.VISIBILITY_SCORE
            resolution_rule_ids = ["MP-1", "MP-3", "MP-4"]
        else:
            primary_part = _last_mention_tiebreak(leaders, observation.last_customer_message_excerpt)
            records.append(
                _record(
                    "MP-4",
                    True,
                    "Visibility tie resolved by last customer message mention.",
                    ("primary_object_part", primary_part.value),
                    ("tied_parts", ",".join(p.value for p in leaders)),
                    ("tie_break", "last_mention"),
                )
            )
            resolution_method = ResolutionMethod.LAST_MENTION_TIEBREAK
            resolution_rule_ids = ["MP-1", "MP-3", "MP-4"]

        secondary_parts = [part for part in affirmed_parts if part != primary_part]
        if secondary_parts:
            records.append(
                _record(
                    "MP-5",
                    True,
                    "Remaining affirmed parts assigned as secondary.",
                    ("secondary_parts", ",".join(p.value for p in secondary_parts)),
                )
            )

    primary_issue_family = _select_primary_issue_family(
        claim.claim_object,
        primary_part,
        observation.alleged_issue_types,
    )
    part_visibility_scores = {part: _visibility_score(part, images) for part in affirmed_parts}

    resolution = ClaimResolutionContext(
        row_id=claim.row_id,
        claim_observation_ref=observation.observation_raw_hash,
        multi_part_claim=observation.multi_part_detected,
        primary_object_part=primary_part,
        primary_issue_family=primary_issue_family,
        secondary_object_parts=secondary_parts,
        resolution_method=resolution_method,
        resolution_rule_ids=resolution_rule_ids,
        part_visibility_scores=part_visibility_scores,
        resolved_at=evaluated_at,
        claim_object=claim.claim_object,
        alleged_parts=affirmed_parts,
    )
    return ResolveClaimStageResult(resolution=resolution, rule_records=records)
