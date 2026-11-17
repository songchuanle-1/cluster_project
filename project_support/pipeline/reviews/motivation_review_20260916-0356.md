# Motivation Review - Attribute Supervision Availability
2026-09-16 03:56.

## 1. Goal
Authoritative goal.json remains Phase1,target .51;exact M95 .5024607181549072.
All14constraints/11bans unchanged. No new model or training admission.

## 2. Story Status
| Hypothesis | State | Evidence | Gap |
|---|---|---|---|
| Same-class wrong selections persist | observed | prior fixedTRAIN captures | mechanism |
| Model lacks attribute loss | false | native loss_sem_align | not a new repair |
| Attribute maps generally absent in errors | unsupported | native token-map audit | semantic correctness |

## 3. Experiment Assessment
M95/M195 metrics unchanged;M196 retained.
Native16TRAIN batches123expressions loaded on server6;no model forward/training.
Scene/annotation identities joined against existing123expression capture.

## 4. Gap Analysis
| Subset | Expressions | Empty target | Empty attribute | Empty relation |
|---|---|---|---|---|
| Success | 85 | 0 | 24 | 8 |
| Confident wrong | 31 | 0 | 7 | 5 |
| Other failure | 7 | 0 | 1 | 1 |
All maps have zero positive positions outside valid token length.
Outcome-defined counts are descriptive,not independent causal evidence.
No automatic equation between empty map and parser error.

## 5. Design Rationale
Native loss already consumes modify_positive_map and rel_positive_map in both
query-to-token and token-to-query terms. A generic missing-attribute-loss proposal
does not match source behavior or this coverage evidence.
Presence does not establish correct semantic assignments or effective gradients.
Do not change loss weights or invent annotation corrections from these counts.

## 6. Next Batch
Retain evidence for a distinct compositional mechanism;no repeat map-coverage audit.
Original-source distinction and native behavior/resource/independence gates remain.
Decision20260916-035632_next_batch.md. Workerexit0;no training process started.
