"""Claim-status evaluation metrics per docs/evaluation_metrics.md §2.1–2.4."""

from __future__ import annotations

from dataclasses import dataclass

from contracts.enums import ClaimStatus

CLAIM_STATUS_LABELS: tuple[str, ...] = (
    ClaimStatus.SUPPORTED.value,
    ClaimStatus.CONTRADICTED.value,
    ClaimStatus.NOT_ENOUGH_INFORMATION.value,
)


@dataclass(frozen=True)
class ClaimStatusMetrics:
    accuracy: float
    precision: dict[str, float]
    recall: dict[str, float]
    f1: dict[str, float]
    macro_f1: float
    confusion_matrix: list[list[int]]
    false_support_rate: float
    false_support_fp: int
    false_support_denominator: int
    total_rows: int


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_confusion_matrix(
    expected: list[str],
    predicted: list[str],
    labels: tuple[str, ...] = CLAIM_STATUS_LABELS,
) -> list[list[int]]:
    index = {label: idx for idx, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    for gold, pred in zip(expected, predicted, strict=True):
        matrix[index[gold]][index[pred]] += 1
    return matrix


def compute_claim_status_metrics(
    expected: list[str],
    predicted: list[str],
    *,
    labels: tuple[str, ...] = CLAIM_STATUS_LABELS,
) -> ClaimStatusMetrics:
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have the same length")

    matrix = compute_confusion_matrix(expected, predicted, labels)
    total = len(expected)
    accuracy = _safe_div(sum(matrix[i][i] for i in range(len(labels))), total)

    precision: dict[str, float] = {}
    recall: dict[str, float] = {}
    f1: dict[str, float] = {}
    for idx, label in enumerate(labels):
        tp = matrix[idx][idx]
        fp = sum(matrix[row][idx] for row in range(len(labels)) if row != idx)
        fn = sum(matrix[idx][col] for col in range(len(labels)) if col != idx)
        p = _safe_div(tp, tp + fp)
        r = _safe_div(tp, tp + fn)
        precision[label] = p
        recall[label] = r
        f1[label] = _safe_div(2 * p * r, p + r)

    macro_f1 = _safe_div(sum(f1.values()), len(labels))

    supported = ClaimStatus.SUPPORTED.value
    fp_supported = sum(
        1
        for gold, pred in zip(expected, predicted, strict=True)
        if pred == supported and gold != supported
    )
    tn_supported = sum(
        1
        for gold, pred in zip(expected, predicted, strict=True)
        if pred != supported and gold != supported
    )
    false_support_rate = _safe_div(fp_supported, fp_supported + tn_supported)

    return ClaimStatusMetrics(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        macro_f1=macro_f1,
        confusion_matrix=matrix,
        false_support_rate=false_support_rate,
        false_support_fp=fp_supported,
        false_support_denominator=fp_supported + tn_supported,
        total_rows=total,
    )
