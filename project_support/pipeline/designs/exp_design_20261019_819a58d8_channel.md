# Experiment Design - cluster_project

## 1. Motivation
Authoritative goal description: cluster research on ScanRefer must return to
hierarchical point/superpoint inst_feats updates that participate with query in
mask prediction; existing hierarchy, inactive routing and supervision-only
changes are not a new mainline contribution. Full original Chinese description
and constraints are preserved in the linked frozen goal, not rewritten here.
This document synthesizes already-preregistered diagnostic executions; it is
NOT a retroactively frozen protocol or a new architecture admission.

## 2. Current Best Results
| Experiment | State | Best mIoU | Acc50 | spmIoU | Epochs |
| --- | --- | --- | --- | --- | --- |
| Historical M95 | Cached comparator | .5020 | UNKNOWN here | UNKNOWN here | Historical |
| model_base1 | Cached baseline | .4894 | UNKNOWN here | UNKNOWN here | Historical |
| Current diagnostic | No training/VAL | UNKNOWN efficacy | UNKNOWN | UNKNOWN |0optimizer steps |

## 3. Analysis And Direction
Existing source rank<=2 is conditional on prefix/assignments; encoder, decoder
and trainable parameters offer other paths. Coherent perturbations show those
two channels can strongly affect masks/loss, so dimensionality alone does not
justify adding full-channel attention. Single-point unresolved loss is not a
proof of task inactivity. Original native null1e-6 failure is retained.

## 4. Experiment Plan
| Protocol | Stable ID | Purpose | Actual scope | Status |
| --- | --- | --- | --- | --- |
| Failure capture | hierarchical-nonlocal-channel-rank-audit | Measure original failing readout amplitude | Same frozen prefix;4source calls | Strict gate FALSE; saved |
| Single-point task suffix | Same ID | Reach actual mask/criterion |1native forward/backward,24readouts | Recorded |
| Coherent field | Same ID | Inspect group/global response |1native forward/backward,24readouts | Recorded; not exact across-process pairing |
| Shared-prefix paired scopes | Same ID | Correct independent-prefix confound |1native forward/backward,144conditions | Recorded |
| Actual matching observation | Same ID | Verify mask targets/indices/num_boxes |1native forward/backward,144conditions | Identical matching observed |
| Sender/receiver2x2 | Same ID | Separate the coupled scope factors |1native forward/backward,288conditions | Identical matching observed |
Preregistrations and exact source/manifests/results are in tick_819a58d8. Keep
all negative results and measured identity drift. No population CI from2scenes.

## 5. GPU Allocation Plan
| Server | Physical GPU | Assignment | Constraint |
| --- | --- | --- | --- |
| server-4 |0 | Sequential bounded diagnostics only | Pinned hostname/UUID, fresh idle checks,3lifetime flocks |
| server-3 |1 | Not used | Foreign occupation observed02:12Shanghai; later state UNKNOWN |
server4GPU1 and server6 remain unauthorized. No sharing, eviction or lock deletion.

## 6. Implementation Checklist
- [x] Preserve original checkpoint/config/source, native flags and fixedTRAINsamples.
- [x] Preregister matched source, suffix, native backward and matching observations.
- [x] Separate sender and receiver factors; persist all partial/failed evidence.
- [x] Count actual invocations; do not count cached work as current output.
- [ ] New independent model/config, resource admission, commit and gated launch:
  NOT proposed/authorized by this diagnosis; none performed.
No optimizer/scheduler, dataset/schedule/goal edits or production-source changes.

## 7. Risk Assessment
No trained performance result exists. Different processes have different numeric
prefixes; only within-prefix comparisons support the paired scope interpretation.
Actual criterion mask matching is fixed in the final controls, but the cause
of tiny arithmetic drift remains UNKNOWN. Sender scopes have different total
energy; only null/row are norm-matched within mode. Own-coarse is an activity
control and its sender factor is a duplicate, not an independent observation.
No discarded failed gate, new tolerance, invented phase/resource hold or claim
that one finite diagnosis exhausts all possible research routes is allowed.

## 8. Smell Check
No variant or parameter search. All changes are diagnostic hooks/AST observation
inside temporary processes; production forward/loss unchanged. This does not
give novelty or admission. Historical rejected identities/purity/BCCA are not
reopened; gate/residual/routing successors and unauthorized revisions remain banned.

Status: IMPLEMENTED (finite diagnostics only; no model/config/admission).
