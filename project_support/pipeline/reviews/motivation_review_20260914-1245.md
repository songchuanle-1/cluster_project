# Motivation Review - cluster_project
2026-09-14 12:45, design tick; upstream snapshot generated 12:43:55 local.

## 1. Goal
Authoritative source: pipeline/goal.json, all 13 constraints and 11 bans read.
Target ScanRefer mIoU >= .51; Phase1 NOT YET. Exact M95 .5024607181549072;
baseline .4894491136074066; gap .0075392818450928.
Changed C1 requires consistent historical resource accounting. Supplemental
counts cannot reject a candidate alone when the parent also fails that count.
All other constraints remain in force, including scientific admission.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Context helps | historical support | goal findings | not SCM evidence |
| SCM joint spatial output improves wrong-instance selection | unverified | 0945 derivation, fixed diagnostics | novelty and training efficacy |
| SCM fails resources at 76.479G | superseded disposition | changed C1 | historical matched-input count |
| Boundary and adjacency losses address measured deficits | unverified | 1101 derivations | specific prevalence and novelty |
| Direct span head is new | rejected as formulated | retained 2411.03405 Eq6 comparison | no new admissible mechanism |

## 3. Experiment Assessment
No new terminal IDs. M191 .4917144179344177 and M193 .4906114339828491
remain below M95; no successors. SCM was never trained or withdrawn from queue.
Reassessing its resource ruling is not a retry of a failed training route.
Original bank: 284 expressions/71 scenes, M95 recoverables111, same-category
63/111 and disjoint selected/oracle89/111. These do not prove boundary errors.
Frozen TRAIN8/2scenes and mined21/11scenes are not efficacy populations.

## 4. Gap Analysis
SCM and parent retained Torch profiles both count14.073542358G, same operators.
SCM fvcore5.43422148G is on TRAIN scene0000_00/object10/annotation136.
Cluster/tools/train.py model_profile uses first VAL sample, one expression.
Thus neither supplemental76.479G nor TRAIN5.434G is the historical absolute
admission answer. Preserve both as diagnostic evidence, not a unilateral gate.
Five targeted web queries this tick returned no usable source content:
3D grounding Wasserstein segmentation; selection mixture Wasserstein
segmentation; boundary loss segmentation Kervadec; referring segmentation
optimal transport; 3D grounding spatial Wasserstein loss.
No absence-of-prior-art conclusion follows. Exact application novelty remains open.

## 5. Design Rationale
Reconcile the changed rule and audit retained code/evidence before new compute.
Prioritize SCM's already supported error hypothesis; do not manufacture three
additional names. Boundary/adjacency need their own deficit evidence; direct span
still fails novelty and small-head smell regardless of the resource correction.
This advances admission correctness without asserting an efficacy result.

## 6. Next Batch
See designs/exp_design_20260914-1245.md. Budget4, admitted0 pending scientific
clearance. No queue, scheduler, goal or production deployment modification.
