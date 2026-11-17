# Actual Source-Loss Head Audit
2026-09-13 foreground continuation. Diagnostic completed, no training admitted.

## Question And Protocol
Can other candidates reverse a correcting wrong-versus-usable-positive pair
update through the shared final classifier? The pre-execution review embeds
the complete goal contract; protocol.json preserves its hash, the original
design hash, source hashes,284 IDs, manifest, raw-input hashes and checkpoint.
All284 artifacts/71 scenes verified. This is the September12 semantic capture,
not the older bank with111 recoverables/158 successes.

Actual source matching is target-instance seed membership union nearest query.
Labels were recomputed from raw superpoint majorities and this capture's query
indices. Native float32 source CE gradients and loss were compared with a
double-precision smooth extension; native-gradient VJP signs also agree.
Selected query is the original deployed index; h is highest-scored usable
positive. IoU>.5 is fixed; no threshold tuning.

## Results
| Population | Banks | Informative pair | No usable positive | Zero pair | Pair correcting | Head correcting | Head worsening | Rest-bank reversal |
|------------|-------|------------------|--------------------|-----------|-----------------|-----------------|----------------|--------------------|
| All | 284 | 101 | 43 | 140 | 96 | 95 | 6 | 1 |
| Recoverable failure | 109 | 96 | 13 | 0 | 91 | 91 | 5 | 0 |
| Success | 145 | 5 | 0 | 140 | 5 | 4 | 1 | 1 |
The remaining30 banks have no acceptable mask. All96 informative recoverable
pairs have corrective independent-logit velocity;91 remain corrective in
shared-head parameter space. Those91 span51 scenes; all96 span54 scenes.
The five adverse cases occur in five distinct scenes. No population confidence
claim follows from this exploratory, reused validation bank.

Decision: 0/91 correcting failure pairs are reversed by the rest of the bank.
Reject that specific mechanism as an explanation of THESE observed failures.
The one success-control reversal prevents a broader claim of no interference
anywhere. A protective gradient projection is not justified as a new method.

## Pair Geometry
Post-result descriptive follow-up, not a new preregistered hypothesis test.
Let Jq=grad_phi(dq), Kij=Ji dot Jj and cq=wq(sigmoid(dq)-yq)/P.
Then the pair contribution is exactly:

    v_pair = -cs(Kss-Ksh) - ch(Ksh-Khh)

For all five adverse recoverables, both labels are positive and
Kss>Ksh>Khh. Therefore cs,ch<0 and BOTH terms increase the wrong-minus-good
margin. Independent logits omit these cross-parameter responses.
This is an algebraic explanation of a local frozen-head derivative, not
evidence of an end-to-end training bottleneck or a novel remedy.

| Scene/object/annotation | Selected IoU | Usable-positive IoU | v_pair | v_head |
|-------------------------|-------------|---------------------|--------|--------|
| scene0222_00/0/75 | .500000 | .507576 | .185506 | .667610 |
| scene0251_00/16/24 | .420455 | .701149 | .031383 | .363750 |
| scene0256_00/0/2 | .486301 | .506849 | .005963 | .341360 |
| scene0689_00/0/58 | .500000 | .643678 | .078056 | 1.201020 |
| scene0693_00/19/3 | .416667 | .565217 | .338501 | 1.134102 |
Values exclude positive outer loss weight .1, which preserves signs.
Two selected IoUs are exactly.5 and one usable positive is only.506849;
do not describe these uniformly as severe wrong-instance errors.
Seven informative recoverables have a positive selected query:5 worsen,2
improve. All89 with a negative selected query improve under this head-only CE.
The13 missing usable-positive cases remain explicit, not imputed zeros.

## Verification And Limits
- First run passed; one CPU thread,19.23s, peak RSS1385.65MiB, CUDA not initialized.
- Eight assignment/source checks and four synthetic projection checks passed.
- All eligible rows checked decomposition, permutation, zero pair and projection.
- Centered differences at1e-4/1e-5:0 flagged informative rows.
- Max gradient error6.87e-8; loss-value error1.11e-6 after target-entropy constant.
- Max decomposition error1.14e-13; native32-vs-double velocity error3.04e-5,
  with no informative sign disagreement.
- Reconstructed selection logits max error.002448, within preregistered .03.
- One stored/deployed-vs-reconstructed selector discrepancy:
  scene0081_00/8/8, index81 vs53; oracle IoU.391304, no usable positive.
  Excluded from informative pairs by the predefined rule, not removed from284.
- Mask threshold comparison flips0; selected/oracle IoUs exactly reproduce
  every original summary row. FP16 full-mask preservation is not claimed.
- Source dtype is float32; head derivatives use double on FP16-captured queries.
- Eval capture, final independent head only, per-bank normalization, Euclidean
  gradient. Excludes upstream decoder, auxiliary objectives, real augmented
  training batches, Adam moments, weight decay and historical trajectories.
- Local code repo remains clean. Diagnostic protected queue/ledger/goal/server
  hashes unchanged before later, separately logged M191 terminal closure.
- Remote code diff unchanged; checkpoint hash verified before/after.
- CPU helper deployment only; no training model/config sync.

## Primary-Source Check
Original PDFs downloaded from arxiv.org and read locally, not abstract-only:
1. Tianhe Yu et al., Gradient Surgery for Multi-Task Learning,
   arXiv2001.06782v4,2020. Section2.3 and Algorithm1, pp3-4:
   projects each conflicting task gradient against another task gradient.
   Our margin normal is not a task gradient by definition, and a single
   constraint is not the whole PCGrad algorithm; projection itself is not new.
2. David Lopez-Paz and Marc'Aurelio Ranzato, Gradient Episodic Memory for
   Continual Learning, arXiv1706.08840v6,2022 revision of the2017 work.
   Section3, Eq7-8, p4: nearest Euclidean gradient satisfying linear
   non-interference inequalities. Our one-margin halfspace projection is a
   standard single-constraint instance of this optimization geometry.
PDF hashes:
pcgrad:4b960b81a001f376e8cb551c61c5578129dd99a9d1ff147be5ea56b9e578cbdf
gem:ddbc9c87d310b092b8621d47aeae1f97f4f664fd061e2406e944d0f9921cbb37
No claim of exhaustive novelty clearance. Oracle h is diagnostic only.

## Next Scientific Gate
Do not build a selector, loss-weight variant or gradient-projection successor.
The majority91 cases already receive corrective final-head CE signal.
Next prerequisite is a separately preregistered training-state replay that
compares actual total-loss/optimizer margin response with this head-only null,
using existing train data, frozen checkpoints and bounded resources.
First establish which optimizer state, batch/augmentation identities and
intermediate activations can actually be reconstructed. Do not call an
eval-state derivative a historical training replay. New mechanism admission
still needs a specific causal discrepancy, derivation, verified prior-art
difference, matched controls and efficiency. That gate is not yet met.
