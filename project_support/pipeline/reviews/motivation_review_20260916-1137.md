# Motivation Review - Readout Axis Closed By A Nonlinear Test
2026-09-16 11:37 Asia/Shanghai. Feasibility measurement; nothing admitted.

## 1. Goal
pipeline/goal.json authoritative: 14 constraints, 11 bans, target mIoU >= .51.
Ledger champion M95 .5020; exact .5024607181549072@16; Phase 1 NOT YET.

## 2. Why
The previous review established causality: restricting selection to the native
training-positive set yields +17.9 pp (22 fixed, 0 broken), while restricting to
"seed inside any instance" is exactly null. The remaining question for mechanism
choice is whether the referent identity needed by that decision is *present in the
query features* the head reads. Earlier probes were linear, which is too weak a basis
for closing a whole axis, so this reruns the question with a nonlinear head.

## 3. Method
Frozen M95 checkpoint, one same-forward capture, 16 batches / 123 expressions / 32
scenes. Per query the feature is the head's own input plus what the architecture
computes but discards: final decoder query embedding (256), query position relative
to the scene centroid (3), predicted-mask centroid offset (1x3), normalised mask size
(1), max mask logit (1). GT is used only to form labels, never as a feature.

A 264-256-64-1 ReLU MLP is trained per fold and evaluated on held-out SCENES, 5-fold
scene-grouped cross-validation, so the probe cannot memorise a scene. Two labels:
`accept` (the query's own mask reaches IoU>0.5 with the target) and `positive` (the
query's sampled seed carries the target instance id).

## 4. Result
| Label | probe selects acceptable | deployed indis selects acceptable | probe top-1 matches label | deployed top-1 matches label |
|---|---|---|---|---|
| accept | 59.3% | **69.1%** | 59.3% | 69.1% |
| positive | 62.6% | **68.3%** | 65.0% | 69.1% |

The nonlinear scene-held-out head does *not* beat the deployed head on either label,
and its ceiling (59-65%) is far below the 87.0% that the oracle positive restriction
achieves.

## 5. Interpretation
This closes the readout axis properly, not just for linear probes. Adding the position
and mask-geometry features the architecture computes but does not feed the head, and
using a nonlinear model with scene-held-out validation, still does not recover the
referent decision. On this frozen checkpoint the identifying information is not
available in the head's own input, so no change to *how* the existing decision is read
can fix it. The +17.9 pp oracle gap therefore requires a change to what the model
learns, not to how the score is decoded.

Combined with the prior ticks this also resolves an apparent tension: the 2D modality
is identity-richer than the fused 3D representation (top-5 81.8% vs 57.6%) yet not
language-addressable (all four alignment variants at chance). Consistent picture: the
identity exists upstream, is not carried into a language-conditioned per-query form,
and the head's input cannot reconstruct it.

## 6. Limitation Stated Before Use
The probe trains on 4/5 of scenes while the deployed head saw all 32 during training,
so the comparison is not perfectly matched and the deployed number is partly
memorisation on the test folds. That weakens any claim of the form "the probe proves
the features are insufficient". The defensible claim is narrower and still decisive
for planning: a scene-generalising readout over the head's own input does not come
close to the oracle ceiling, so readout engineering is not a credible route to the
measured +17.9 pp. The frozen-feature setting also cannot exclude that retraining
would move the features.

## 7. Consequence
Route status unchanged and now better supported:
- readout / rescoring / calibration / rerank: closed (linear and nonlinear, scene
  held-out; ceiling 59-65% vs oracle 87.0%);
- objectness-only mechanisms: closed by the exactly-null control;
- the indicated training change (make the referent decision about the object
  hypothesis) is RefMask3D/DETR prior art and remains unadmitted;
- no new admissible candidate exists, so the slots stay empty.

## 8. Next Batch
-> see pipeline/designs/exp_design_20260916-1137.md
Status: FEASIBILITY MEASURED / READOUT AXIS CLOSED / NO CANDIDATE ADMITTED.
