"""Load labeled rows from dataset/sample_claims.csv."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from contracts.enums import ClaimObject
from orchestration.emit import OUTPUT_COLUMNS
from orchestration.intake import ClaimInputRow, _extract_case_folder

LABEL_COLUMNS: tuple[str, ...] = tuple(
    column
    for column in OUTPUT_COLUMNS
    if column not in ("user_id", "image_paths", "user_claim", "claim_object")
)


@dataclass(frozen=True)
class SampleClaimRow:
    row_id: str
    input_row: ClaimInputRow
    expected: dict[str, str]


def load_sample_claims(sample_csv: Path) -> list[SampleClaimRow]:
    rows: list[SampleClaimRow] = []
    with sample_csv.open(encoding="utf-8", newline="") as handle:
        for raw in csv.DictReader(handle):
            input_row = ClaimInputRow(
                user_id=raw["user_id"],
                image_paths=raw["image_paths"],
                user_claim=raw["user_claim"],
                claim_object=ClaimObject(raw["claim_object"]),
            )
            case_folder = _extract_case_folder(input_row.image_paths)
            row_id = f"{input_row.user_id}:{case_folder}"
            expected = {column: raw[column] for column in LABEL_COLUMNS}
            rows.append(SampleClaimRow(row_id=row_id, input_row=input_row, expected=expected))
    return rows
