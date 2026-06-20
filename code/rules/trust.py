"""Valid image matrix — decision_matrix §2 (VI-R01..VI-R04)."""

from __future__ import annotations

from datetime import datetime

from contracts.resolution import ClaimResolutionContext, EvidenceContext
from contracts.reconciliation import TrustAssessmentContext
from rules.confidence import confidence_at_least
from rules.predicates import compute_all_predicates
from rules.types import RuleExecutionRecord, TraceField, TrustStageResult


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


def _contents_unreviewable(evidence: EvidenceContext, resolution: ClaimResolutionContext) -> bool:
    bundle = compute_all_predicates(evidence.claim, evidence.images, resolution)
    if not bundle.snapshot.contents_claim or bundle.snapshot.contents_area_clear:
        return False
    if not evidence.images:
        return False
    return all(
        image.is_cropped_or_obstructed.value
        and confidence_at_least(image.is_cropped_or_obstructed.confidence, "high")
        for image in evidence.images
    )


def evaluate_trust(
    evidence: EvidenceContext,
    resolution: ClaimResolutionContext,
    *,
    evaluated_at: datetime,
) -> TrustStageResult:
    bundle = compute_all_predicates(evidence.claim, evidence.images, resolution)
    snapshot = bundle.snapshot
    records: list[RuleExecutionRecord] = []

    checks = [
        (
            "VI-R01",
            snapshot.all_images_unusable,
            "All images unusable for automated review.",
            (("all_images_unusable", str(snapshot.all_images_unusable).lower()),),
        ),
        (
            "VI-R02",
            snapshot.any_non_original_high,
            "Non-original image detected at high confidence.",
            (("any_non_original_high", str(snapshot.any_non_original_high).lower()),),
        ),
    ]

    triggered_rule_id = "VI-R04"
    valid_image = True
    trust_failure_image_ids: list[str] = []
    trust_failure_reason: str | None = None

    for rule_id, matched, justification, pairs in checks:
        records.append(_record(rule_id, matched, justification, *pairs))
        if matched:
            triggered_rule_id = rule_id
            valid_image = False
            if rule_id == "VI-R02":
                trust_failure_image_ids = [
                    img.image_id
                    for img in evidence.images
                    if img.is_non_original_image.value
                    and confidence_at_least(img.is_non_original_image.confidence, "high")
                ]
            trust_failure_reason = justification
            break
    else:
        contents_unreviewable = _contents_unreviewable(evidence, resolution)
        records.append(
            _record(
                "VI-R03",
                contents_unreviewable,
                "Contents claim without visible contents and all images cropped or obstructed."
                if contents_unreviewable
                else "Contents reviewability check passed.",
                ("contents_unreviewable", str(contents_unreviewable).lower()),
            )
        )
        if contents_unreviewable:
            triggered_rule_id = "VI-R03"
            valid_image = False
            trust_failure_image_ids = [img.image_id for img in evidence.images]
            trust_failure_reason = "contents_unreviewable"
        else:
            records.append(
                _record(
                    "VI-R04",
                    True,
                    "Default valid_image=true; no trust failure rule matched.",
                    ("valid_image", "true"),
                )
            )

    contents_unreviewable = _contents_unreviewable(evidence, resolution)

    trust = TrustAssessmentContext(
        row_id=evidence.claim.row_id,
        valid_image=valid_image,
        triggered_rule_id=triggered_rule_id,
        all_images_unusable=snapshot.all_images_unusable,
        any_non_original_high=snapshot.any_non_original_high,
        contents_unreviewable=contents_unreviewable,
        trust_failure_image_ids=trust_failure_image_ids,
        evaluated_at=evaluated_at,
        trust_failure_reason=trust_failure_reason,
    )
    return TrustStageResult(trust=trust, rule_records=records)
