"""Set-level consistency aggregation from §0.5 predicates."""

from __future__ import annotations

from datetime import datetime

from contracts.enums import ClaimObject
from contracts.resolution import ClaimResolutionContext, EvidenceContext
from contracts.reconciliation import ConsistencyContext
from rules.identity_helpers import collect_identity_conflict_pairs, parse_identity_features
from rules.confidence import confidence_at_least
from rules.predicates import compute_all_predicates
from rules.types import ConsistencyStageResult


def build_consistency_context(
    evidence: EvidenceContext,
    resolution: ClaimResolutionContext,
    *,
    evaluated_at: datetime,
) -> ConsistencyStageResult:
    bundle = compute_all_predicates(evidence.claim, evidence.images, resolution)
    snapshot = bundle.snapshot
    pairs = collect_identity_conflict_pairs(evidence.images)

    consistent_vehicle = True
    if evidence.claim.claim_object is ClaimObject.CAR and evidence.images:
        colors: set[str] = set()
        for image in evidence.images:
            if confidence_at_least(image.depicts_claim_object.confidence, "medium") and image.depicts_claim_object.value:
                features = parse_identity_features(image.vehicle_identity_features)
                if "color" in features:
                    colors.add(features["color"])
        if len(colors) > 1:
            consistent_vehicle = False

    consistency = ConsistencyContext(
        row_id=evidence.claim.row_id,
        image_count=len(evidence.images),
        identity_conflict=snapshot.identity_conflict,
        identity_conflict_image_pairs=pairs,
        wrong_object_set=snapshot.wrong_object_set,
        consistent_vehicle_features=consistent_vehicle,
        best_part_image_ids=snapshot.best_part_image_ids,
        evaluated_at=evaluated_at,
        claim_object=evidence.claim.claim_object.value,
    )
    return ConsistencyStageResult(consistency=consistency, rule_records=[])
