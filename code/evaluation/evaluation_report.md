# Evaluation Report

Dataset: `D:\multimodal-claim-review-system\dataset\sample_claims.csv`
Rows evaluated: 20
Provider mode: `gemini`
Evaluated at: 2026-06-20T05:12:21.823797+00:00

## Summary Metrics (claim_status)

| Metric | Value |
| --- | --- |
| Accuracy | 15.00% |
| Macro-F1 | 8.70% |
| False Support Rate | 0.00% |

## Precision / Recall / F1

| Class | Precision | Recall | F1 |
| --- | --- | --- | --- |
| supported | 0.00% | 0.00% | 0.00% |
| contradicted | 0.00% | 0.00% | 0.00% |
| not_enough_information | 15.00% | 100.00% | 26.09% |

## Confusion Matrix

Rows = expected (gold), columns = predicted.

| expected \ predicted | supported | contradicted | not_enough_information |
| --- | --- | --- | --- |
| supported | 0 | 0 | 12 |
| contradicted | 0 | 0 | 5 |
| not_enough_information | 0 | 0 | 3 |

## False Support Rate

Definition: `FP_supported / (FP_supported + TN_supported)` where gold `claim_status` ≠ supported.

- False supports (predicted supported, gold ≠ supported): 0
- Denominator (gold ≠ supported): 8
- Rate: 0.00%

## Row-Level claim_status Mismatches

| row_id | expected | predicted |
| --- | --- | --- |
| `user_001:case_001` | `supported` | `not_enough_information` |
| `user_004:case_003` | `supported` | `not_enough_information` |
| `user_007:case_004` | `supported` | `not_enough_information` |
| `user_005:case_005` | `contradicted` | `not_enough_information` |
| `user_003:case_007` | `supported` | `not_enough_information` |
| `user_008:case_008` | `contradicted` | `not_enough_information` |
| `user_009:case_009` | `supported` | `not_enough_information` |
| `user_010:case_010` | `supported` | `not_enough_information` |
| `user_011:case_011` | `supported` | `not_enough_information` |
| `user_012:case_012` | `supported` | `not_enough_information` |
| `user_018:case_013` | `supported` | `not_enough_information` |
| `user_020:case_014` | `contradicted` | `not_enough_information` |
| `user_015:case_015` | `supported` | `not_enough_information` |
| `user_030:case_016` | `supported` | `not_enough_information` |
| `user_031:case_017` | `supported` | `not_enough_information` |
| `user_033:case_019` | `contradicted` | `not_enough_information` |
| `user_034:case_020` | `contradicted` | `not_enough_information` |
