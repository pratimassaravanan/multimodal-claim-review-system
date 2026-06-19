# Multi-Modal Claim Review — Code

## Phase P0 (current)

Contracts (`contracts/`) and ontology (`ontology/`) layers per `docs/pydantic_contracts_v2.md`.

## Setup

```bash
cd code
pip install -e ".[dev]"
```

## Run tests

```bash
pytest tests/ -v
```

## Layout

- `contracts/` — Pydantic v2 models for all pipeline contracts
- `ontology/` — Enum constants, validation, normalization helpers
