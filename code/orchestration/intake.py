"""Load ClaimContext and dataset catalogs from CSV inputs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from contracts.enums import ClaimObject, DatasetSplit
from contracts.intake import ClaimContext
from ontology.normalize import parse_history_flags

PIPELINE_VERSION = "1.0.0"
UNIVERSAL_REQUIREMENT_IDS = ("REQ_GENERAL_OBJECT_PART", "REQ_REVIEW_TRUST")
MULTI_IMAGE_REQUIREMENT_ID = "REQ_GENERAL_MULTI_IMAGE"


@dataclass(frozen=True)
class ClaimInputRow:
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: ClaimObject


@dataclass(frozen=True)
class UserHistoryRecord:
    user_id: str
    past_claim_count: int
    accept_claim: int
    manual_review_claim: int
    rejected_claim: int
    last_90_days_claim_count: int
    history_flags: str
    history_summary: str | None


def _repo_dataset_root(repo_root: Path) -> Path:
    return repo_root / "dataset"


def load_user_history(repo_root: Path) -> dict[str, UserHistoryRecord]:
    path = _repo_dataset_root(repo_root) / "user_history.csv"
    records: dict[str, UserHistoryRecord] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            records[row["user_id"]] = UserHistoryRecord(
                user_id=row["user_id"],
                past_claim_count=int(row["past_claim_count"]),
                accept_claim=int(row["accept_claim"]),
                manual_review_claim=int(row["manual_review_claim"]),
                rejected_claim=int(row["rejected_claim"]),
                last_90_days_claim_count=int(row["last_90_days_claim_count"]),
                history_flags=row["history_flags"],
                history_summary=row.get("history_summary") or None,
            )
    return records


def load_requirement_ids(repo_root: Path) -> dict[str, list[str]]:
    path = _repo_dataset_root(repo_root) / "evidence_requirements.csv"
    by_object: dict[str, list[str]] = {"all": []}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            claim_object = row["claim_object"]
            requirement_id = row["requirement_id"]
            by_object.setdefault(claim_object, []).append(requirement_id)
            if claim_object == "all":
                by_object["all"].append(requirement_id)
    return by_object


def load_claim_rows(claims_csv: Path) -> list[ClaimInputRow]:
    rows: list[ClaimInputRow] = []
    with claims_csv.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                ClaimInputRow(
                    user_id=row["user_id"],
                    image_paths=row["image_paths"],
                    user_claim=row["user_claim"],
                    claim_object=ClaimObject(row["claim_object"]),
                )
            )
    return rows


def _extract_case_folder(image_paths: str) -> str:
    first_path = image_paths.split(";")[0].strip()
    for part in Path(first_path).parts:
        if part.startswith("case_"):
            return part
    return Path(first_path).parent.name


def _split_image_paths(image_paths: str) -> list[str]:
    return [piece.strip() for piece in image_paths.split(";") if piece.strip()]


def _image_id_from_path(path: str) -> str:
    return Path(path).stem


def build_applicable_requirement_ids(
    claim_object: ClaimObject,
    *,
    image_count: int,
    requirements_by_object: dict[str, list[str]],
) -> list[str]:
    ids: list[str] = []
    for requirement_id in requirements_by_object.get("all", []):
        if requirement_id not in ids:
            ids.append(requirement_id)
    for requirement_id in requirements_by_object.get(claim_object.value, []):
        if requirement_id not in ids:
            ids.append(requirement_id)
    if image_count >= 2 and MULTI_IMAGE_REQUIREMENT_ID not in ids:
        ids.append(MULTI_IMAGE_REQUIREMENT_ID)
    return ids


def build_claim_context(
    row: ClaimInputRow,
    *,
    repo_root: Path,
    user_history: dict[str, UserHistoryRecord],
    requirements_by_object: dict[str, list[str]],
    observed_at: datetime,
    dataset_split: DatasetSplit = DatasetSplit.TEST,
) -> ClaimContext:
    image_paths = _split_image_paths(row.image_paths)
    case_folder = _extract_case_folder(row.image_paths)
    row_id = f"{row.user_id}:{case_folder}"
    dataset_root = _repo_dataset_root(repo_root)
    resolved_files = [str((dataset_root / path).resolve()) for path in image_paths]
    image_ids = [_image_id_from_path(path) for path in image_paths]
    history = user_history.get(row.user_id)
    if history is None:
        raise KeyError(f"Missing user history for {row.user_id}")

    return ClaimContext(
        row_id=row_id,
        user_id=row.user_id,
        claim_object=row.claim_object,
        user_claim=row.user_claim,
        image_paths=image_paths,
        image_ids=image_ids,
        image_count=len(image_ids),
        resolved_image_files=resolved_files,
        history_flags=parse_history_flags(history.history_flags),
        history_summary=history.history_summary,
        past_claim_count=history.past_claim_count,
        accept_claim=history.accept_claim,
        manual_review_claim=history.manual_review_claim,
        rejected_claim=history.rejected_claim,
        last_90_days_claim_count=history.last_90_days_claim_count,
        applicable_requirement_ids=build_applicable_requirement_ids(
            row.claim_object,
            image_count=len(image_ids),
            requirements_by_object=requirements_by_object,
        ),
        pipeline_version=PIPELINE_VERSION,
        observed_at=observed_at,
        dataset_split=dataset_split,
        case_folder=case_folder,
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
