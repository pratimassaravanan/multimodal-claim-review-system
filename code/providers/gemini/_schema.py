"""Load and dereference provider JSON schemas."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


def _resolve_refs(node: object, defs: dict[str, object]) -> object:
    if isinstance(node, dict):
        if "$ref" in node:
            ref = node["$ref"]
            if ref.startswith("#/$defs/"):
                key = ref.rsplit("/", 1)[-1]
                return _resolve_refs(defs[key], defs)
            raise ValueError(f"Unsupported schema ref: {ref}")
        return {key: _resolve_refs(value, defs) for key, value in node.items() if key != "$defs"}
    if isinstance(node, list):
        return [_resolve_refs(item, defs) for item in node]
    return node


@lru_cache(maxsize=4)
def load_provider_schema(name: str) -> dict[str, object]:
    path = SCHEMA_DIR / name
    raw = json.loads(path.read_text(encoding="utf-8"))
    defs = raw.get("$defs", {})
    resolved = _resolve_refs({key: value for key, value in raw.items() if key != "$defs"}, defs)
    assert isinstance(resolved, dict)
    return resolved
