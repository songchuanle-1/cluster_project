# Frozen Paired-Outcome Regression Audit
Completed 2026-09-13T04:10:27.341302 Asia/Shanghai.

## Question And Provenance
Does the casebook sampling role denote each model's actual outcome?
Source: pipeline\reports\d1_case_scope_coupling_20260912-1610\case_scope_coupling.json; SHA256 201b60f24cc31ee613f6e25a3a1d78a36ee49c90df30835d733e900be225a0ea.
All three upstream hashes verified. All42 records joined into21 unique
baseline/M95 pairs; missing IDs0, duplicate model-ID pairs0.
Descriptions, target labels, scopes and sampling roles agree across each pair.
Selected IoU never exceeds the corresponding bank oracle; success labels
agree with the existing IoU>=0.5 diagnostic threshold for all42 records.

## Paired Outcomes
| Baseline Outcome | M95 Outcome | Descriptions |
|------------------|-------------|--------------|
| recoverable | recoverable | 7 |
| success | recoverable | 5 |
| success | success | 9 |

## Interpretation
The error/control role was selected using M95, not baseline. A baseline record
with role=error can therefore be a successful prediction, not a labeling bug.
These paired transitions are deterministic regression fixtures only: the
outcome-selected21 descriptions cannot estimate either model's population
gain, a paired significance test or a generalization result. Their11 scenes
and20 objects are unchanged from the sampling audit. Do not silently redefine
roles per model or select a mechanism by maximizing performance on these cases.
No new labels, inference, data acquisition, mechanism or training is involved.
