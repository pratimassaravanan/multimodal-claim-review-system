"""Deterministic mock providers for offline development and tests."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from contracts.enums import (
    ClaimObject,
    ClaimedSeverityLanguage,
    DamageExtent,
    IdentitySide,
    IssueType,
    ObjectPart,
)
from contracts.intake import ClaimContext
from contracts.observation import ClaimObservation, ImageEvidence
from contracts.primitives import ConfidenceLevel, ScoredField
from ontology.issue_families import is_family_compatible_with_part, map_issue_type_to_family
from ontology.normalize import normalize_claimed_severity_language, normalize_issue_type, normalize_object_part
from providers.common import hash_raw_payload


def _confidence(value: str) -> ConfidenceLevel:
    if value in {"high", "medium", "low"}:
        return value  # type: ignore[return-value]
    return "medium"


def _scored_bool(
    value: bool,
    confidence: ConfidenceLevel = "medium",
    *,
    source_module: str,
    source_image_id: str | None = None,
) -> ScoredField[bool]:
    return ScoredField(
        value=value,
        confidence=confidence,
        source_module=source_module,  # type: ignore[arg-type]
        source_image_id=source_image_id,
    )


class MockFlashProvider:
    """Heuristic claim observer — no external API."""

    model_name = "mock-gemini-2.5-flash"
    prompt_version = "mock-claim-v1"

    def observe_claim(self, claim: ClaimContext, *, observed_at: datetime) -> ClaimObservation:
        text = claim.user_claim.lower()
        detected = (
            ["hi"]
            if re.search(r"[\u0900-\u097F]|\bmein\b|\bmeri\b", claim.user_claim, re.IGNORECASE)
            else ["en"]
        )
        sanitized = claim.user_claim.split("|")[-1].strip() if "|" in claim.user_claim else claim.user_claim.strip()

        part = self._infer_part(text, claim.claim_object)
        issue = self._ensure_compatible_issue(part, claim.claim_object, self._infer_issue(text, claim.claim_object))
        identity_active = any(token in text for token in ("blue", "red", "left", "right", "front", "rear", "my "))
        side = self._infer_side(text)
        color = self._infer_color(text)
        severity_language = normalize_claimed_severity_language(
            "exaggerated"
            if any(token in text for token in ("pretty bad", "severe", "exaggerated", "badly"))
            else "medium"
        )
        injection = "approve this claim" in text or "ignore instructions" in text
        injection_excerpt = "approve this claim" if injection else None
        if injection:
            sanitized = sanitized.replace("approve this claim", "[redacted]").replace(
                "ignore instructions", "[redacted]"
            )

        alleged_parts = [part]
        alleged_issue_types = [issue]
        families = [
            map_issue_type_to_family(issue, claim.claim_object, part),
        ]
        raw = {
            "detected_languages": detected,
            "sanitized_claim_excerpt": sanitized,
            "alleged_parts": [part.value],
            "alleged_issue_types": [issue.value],
        }
        return ClaimObservation(
            row_id=claim.row_id,
            alleged_parts=alleged_parts,
            alleged_issue_types=alleged_issue_types,
            alleged_issue_families=families,
            exclusions=[],
            identity_constraint_active=_scored_bool(
                identity_active,
                "high" if identity_active else "low",
                source_module="claim_observer",
            ),
            identity_side=ScoredField(
                value=side,
                confidence="high",
                source_module="claim_observer",
                source_image_id=None,
            )
            if side
            else None,
            identity_color=ScoredField(
                value=color,
                confidence="high",
                source_module="claim_observer",
                source_image_id=None,
            )
            if color
            else None,
            claimed_damage_alleged=_scored_bool(True, "high", source_module="claim_observer"),
            claimed_severity_language=_scored_bool(
                severity_language,
                "medium",
                source_module="claim_observer",
            ),
            multi_part_detected=False,
            injection_detected_in_chat=injection,
            injection_excerpt=injection_excerpt,
            sanitized_claim_excerpt=sanitized[:500],
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            observation_raw_hash=hash_raw_payload(str(raw)),
            observed_at=observed_at,
            detected_languages=detected,
            last_customer_message_excerpt=sanitized[:200],
            overall_extraction_confidence="medium",
            claim_object=claim.claim_object,
        )

    def _infer_part(self, text: str, claim_object: ClaimObject) -> ObjectPart:
        if claim_object is ClaimObject.PACKAGE:
            if "label" in text:
                return ObjectPart.LABEL
            if "seal" in text:
                return ObjectPart.SEAL
            if "corner" in text:
                return ObjectPart.PACKAGE_CORNER
            if any(token in text for token in ("contents", "inside item", "product inside", "item inside")):
                return ObjectPart.ITEM if "item" in text else ObjectPart.CONTENTS
            if "missing" in text and "contents" in text:
                return ObjectPart.CONTENTS
            return ObjectPart.BOX
        if claim_object is ClaimObject.LAPTOP:
            if "trackpad" in text:
                return ObjectPart.TRACKPAD
            if "keyboard" in text or "teclado" in text or "teclas" in text or "keycap" in text:
                return ObjectPart.KEYBOARD
            if "hinge" in text:
                return ObjectPart.HINGE
            if "lid" in text:
                return ObjectPart.LID
            if "corner" in text or "palm-rest" in text:
                return ObjectPart.CORNER
            if "port" in text:
                return ObjectPart.PORT
            if "body" in text and "screen" not in text:
                return ObjectPart.BASE
            if "screen" in text or "pantalla" in text or "display" in text:
                return ObjectPart.SCREEN
            return ObjectPart.BASE
        if "windshield" in text or "front glass" in text:
            return ObjectPart.WINDSHIELD
        if "side mirror" in text or ("mirror" in text and "side" in text):
            return ObjectPart.SIDE_MIRROR
        if "taillight" in text or "tail light" in text or "back light" in text:
            return ObjectPart.TAILLIGHT
        if "headlight" in text:
            return ObjectPart.HEADLIGHT
        if "door" in text:
            return ObjectPart.DOOR
        if "hood" in text or "hail" in text:
            return ObjectPart.HOOD
        if "front bumper" in text or ("front" in text and "bumper" in text):
            return ObjectPart.FRONT_BUMPER
        if "rear bumper" in text or "parachoques" in text or "bumper" in text:
            return ObjectPart.REAR_BUMPER
        if "body panel" in text or "car body" in text:
            return ObjectPart.BODY
        return normalize_object_part("rear_bumper", claim_object)

    def _infer_issue(self, text: str, claim_object: ClaimObject) -> IssueType:
        if claim_object is ClaimObject.PACKAGE:
            if "torn" in text or "opened" in text:
                return IssueType.TORN_PACKAGING
            if "crush" in text:
                return IssueType.CRUSHED_PACKAGING
            if "missing" in text:
                return IssueType.MISSING_PART
            if any(token in text for token in ("stain", "oil", "wet", "water")):
                return IssueType.STAIN
        if claim_object is ClaimObject.LAPTOP:
            if any(token in text for token in ("liquid", "water", "coffee", "spill", "stain", "rain")):
                return IssueType.STAIN
            if any(token in text for token in ("missing", "keycap", "teclas", "faltan")):
                return IssueType.BROKEN_PART
        if "scratch" in text or "scrape" in text:
            return IssueType.SCRATCH
        if "shatter" in text:
            return IssueType.GLASS_SHATTER if claim_object is ClaimObject.CAR else IssueType.CRACK
        if "crack" in text or "cracked" in text:
            return IssueType.CRACK if claim_object is ClaimObject.LAPTOP else IssueType.BROKEN_PART
        if "broken" in text or "toot" in text:
            return IssueType.BROKEN_PART
        if "dent" in text or "dab" in text or "danado" in text or "dano" in text:
            return IssueType.DENT
        if "hail" in text:
            return IssueType.DENT
        return normalize_issue_type("dent")

    def _ensure_compatible_issue(
        self,
        part: ObjectPart,
        claim_object: ClaimObject,
        issue: IssueType,
    ) -> IssueType:
        family = map_issue_type_to_family(issue, claim_object, part)
        if is_family_compatible_with_part(family, claim_object, part):
            return issue

        candidates: list[IssueType] = [issue]
        if claim_object is ClaimObject.LAPTOP:
            candidates.extend([IssueType.STAIN, IssueType.BROKEN_PART, IssueType.CRACK, IssueType.DENT])
        elif claim_object is ClaimObject.CAR:
            candidates.extend(
                [IssueType.BROKEN_PART, IssueType.CRACK, IssueType.GLASS_SHATTER, IssueType.DENT, IssueType.SCRATCH]
            )
        elif claim_object is ClaimObject.PACKAGE:
            candidates.extend(
                [
                    IssueType.CRUSHED_PACKAGING,
                    IssueType.TORN_PACKAGING,
                    IssueType.STAIN,
                    IssueType.MISSING_PART,
                    IssueType.WATER_DAMAGE,
                ]
            )

        for candidate in candidates:
            candidate_family = map_issue_type_to_family(candidate, claim_object, part)
            if is_family_compatible_with_part(candidate_family, claim_object, part):
                return candidate
        return issue

    def _infer_side(self, text: str) -> IdentitySide | None:
        for side in IdentitySide:
            if side.value in text:
                return side
        return None

    def _infer_color(self, text: str) -> str | None:
        for color in ("blue", "red", "black", "white", "silver"):
            if color in text:
                return color
        return None


class MockProProvider:
    """Heuristic image observer — no external API."""

    model_name = "mock-gemini-2.5-pro"
    prompt_version = "mock-vision-v1"

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
        path_exists = __import__("pathlib").Path(image_path).is_file()
        if claim.claim_object is ClaimObject.PACKAGE:
            default_part = primary_object_part or ObjectPart.BOX
            default_issue = IssueType.NONE
        elif claim.claim_object is ClaimObject.LAPTOP:
            default_part = primary_object_part or ObjectPart.SCREEN
            default_issue = IssueType.CRACK
        else:
            default_part = primary_object_part or ObjectPart.REAR_BUMPER
            default_issue = IssueType.DENT
        part = default_part
        issue = default_issue
        extent = DamageExtent.MEDIUM if path_exists else DamageExtent.UNKNOWN
        readable = path_exists
        raw = {"image_id": image_id, "file_readable": readable, "observation_pass": observation_pass}
        low = "low"
        high = "high"
        return ImageEvidence(
            row_id=claim.row_id,
            image_id=image_id,
            image_path=image_path,
            file_readable=readable,
            usable_for_automated_review=readable,
            depicts_claim_object=_scored_bool(True, high if readable else low, source_module="image_observer", source_image_id=image_id),
            visible_part=_scored_bool(part, high if readable else low, source_module="image_observer", source_image_id=image_id),
            claimed_primary_part_visible=_scored_bool(True, high if readable else low, source_module="image_observer", source_image_id=image_id),
            visible_issue_type=_scored_bool(issue, high if readable else low, source_module="image_observer", source_image_id=image_id),
            visible_damage_extent=_scored_bool(extent, high if readable else low, source_module="image_observer", source_image_id=image_id),
            is_blurry=_scored_bool(False, low, source_module="image_observer", source_image_id=image_id),
            is_cropped_or_obstructed=_scored_bool(False, low, source_module="image_observer", source_image_id=image_id),
            is_low_light_or_glare=_scored_bool(False, low, source_module="image_observer", source_image_id=image_id),
            is_wrong_angle_for_claimed_part=_scored_bool(False, low, source_module="image_observer", source_image_id=image_id),
            is_non_original_image=_scored_bool(False, low, source_module="image_observer", source_image_id=image_id),
            is_possibly_manipulated=_scored_bool(False, low, source_module="image_observer", source_image_id=image_id),
            has_instruction_text=_scored_bool(False, low, source_module="image_observer", source_image_id=image_id),
            package_is_opened=_scored_bool(False, low, source_module="image_observer", source_image_id=image_id),
            contents_area_visible=_scored_bool(False, low, source_module="image_observer", source_image_id=image_id),
            vehicle_identity_features=[],
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            observed_at=observed_at,
            observation_pass=observation_pass,
            observation_raw_hash=hash_raw_payload(str(raw)),
            claim_object=claim.claim_object,
            allowed_image_ids=claim.image_ids,
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


class MockProvider:
    """Bundle of mock Flash + Pro providers."""

    def __init__(self) -> None:
        self.flash = MockFlashProvider()
        self.pro = MockProProvider()
