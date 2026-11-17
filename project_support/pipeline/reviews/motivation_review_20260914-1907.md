# Motivation Review - cluster_project
2026-09-14 19:07 Asia/Shanghai. Design tick; budget2.

## 1. Goal
Source: pipeline/goal.json, read in full this tick (13 constraints,11 bans).
Full quoted goal contract: motivation_review_20260914-1705.md section1;
no goal changes are reported by preflight. Target ScanRefer mIoU>=.51.
Exact historical M95 .5024607182;baseline .4894491136;Phase1 NOT YET.

## 2. Story Status
| Hypothesis | State | Evidence | Gap |
|---|---|---|---|
| Spatial output supervision helps hard grounding | unverified | M194 running9/50,.4649 | terminal validation |
| Common-seed paired switching helps identity | unverified | M195 waiting;313 eligible frozen pairs | optimization mass versus hard errors |
| Displaced boundaries need distance supervision | held | existing1101/1607 proposal | specific boundary diagnosis,original-source distinction |
| Fragmented masks need adjacency supervision | held | existing1101/1607 proposal | measured fragmentation/contact evidence,novelty |

## 3. Experiment Assessment
No new terminal IDs. Do not reinterpret early M194 trajectory as success/failure.
M95 exact peak16 remains champion;ledger .5020@22 is historical metadata.
M184-M191/M193 old route screens remain closed;no descendants or retries.
M195 admission is not evidence of generalization or adequate native TRAIN mass.

## 4. Gap Analysis
Saved CPS audit has four native seed-logit cells,Delta,row margins,hard IoUs
and scene identities. These support a new OFFLINE cross-tab without recapturing
banks:how often positive assignment margins coexist with hard errors, and how
much unweighted pair-loss derivative mass falls in each stratum?
This cannot identify boundary versus selection errors;do not use it to admit
either held boundary/adjacency candidate. Frozen mined VAL is not TRAIN.

## 5. Design Rationale
Budget2:screen the two previously formulated,structurally distinct boundary
and adjacency proposals. Neither has completed C9/C10;admit0,not renamed IDs.
Instead audit the already admitted CPS mechanism's surrogate limitations.
For L=softplus(-Delta),absolute derivative is sigmoid(-Delta);positive Delta
alone neither guarantees two row margins positive nor two correct hard masks.
Compute exact counts,scene denominators,stable loss/derivative,source hash,
full pair identities and scene-cluster uncertainty. No changed training rule.

## 6. Next Batch
See designs/exp_design_20260914-1907.md. No new model/config or queue mutation.
Keep M194 and M195 contracts/FIFO intact;do not combine SCM+CPS or alter weights.
Pending questions in snapshot:[];record audit limitations locally,not an
interactive approval request.
