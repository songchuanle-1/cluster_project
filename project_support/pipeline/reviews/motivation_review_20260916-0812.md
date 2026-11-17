# Motivation Review - Multi-Scale Cluster Evidence Necessity
2026-09-16 08:12 Asia/Shanghai. Diagnostic only; no training admitted.

## 1. Goal
pipeline/goal.json is authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact checkpoint .5024607181549072@16; Phase 1 NOT YET.
The description names three diagnostics before a core mechanism may be chosen:
candidate coverage/boundary, same-class discrimination and relation binding, and
multi-scale evidence duplication. The first two have run; the third had not been
measured at the decision level.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Multi-scale cluster context drives the deployed decision | REFUTED | zeroing the entire message leaves the selected query identical in 123/123 fixed TRAIN expressions | none |
| Coarse scales carry complementary non-duplicated evidence | REFUTED | cos(l1,l2)=.905, cos(l0,l1)=.764 over target superpoints; gate weight l2=.087, dominant in 0/123 | none |
| The deployed bottleneck is mask quality | REFUTED | 33/38 failures already contain a query with IoU>0.5; only 5 are mask-limited | none |
| The deployed bottleneck is referent-query selection | CONFIRMED | 33 recoverable failures, matched by 33 wrong-instance selections | mechanism not yet derived |

## 3. Experiment Assessment
Two independent forward-only interventions on the same fixed 16 TRAIN batches,
M95 checkpoint, identical FPS seeds and identical query support.

Whole-message intervention (existing report, re-aggregated):
- base mean selected IoU .60825, success 85/123
- repeat .60825, 85 (exact reproduction)
- zero .61054, 85 (message removed entirely; slightly higher)
- shift .59649, 84 (message content rolled by one point)
- selected query identical to base in 123/123 in every branch

Per-scale intervention (new this tick), dropping one scale inside the unchanged
learned gate:
| Scale dropped | mean selected IoU | success | winner changed |
|---|---|---|---|
| none | .60825 | 85 | - |
| l0 (256) | .60739 | 85 | 0/123 |
| l1 (64) | .60872 | 85 | 0/123 |
| l2 (8) | .60750 | 85 | 0/123 |

Learned gate and duplication:
- mean level weights .5163 / .3967 / .0870; dominant scale l0 in 116/123, l1 in
  7/123, l2 in 0/123.
- mean cosine between per-point scale messages over target superpoints:
  l0-l1 .764, l1-l2 .905, l0-l2 .705.

Cross-reference to the purity measurement (07:58): l1 already mixes instances for
89.0% of target superpoints and l2 for 100%. The two coarse tokens are therefore
scene-level mixtures, and they are also the two most correlated with each other.

## 4. Gap Analysis
Answered: multi-scale evidence duplication is real and severe, not marginal. The
scale axis is redundant by construction (coarse tokens are instance mixtures), the
per-point gate collapses onto the finest scale, and no scale -- nor the whole
message -- changes the deployed referent selection.

Consequences that close the axis:
- Any further change to pooling, selector, readback position, scale count,
  cross-scale decorrelation weight, or per-point scale gate cannot move the
  deployed decision. Those are the goal's explicit non-main-line families.
- CSORT optimises cosine between coarse and aggregated fine tokens, but the
  measured l1-l2 cosine is already .905 and dropping l1 or l2 changes nothing, so
  the champion margin on this axis cannot be attributed to decorrelation.
- The forward-only zero result also reframes the champion's +.0130 over baseline:
  it must be a training-time effect of the joint optimisation, not a deployed
  contribution of the cluster message. This is a limitation of the current
  evidence, not a claim that the cluster branch is useless.

The project's real bottleneck is now unambiguous and one level up: within this
same forward pass, 33 of 38 failures already contain a query whose mask exceeds
IoU 0.5 with the target, and sampling loses 0 of 117 covered targets. The network
produces the answer and then selects the wrong query.

## 5. Design Rationale
The next mechanism must attach to referent-query selection. It must not be a
re-ranked, re-scored, contrastively trained, or competition-based selection head
(closed), and it must not be an IoU-competition or semantic-projection variant.
The selection head currently consumes only the query embedding; a structurally
distinct mechanism has to change what evidence the selection decision is computed
from, and it must be compared against the whole computation in NS3D, InstAlign,
HCF-RES, JVGN and QueryInst-style selection prior art before admission.

## 6. Next Batch
-> see pipeline/designs/exp_design_20260916-0812.md
Status: DIAGNOSTIC COMPLETE / MULTI-SCALE AXIS CLOSED / TRAINING NOT ADMITTED.

## 7. Follow-up Evidence Added At 09:40 (same design lineage)
Two further measurements on the same fixed forward were appended to
exp_design_20260916-0812.md as sections 3.6 and 3.7 and logged as decisions
20260916-093202 (fix class) and 20260916-094007 (no existing scalar).

Correction recorded: "the selected query outscores the correct query in 33/33
failures" is an automatic consequence of the argmax and is NOT evidence. It must not
be cited. The non-trivial facts are the rank, the gap magnitude and the rarity of
ties.

New non-trivial facts over the 33 recoverable failures:
- The correct query ranks median 12 / 13 / 13 by indis, mask-score head and sampling
  language-point correlation, with top-1 rates 0% / 6.1% / 9.1% and mean ranks
  24.3 / 30.1 / 29.8. All three existing scalar scores fail the same way, so the
  missing signal is absent from every current scalar, not just from indis.
- The correct query's mask covers the target almost perfectly (best IoU mean .871 /
  median .933; target coverage .947), a median of 6 (mean 10.7) queries already
  exceed IoU 0.5, and the selected and correct masks are usually disjoint (median
  overlap 0 points).
- Errors are confident, not marginal: mean indis gap -0.409, median -0.379, only
  10/33 near-ties.

Consequence for the design: a rescoring or calibration fix is excluded; a candidate
must inject identifying evidence. The obvious scoring-unit repair (score predicted
regions rather than queries) is efficacy-likely but novelty-negative, because
region-level language scoring is the dominant 3D-RES paradigm
(InstanceRefer / M3DRef / 3DVG-Transformer). It may serve as a matched control, never
as the contribution, unless the derivation adds a mechanism a generic region score
does not already provide.
