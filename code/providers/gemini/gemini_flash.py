"""Gemini 2.5 Flash claim observer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from contracts.enums import ClaimObject, ClaimedSeverityLanguage, IdentitySide, IssueType, ObjectPart
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation
from contracts.primitives import ConfidenceLevel, ScoredField
from ontology.issue_families import map_issue_type_to_family
from ontology.normalize import (
    normalize_claimed_severity_language,
    normalize_issue_type,
    normalize_object_part,
)
from providers.common import (
    assert_no_forbidden_fields,
    hash_raw_payload,
    parse_json_response,
    strip_forbidden_fields,
    validate_json_schema,
)
from providers.exceptions import ProviderError
from providers.gemini._client import GeminiClient
from providers.gemini._schema import load_provider_schema

FLASH_SYSTEM_PROMPT = """You are a claim observation model for insurance evidence review.
Perform language detection, translate to concise English, extract alleged parts and issue types,
and normalize values to the allowed ontology strings.

Return JSON only. Never output verdict or decision fields such as:
claim_status, evidence_standard_met, severity, risk_flags, supported, contradicted,
not_enough_information, valid_image, supporting_image_ids, or manual_review_required.

Use visible observation language only. Do not decide whether the claim is supported."""

MODEL_NAME = "gemini-2.5-flash"
PROMPT_VERSION = "claim-v1"


def _scored_field(
    payload: dict[str, Any] | None,
    *,
    default_value: Any,
    source_module: str,
) -> ScoredField[Any]:
    if not payload:
        return ScoredField(
            value=default_value,
            confidence="low",
            source_module=source_module,  # type: ignore[arg-type]
            source_image_id=None,
        )
    confidence = payload.get("confidence", "medium")
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"
    return ScoredField(
        value=payload.get("value", default_value),
        confidence=confidence,
        confidence_score=payload.get("confidence_score"),
        source_module=source_module,  # type: ignore[arg-type]
        source_image_id=None,
    )


class GeminiFlashProvider:
    """Gemini Flash adapter producing ClaimObservation only."""

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
        self._schema = load_provider_schema("flash_output.schema.json")

    def observe_claim(self, claim: ClaimContext, *, observed_at: datetime) -> ClaimObservation:
        user_prompt = (
            f"claim_object: {claim.claim_object.value}\n"
            f"row_id: {claim.row_id}\n"
            f"user_claim:\n{claim.user_claim}\n\n"
            "Return JSON matching the observation schema."
        )
        raw_text = self.client.generate_json(
            model=self.model_name,
            system_instruction=FLASH_SYSTEM_PROMPT,
            user_text=user_prompt,
        )
        payload = parse_json_response(raw_text)
        assert_no_forbidden_fields(payload)
        payload = strip_forbidden_fields(payload)
        validate_json_schema(payload, self._schema)
        return self._to_claim_observation(payload, claim=claim, observed_at=observed_at, raw_text=raw_text)

    def _to_claim_observation(
        self,
        payload: dict[str, Any],
        *,
        claim: ClaimContext,
        observed_at: datetime,
        raw_text: str,
    ) -> ClaimObservation:
        alleged_parts = [
            normalize_object_part(part, claim.claim_object)
            for part in payload.get("alleged_parts", [])
            if str(part).strip()
        ]
        if not alleged_parts:
            alleged_parts = [ObjectPart.UNKNOWN]

        alleged_issue_types = [
            normalize_issue_type(issue) for issue in payload.get("alleged_issue_types", []) if str(issue).strip()
        ]
        if not alleged_issue_types:
            alleged_issue_types = [IssueType.UNKNOWN]

        families = [
            map_issue_type_to_family(issue, claim.claim_object, part)
            for issue, part in zip(alleged_issue_types, alleged_parts, strict=False)
        ]
        if not families:
            families = [
                map_issue_type_to_family(alleged_issue_types[0], claim.claim_object, alleged_parts[0]),
            ]

        identity_side_field = None
        identity_side_payload = payload.get("identity_side")
        if isinstance(identity_side_payload, dict) and identity_side_payload.get("value"):
            token = str(identity_side_payload["value"]).strip().lower()
            if token in IdentitySide._value2member_map_:
                identity_side_field = ScoredField(
                    value=IdentitySide(token),
                    confidence=identity_side_payload.get("confidence", "medium"),
                    confidence_score=identity_side_payload.get("confidence_score"),
                    source_module="claim_observer",
                    source_image_id=None,
                )

        identity_color_field = None
        identity_color_payload = payload.get("identity_color")
        if isinstance(identity_color_payload, dict) and identity_color_payload.get("value"):
            identity_color_field = ScoredField(
                value=str(identity_color_payload["value"]),
                confidence=identity_color_payload.get("confidence", "medium"),
                confidence_score=identity_color_payload.get("confidence_score"),
                source_module="claim_observer",
                source_image_id=None,
            )

        severity_language = normalize_claimed_severity_language(
            _scored_field(
                payload.get("claimed_severity_language"),
                default_value=ClaimedSeverityLanguage.NONE,
                source_module="claim_observer",
            ).value
        )

        sanitized = str(payload.get("sanitized_claim_excerpt", "")).strip()
        if not sanitized:
            raise ProviderError("sanitized_claim_excerpt must not be empty")

        overall_conf: ConfidenceLevel | None = payload.get("overall_extraction_confidence")
        if overall_conf not in {None, "high", "medium", "low"}:
            overall_conf = None

        return ClaimObservation(
            row_id=claim.row_id,
            alleged_parts=alleged_parts,
            alleged_issue_types=alleged_issue_types,
            alleged_issue_families=families,
            exclusions=[str(item) for item in payload.get("exclusions", [])],
            identity_constraint_active=_scored_field(
                payload.get("identity_constraint_active"),
                default_value=False,
                source_module="claim_observer",
            ),
            identity_side=identity_side_field,
            identity_color=identity_color_field,
            claimed_damage_alleged=_scored_field(
                payload.get("claimed_damage_alleged"),
                default_value=True,
                source_module="claim_observer",
            ),
            claimed_severity_language=ScoredField(
                value=severity_language,
                confidence=_scored_field(
                    payload.get("claimed_severity_language"),
                    default_value=ClaimedSeverityLanguage.NONE,
                    source_module="claim_observer",
                ).confidence,
                confidence_score=_scored_field(
                    payload.get("claimed_severity_language"),
                    default_value=ClaimedSeverityLanguage.NONE,
                    source_module="claim_observer",
                ).confidence_score,
                source_module="claim_observer",
                source_image_id=None,
            ),
            multi_part_detected=len(alleged_parts) > 1,
            injection_detected_in_chat=bool(payload.get("injection_detected_in_chat", False)),
            injection_excerpt=payload.get("injection_excerpt"),
            sanitized_claim_excerpt=sanitized,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            observation_raw_hash=hash_raw_payload(raw_text),
            observed_at=observed_at,
            detected_languages=[str(item) for item in payload.get("detected_languages", [])] or None,
            last_customer_message_excerpt=payload.get("last_customer_message_excerpt"),
            overall_extraction_confidence=overall_conf,
            claim_object=claim.claim_object,
        )
