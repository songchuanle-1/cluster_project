# Fixed Casebook Sampling Audit
Completed 2026-09-13T03:10:34.672005 Asia/Shanghai.

## Source And Denominator
Source: pipeline\reports\d1_case_scope_coupling_20260912-1610\case_scope_coupling.json; SHA256: 201b60f24cc31ee613f6e25a3a1d78a36ee49c90df30835d733e900be225a0ea.
All three upstream source hashes verified. Baseline/M95 expression IDs match:
21 unique descriptions each, 42 total records, zero missing IDs.
The 21 descriptions cover 11 scenes and 20 scene-object pairs.
Only 9 scenes contain both selected errors and controls.
Repeated objects: [{"scene": "scene0046_00", "object": "26", "descriptions": 2}].
Full IDs are in audit.json; no new cases, labels, inference or training.

## Scene Coverage
| Scene | Selected Errors | Selected Controls | Distinct Objects |
|-------|-----------------|-------------------|------------------|
| scene0046_00 | 1 | 1 | 1 |
| scene0146_00 | 1 | 1 | 2 |
| scene0208_00 | 1 | 0 | 1 |
| scene0249_00 | 1 | 1 | 2 |
| scene0328_00 | 1 | 1 | 2 |
| scene0334_00 | 1 | 1 | 2 |
| scene0426_00 | 1 | 1 | 2 |
| scene0578_00 | 1 | 1 | 2 |
| scene0591_00 | 1 | 1 | 2 |
| scene0621_00 | 2 | 0 | 2 |
| scene0652_00 | 1 | 1 | 2 |

## Interpretation And Admission
The earlier 12/12 recoverable-error and 9/9 successful-control contrast is
outcome-selected, not an estimate of a population failure rate. Description
counts are not independent scene counts. Scene grouping cannot undo selection
bias, and a bootstrap on this casebook would not establish generalization.
Use these cases for deterministic regression tests only; select any evaluation
subset by outcome-independent criteria before mechanism testing. No novel
forward/loss follows from this coverage check. Mechanism admission remains
incomplete; no new selector, reranker, shared-anchor mechanism or successor.
