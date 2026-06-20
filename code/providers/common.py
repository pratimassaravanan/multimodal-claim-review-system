"""Shared provider utilities: retries, timeouts, schema checks, forbidden keys."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from typing import Any, TypeVar

from providers.exceptions import (
    ForbiddenProviderOutputError,
    ProviderError,
    ProviderSchemaValidationError,
    ProviderTimeoutError,
)

T = TypeVar("T")

FORBIDDEN_OUTPUT_KEYS: frozenset[str] = frozenset(
    {
        "claim_status",
        "evidence_standard_met",
        "evidence_standard_met_reason",
        "severity",
        "risk_flags",
        "risk_flag",
        "supported",
        "contradicted",
        "not_enough_information",
        "valid_image",
        "manual_review_required",
        "supporting_image_ids",
        "claim_status_justification",
        "claim_status_rule_id",
        "severity_rule_id",
        "supporting_image_rule_id",
    }
)


def hash_raw_payload(payload: str | bytes) -> str:
    data = payload if isinstance(payload, bytes) else payload.encode("utf-8")
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def find_forbidden_keys(value: Any, *, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            current = f"{path}.{key}" if path else key
            if key in FORBIDDEN_OUTPUT_KEYS:
                hits.append(current)
            hits.extend(find_forbidden_keys(nested, path=current))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(find_forbidden_keys(item, path=f"{path}[{index}]"))
    return hits


def strip_forbidden_fields(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if key in FORBIDDEN_OUTPUT_KEYS:
            continue
        if isinstance(value, dict):
            cleaned[key] = strip_forbidden_fields(value)
        elif isinstance(value, list):
            cleaned[key] = [
                strip_forbidden_fields(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned


def assert_no_forbidden_fields(payload: Any) -> None:
    hits = find_forbidden_keys(payload)
    if hits:
        raise ForbiddenProviderOutputError(
            f"Provider output contained forbidden decision fields: {', '.join(hits)}"
        )


def _validate_node(value: Any, schema: dict[str, Any], path: str) -> None:
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(value, dict):
            raise ProviderSchemaValidationError(f"{path} expected object")
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ProviderSchemaValidationError(f"{path}.{key} is required")
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}))
            for key in value:
                if key not in allowed:
                    raise ProviderSchemaValidationError(f"{path}.{key} is not allowed")
        for key, child_schema in schema.get("properties", {}).items():
            if key in value:
                _validate_node(value[key], child_schema, f"{path}.{key}")
        return

    if schema_type == "array":
        if not isinstance(value, list):
            raise ProviderSchemaValidationError(f"{path} expected array")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _validate_node(item, item_schema, f"{path}[{index}]")
        return

    if schema_type == "string":
        if not isinstance(value, str):
            raise ProviderSchemaValidationError(f"{path} expected string")
        enum = schema.get("enum")
        if enum and value not in enum:
            raise ProviderSchemaValidationError(f"{path} must be one of {enum}")
        return

    if schema_type == "boolean":
        if not isinstance(value, bool):
            raise ProviderSchemaValidationError(f"{path} expected boolean")
        return

    if schema_type in {"number", "integer"}:
        if not isinstance(value, (int, float)):
            raise ProviderSchemaValidationError(f"{path} expected number")
        return

    if "enum" in schema:
        if value not in schema["enum"]:
            raise ProviderSchemaValidationError(f"{path} must be one of {schema['enum']}")


def validate_json_schema(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate provider JSON against a small JSON-schema subset."""
    _validate_node(payload, schema, "$")


def parse_json_response(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Provider response was not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ProviderError("Provider JSON root must be an object")
    return parsed


def retry_with_backoff(
    func: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.25,
    retry_exceptions: tuple[type[Exception], ...] = (ProviderError, TimeoutError),
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except retry_exceptions as exc:
            last_error = exc
            if attempt >= max_attempts:
                break
            time.sleep(base_delay_seconds * attempt)
    assert last_error is not None
    raise last_error


def with_timeout(func: Callable[[], T], *, timeout_seconds: float) -> T:
    """Best-effort timeout wrapper using a worker thread."""
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError as exc:
            raise ProviderTimeoutError(
                f"Provider call exceeded {timeout_seconds}s timeout"
            ) from exc
