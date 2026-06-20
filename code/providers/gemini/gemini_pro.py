"""Gemini 2.5 Pro image observer."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from contracts.enums import ObjectPart
from contracts.intake import ClaimContext
from contracts.observation import ImageEvidence
from contracts.primitives import ScoredField
from ontology.normalize import normalize_damage_extent, normalize_issue_type, normalize_object_part
from providers.common import (
    assert_no_forbidden_fields,
    hash_raw_payload,
    parse_json_response,
    strip_forbidden_fields,
    validate_json_schema,
)
from providers.gemini._client import GeminiClient
from providers.gemini._schema import load_provider_schema

PRO_SYSTEM_PROMPT = """You are a vision observation model for insurance evidence review.
Detect visible issue type, object part, visible damage extent, and image quality signals.

Return JSON only. Never output verdict or decision fields such as:
claim_status, evidence_standard_met, severity decision labels, risk_flags, supported,
contradicted, not_enough_information, valid_image, supporting_image_ids, or manual_review_required.

Report visible_damage_extent as an observation enum (none/low/medium/high/unknown), not a final severity decision."""

MODEL_NAME = "gemini-2.5-pro"
PROMPT_VERSION = "vision-v1"


def _image_scored(
    payload: dict[str, Any] | None,
    *,
    default_value: Any,
    image_id: str,
) -> ScoredField[Any]:
    if not payload:
        return ScoredField(
            value=default_value,
            confidence="low",
            source_module="image_observer",
            source_image_id=image_id,
        )
    confidence = payload.get("confidence", "medium")
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"
    return ScoredField(
        value=payload.get("value", default_value),
        confidence=confidence,
        confidence_score=payload.get("confidence_score"),
        source_module="image_observer",
        source_image_id=image_id,
    )


class GeminiProProvider:
    """Gemini Pro adapter producing ImageEvidence only."""

    def __init__(
        self,
        client: GeminiClient | None = None,
        *,
        model_name: str = MODEL_NAME,
        prompt_version: str = PROMPT_VERSION,
    ) -> None:
        self.client = client or GeminiClient()
        self.model_name = model_name
        self.prompt_version = prompt_version
        self._schema = load_provider_schema("pro_output.schema.json")

    def observe_image(
        self,
        claim: ClaimContext,
        *,
        image_id: str,
        image_path: str,
        primary_object_part: ObjectPart | None = None,
        observation_pass: Literal[1, 2] = 1,
        observed_at: datetime,
    ) -> ImageEvidence:
        user_prompt = (
            f"claim_object: {claim.claim_object.value}\n"
            f"row_id: {claim.row_id}\n"
            f"image_id: {image_id}\n"
            f"observation_pass: {observation_pass}\n"
            f"primary_object_part: {primary_object_part.value if primary_object_part else 'unknown'}\n"
            "Return JSON matching the observation schema."
        )
        raw_text = self.client.generate_json(
            model=self.model_name,
            system_instruction=PRO_SYSTEM_PROMPT,
            user_text=user_prompt,
            image_path=image_path,
        )
        payload = parse_json_response(raw_text)
        assert_no_forbidden_fields(payload)
        payload = strip_forbidden_fields(payload)
        validate_json_schema(payload, self._schema)
        return self._to_image_evidence(
            payload,
            claim=claim,
            image_id=image_id,
            image_path=image_path,
            observation_pass=observation_pass,
            observed_at=observed_at,
            raw_text=raw_text,
        )

    def observe_images(
        self,
        claim: ClaimContext,
        *,
        primary_object_part: ObjectPart | None = None,
        observation_pass: Literal[1, 2] = 1,
        observed_at: datetime,
    ) -> list[ImageEvidence]:
        return [
            self.observe_image(
                claim,
                image_id=image_id,
                image_path=path,
                primary_object_part=primary_object_part,
                observation_pass=observation_pass,
                observed_at=observed_at,
            )
            for image_id, path in zip(claim.image_ids, claim.resolved_image_files, strict=True)
        ]

    def _to_image_evidence(
        self,
        payload: dict[str, Any],
        *,
        claim: ClaimContext,
        image_id: str,
        image_path: str,
        observation_pass: Literal[1, 2],
        observed_at: datetime,
        raw_text: str,
    ) -> ImageEvidence:
        file_readable = bool(payload.get("file_readable", True))
        low_conf = "low"

        def image_scored(key: str, default_value: Any) -> ScoredField[Any]:
            scored = _image_scored(payload.get(key), default_value=default_value, image_id=image_id)
            if not file_readable:
                return scored.model_copy(update={"confidence": low_conf})
            return scored

        visible_part_scored = image_scored("visible_part", ObjectPart.UNKNOWN)
        visible_issue_scored = image_scored("visible_issue_type", "unknown")
        visible_extent_scored = image_scored("visible_damage_extent", "unknown")

        return ImageEvidence(
            row_id=claim.row_id,
            image_id=image_id,
            image_path=image_path,
            file_readable=file_readable,
            usable_for_automated_review=bool(payload.get("usable_for_automated_review", file_readable)),
            depicts_claim_object=image_scored("depicts_claim_object", True),
            visible_part=ScoredField(
                value=normalize_object_part(visible_part_scored.value, claim.claim_object),
                confidence=visible_part_scored.confidence,
                confidence_score=visible_part_scored.confidence_score,
                source_module="image_observer",
                source_image_id=image_id,
            ),
            claimed_primary_part_visible=image_scored("claimed_primary_part_visible", True),
            visible_issue_type=ScoredField(
                value=normalize_issue_type(visible_issue_scored.value),
                confidence=visible_issue_scored.confidence,
                confidence_score=visible_issue_scored.confidence_score,
                source_module="image_observer",
                source_image_id=image_id,
            ),
            visible_damage_extent=ScoredField(
                value=normalize_damage_extent(visible_extent_scored.value),
                confidence=visible_extent_scored.confidence,
                confidence_score=visible_extent_scored.confidence_score,
                source_module="image_observer",
                source_image_id=image_id,
            ),
            is_blurry=image_scored("is_blurry", False),
            is_cropped_or_obstructed=image_scored("is_cropped_or_obstructed", False),
            is_low_light_or_glare=image_scored("is_low_light_or_glare", False),
            is_wrong_angle_for_claimed_part=image_scored("is_wrong_angle_for_claimed_part", False),
            is_non_original_image=image_scored("is_non_original_image", False),
            is_possibly_manipulated=image_scored("is_possibly_manipulated", False),
            has_instruction_text=image_scored("has_instruction_text", False),
            package_is_opened=image_scored("package_is_opened", False),
            contents_area_visible=image_scored("contents_area_visible", False),
            vehicle_identity_features=[
                str(item) for item in payload.get("vehicle_identity_features", []) if str(item).strip()
            ],
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            observed_at=observed_at,
            observation_pass=observation_pass,
            observation_raw_hash=hash_raw_payload(raw_text),
            injection_text_excerpt=payload.get("injection_text_excerpt"),
            claim_object=claim.claim_object,
            allowed_image_ids=claim.image_ids,
        )
