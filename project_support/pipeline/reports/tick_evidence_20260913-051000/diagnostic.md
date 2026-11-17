# Frozen Supervision And Outcome Audit
Completed 2026-09-13T05:10:13.038750 Asia/Shanghai.

## Question And Provenance
Is selected_positive interchangeable with selected_iou>=0.5 in the casebook?
Source: pipeline\reports\d1_case_scope_coupling_20260912-1610\case_scope_coupling.json; SHA256 201b60f24cc31ee613f6e25a3a1d78a36ee49c90df30835d733e900be225a0ea.
All three upstream hashes verified; 42 unique model-description records;
21 descriptions per model, zero missing/duplicate records.

## Contingency
| Model | Selected Positive Label | IoU Success | Count |
|-------|-------------------------|-------------|-------|
| baseline | False | False | 6 |
| baseline | True | False | 1 |
| baseline | True | True | 14 |
| m95 | False | False | 12 |
| m95 | True | True | 9 |

Discordant records: 1. Full IDs and source fields are retained
in audit.json. The two fields represent different diagnostic definitions;
do not infer a parser bug, or force equality, from a disagreement.

## Interpretation And Boundary
Supervision-positive status is not a substitute for measured segmentation
success. Future fixed-fixture checks must preserve both fields and use the
existing selected_iou threshold for outcome strata. This audit checks source
field semantics only, not training-time label construction or correctness.
It does not establish a new failure mechanism or justify replacing supervision.
These outcome-selected cases are not independent evidence, a population
confusion matrix, an unbiased error rate, or a generalization test.
No new inference, labels, dataset, loss, model, checkpoint or queue mutation.
