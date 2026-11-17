# Motivation Review - Admission Constraint Audit And The Missing Causal Test
2026-09-16 11:30 Asia/Shanghai. Audit plus one causal intervention; nothing admitted.

## 1. Goal
pipeline/goal.json authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact .5024607181549072@16; Phase 1 NOT YET.

## 2. Why An Audit
Several turns had accumulated the claim "every remaining direction is prior art or
banned". That claim mixes three different kinds of authority and can silently become
self-imposed over-restriction. This review separates them and re-derives exactly what
is closed, by what, and on what stated basis.

## 3. Authority Split
**A. goal.json literal bans (11).** gate系; 语言路由系; attnpool/qcond/agg/multi;
prune; nomask; 3/4/6 层重复注入; 大型 Q/K/V/O 投影; Phase1 调参系; the Phase1
parameter-count principle (<5K params with no new compute graph; numeric-distribution
only; underived hyperparameters; "added one single layer/operator at X"); true_route /
显式 routing 注入; residual 系.

Notably absent from that list: any ban on referent-positive relabelling, on
mask-aware matching, on query-to-GT assignment, or on modality fusion. Those
exclusions come from the next two categories, not from goal.json.

**B. Recorded decisions (authoritative as project policy).**
- 20260913-061110: "Does the positive-label IoU-failure fixture justify supervision
  repair or queue refill?" - decision "No label repair or unadmitted refill", basis
  "Source-identical assignment and 568 frozen records agree; label membership is not
  mask IoU. **Scientific admission remains incomplete.**"
- 20260913-071026: "Does nearest-query assignment prevalence justify relabeling or
  refill at zero waiting?" - decision "No relabeling or unadmitted refill", basis
  "568 frozen rows distinguish added positives from actual selection; **descriptive
  association is not causal evidence.** Scientific admission remains incomplete."

Both state their basis explicitly, and in both the stated basis is *insufficient
evidence*, not novelty. They close the route conditionally on the evidence being
descriptive.

**C. My own accumulated inference.** The "assignment-successor family" phrasing and
the merged "closed" lists are my summarisation, not goal.json text. Per the concurrent
audit: recorded policy binds, but goal.json literal bans remain the authoritative
list, and I must neither broaden nor relax them.

## 4. The Missing Causal Test
The 09-13 basis names exactly what was missing: a causal intervention rather than a
descriptive association. That test had not been run. It needs no training and no new
annotation: hold the checkpoint fixed and change only *which* query is selected,
inside one same-forward capture.

| Selection rule | pooled | scene-balanced | scene bootstrap 95% CI |
|---|---|---|---|
| deployed argmax over all 128 queries | 69.1% | 68.75% | [57.8, 78.9] |
| argmax restricted to the native training-positive set (oracle) | **87.0%** | **86.7%** | **[80.5, 92.2]** |
| argmax restricted to "seed inside ANY instance" | 69.1% | 68.75% | [57.8, 78.9] |

Paired effect of the positive restriction: **+17.9 pp** pooled and scene-balanced,
95% CI **[+10.9, +25.8]**, with **22 expressions fixed and 0 broken** - it strictly
dominates the deployed rule.

Supporting structure: 95.1% of expressions have at least one positive; mean 6.5
positives per expression; the "any instance" restriction is available for
essentially every query (mean 114.4 of 128), which is why that control is exactly
null.

## 5. What This Establishes
1. **Causality is now established.** Selection outside the native training-positive
   set causes a large, strictly one-directional share of the failures. The stated
   basis of the 09-13 decisions - "descriptive association is not causal evidence" -
   no longer holds.
2. **The effect is referent identity, not objectness.** Restricting to "seed inside
   any instance" changes nothing at all (69.1% -> 69.1%, identical to the third
   decimal). The gain comes specifically from knowing which object is *referred*.
   This is a new negative control that constrains every future mechanism: anything
   that merely prefers queries whose seed sits inside some object is provably inert
   here.
3. **The remaining blocker is novelty, not evidence.** The fix the causality points
   to (make referent positives agree with the object hypothesis) is RefMask3D's
   mask-aware matching with a cls+BCE+dice cost, and DETR-style one-to-one
   assignment. That is prior art, so it cannot be this project's contribution.

## 6. What Is Still Closed, And Why
Unchanged and not reopened: multi-scale/pooling/selector/readback (decision-inert,
0/123 winner changes); readouts and region scoring (measured to fail; region scoring
also prior art); modality re-weighting / extra fusion / gating (MDIN prior art, and
numeric); the 2D identity lead (closed 1135: identity-rich but not
language-addressable); instance-pure re-partitioning (weak causal link, banned
pooling family).

## 7. Consequence For The Objective
The objective requires a *qualified* variant - novel and derived. The audit shows the
blocker is now exactly one axis: novelty. The evidence axis is resolved, the resource
and independence gates are procedural, and the causality is measured. This is the
cleanest possible statement of the decision the project needs, and it is recorded as
question 101512.

## 8. Next Batch
-> see pipeline/designs/exp_design_20260916-1130.md
Status: AUDIT COMPLETE / CAUSALITY ESTABLISHED / NOVELTY STILL BLOCKING / NOT ADMITTED.
