# Motivation Review - cluster_project
2026-09-14 16:07 local; design tick; source snapshot 08:07:09 UTC.

## 1. Goal
Authoritative goal.json read in full: target ScanRefer mIoU >= .51;
13 constraints and 11 bans. Exact retained M95 .5024607181549072,
baseline .4894491136074066, gap .0075392818450928. Phase1 not reached.
Budget3, active1/target4. No new terminal evidence; preflight already complete.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Context helps | historical support | M95 vs baseline +.013012 | not SCM evidence |
| SCM improves hard selection | running, unverified | 1405 admission; M194 epoch4 best .4102 | full validation and hard-mask diagnostics |
| Boundary supervision helps | held | 1101 derivation; 1247 resource-veto correction | boundary-specific denominator and novelty |
| Adjacency supervision helps | held | 1101 derivation | fragmentation denominator and novelty |
| Token-span classifier is a new core | rejected as formulated | 1101 retained Eq6 comparison | duplicates existing objective; small-head smell |

## 3. Experiment Assessment
| Experiment | mIoU | Relation to motivation | Contribution |
|---|---:|---|---|
| model_base1 | .489449 | no cluster | historical reference |
| M95 | .502461 | strongest retained context parent | below target |
| M191 | .491714 | selector/readout | negative successor evidence |
| M193 | .490611 | hierarchy consensus | negative successor evidence |
M194 .4102 is an early running value, not a terminal comparison.

## 4. Gap Analysis
The original diagnostic bank has111/284 recoverables and89/111 disjoint
selected/oracle masks. This does not measure boundary displacement or
fragmentation prevalence. No new dataset or terminal evidence resolves either
hold. The old candidate-only sparse resource rejection is superseded; it must
not be reused to reject these candidates.
SCM's known equal-marginal blind spot is separate from a possible disagreement
between normalized soft-mask transport and deployed hard-mask quality.

## 5. Design Rationale
Advance a bounded offline falsifier audit of admitted SCM: construct an unequal-
marginal, one-dimensional example where a worse thresholded candidate has lower
transport and is favored by selector gradients. This tests a mathematical risk,
not its prevalence, novelty, or empirical efficacy. No new loss is proposed.
Use the retained NumPy reference, not a training job or a production patch.

## 6. Next Batch
Reassess the three distinct existing proposals against budget3; admit0.
Do not call these three newly designed variants or allocate experiment IDs.
See designs/exp_design_20260914-1607.md. Continue M194 and preserve FIFO,
capacity, schedule, seed and all existing controls.
