# Motivation Review - Failure Decomposition By Training-Positive Membership
2026-09-16 11:02 Asia/Shanghai. Diagnostic only; nothing admitted.

## 1. Goal
pipeline/goal.json authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact .5024607181549072@16; Phase 1 NOT YET.

## 2. Why This Measurement
Earlier ticks concluded that the deployed referent head answers a point-level
question ("is my seed inside the referred object") instead of an object-level one,
and inferred that its positive set never requires mask agreement. That inference was
never measured. This tick intercepts the model's own `match_sampled_ins` at the
query-level call, so the measured set is the native set that supervises `loss_indi`,
the score regression and the mask losses.

## 3. Result: The Positive Set Is Not The Problem
| Quantity | Value |
|---|---|
| expressions / scenes | 123 / 32 |
| positive query-slots | 824 (6.7 per expression) |
| positives whose mask overlaps the target above IoU .5 | 783 (**95.0%**) |
| positives with a mask that does not | 41 (5.0%) |
| mask-OK queries excluded from positives | **2455** (3.0 per positive) |
| mean IoU of positive queries | .801 |
| mean IoU of the 41 bad positives | .374 |
| mean IoU of the 2455 excluded mask-OK queries | .770 |
| expressions with no mask-OK positive at all | 10 |

So the earlier inference was wrong in an important way: **the native positives already
agree with the mask 95% of the time**. The seed criterion approximately implies mask
agreement on this data. Retargeting positives to mask agreement therefore adds
mostly the 2455 *duplicate* hypotheses, and its main effect would be to stop calling
those duplicates "no object" -- which is precisely the mask-aware matching that
RefMask3D already does and this project bans. The earlier review's mechanism story
is superseded.

## 4. Result: The Failure Is Classifier Discrimination
Cross-tabulation of the deployed argmax selection:

| selected query | mask OK | mask bad | row total |
|---|---|---|---|
| is a training positive | 83 | 6 | 89 (72.4%) |
| is NOT a training positive | 2 | 32 | 34 (27.6%) |

- Success conditioned on selecting a positive: **93.3%** (83/89).
- Success conditioned on selecting a non-positive: **5.9%** (2/34).
- Current overall TRAIN success: **69.1%** (85/123).

The failure decomposition is therefore 32/38 (84%) "the top-scoring query was never
marked as a referent at training time", plus 6/38 "a trained positive whose own mask
is wrong". The head's problem is not that its positives are wrong; it is that it
fails to reject unmatched queries, and it has 2455 mask-OK negatives to reject.

## 5. Ceiling
If the selection could be restricted perfectly to training positives, and the
positive mask-OK rate of 95.0% carried over, TRAIN success would rise from 69.1% to
roughly 92-95%. A conservative floor that needs no extrapolation: 113 of 123
expressions (91.9%) contain at least one mask-OK positive, against 85 today. This
confirms referent selection remains by far the highest-value target, and it bounds
what any fix on this axis can deliver.

## 6. What This Changes
- Retract the "positives never require mask agreement" story; the measured rate is
  95% agreement. Keep only the measured version: 5% of positives are mask-bad, and
  the head's dominant error is accepting non-positives.
- The remaining fixed-radius explanation is label ambiguity: about 7 queries per
  expression are all labelled referent, so the ordering *within* the positive set is
  unconstrained by the referent loss, and 2455 mask-OK duplicates are labelled
  no-object. Set-based and one-to-one matching fixes for this are prior art
  (Hungarian/set losses) and sit inside the banned assignment-successor family.
- The scope question logged as decision 101512 stands and is now better quantified.

## 7. Next Batch
-> see pipeline/designs/exp_design_20260916-1102.md
Status: DIAGNOSTIC COMPLETE / EARLIER INFERENCE CORRECTED / NOT ADMITTED.
