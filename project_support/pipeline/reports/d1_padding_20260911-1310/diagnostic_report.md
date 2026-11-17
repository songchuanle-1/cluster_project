# D1 Real-Projection Padding Audit

## Scope
Frozen 21 IDs/11 scenes per checkpoint, 12 outcome-selected M95 errors and
9 controls; 3 missing controls retained. Both captures complete in 14
original language groups. Context descriptions are not scored samples.
These strata are not causal matches or population prevalence estimates.
Historical baseline identity remains unverified. No reserved-scene inference.

## Source And Derivation
Current source loss_sem_align retains all five maps, fractional annotation
weights, modifier/pronoun/relation terms and ordered token-weight overwrites.
Saved temperature/eos used. Source matching replay on captured FPS/sample
indices equals earlier assignment for all42; per-description normalizer M.
S=V T^T/tau; O indicates other entities; b_q is main-map activity;
w_q is source match weight. All annotation padding support is zero.
A_q=LSE_all((1+O)S); C_q=LSE_valid((1+O)S).
Unchanged positive terms and token-to-query terms cancel, hence
DeltaL=sum_q w_q*b_q*(A_q-C_q)/(2M).
For padding j, dL/dS_qj=w_q*b_q*softmax((1+O)S)_qj/(2M).
The full source AST supplies all other gradients; the separate logit-input
AST gives gV=gS*T/tau and gT=gS^T*V/tau. Autograd/identity checks pass.
These are gradients of detached normalized projection tensors, not the
normalization Jacobian, shared network parameters or training trajectory.
Stored projections originate in float32; source criterion is audited with
float64 projected tensors and source-created map/weight dtypes unchanged.
This validates algebra at the captured values, not bitwise production
float32 loss/gradient execution. All42 cases contain padding; no natural
unpadded control was observed. Earlier synthetic controls cover that case.

## Results
|Model|N|Padded|Mean padding mass|Mean weighted mass|Mean loss delta|Mean query-gradient change/full|Mean padded/full token-gradient norm|
|---|---|---|---|---|---|---|---|
|baseline|21|21|1.92318208e-05|5.03978004e-05|8.83026839e-05|0.000221044188|9.20206685e-05|
|m95|21|21|1.27469302e-05|3.4925523e-05|6.53158574e-05|0.000153642464|5.7721147e-05|

verification.json includes all/error/control count, mean, median, min/max;
padding.json includes per-ID numerators and denominators. No confidence
interval or statistical error-vs-control conclusion for this selected set.

## Recapture Discrepancy
Original audit halted at mask-logit drift 7.2479248e-5. Reporting-only
repair1 retained atol=rtol=1e-5, recorded every comparison, and rejected
linked claims where any comparison failed. No threshold relaxation.
- baseline: prior-bank linked claims accepted 6/21; binary/index/IoU identical 21/21/21 of21; max mask/score logit drift 9.91821289e-05/5.00679016e-06.
- m95: prior-bank linked claims accepted 4/21; binary/index/IoU identical 21/21/21 of21; max mask/score logit drift 0.000183105469/6.19888306e-06.
Current-capture internal criterion evidence is separate from prior-bank
equivalence. Exact indices/GT mapping pass; drift cause remains unknown.

## Decision And Limits
Measured projected-gradient changes are small in this selected evaluation
sample. Do not prioritize padding correction as the main research mechanism
on this evidence; do not claim zero exposure, training harmlessness or harm.
No model correction, training enqueue, causal efficacy or novelty claim.
Ordinary mask correctness is not an independent core contribution.
Evaluation dropout/augmentation/batch normalizers differ from training.
Both original GPU captures exited0; CPU reporting repair1 exited0.
Runtime/memory reflect shared load and are not the required efficiency benchmark.

## Next Evidence
Return to the concrete candidate-scoring problem: most recoverable errors
retain usable supervised positives. Next quantify discriminator margins
and gradient directions for selected false candidates versus usable positives
on existing banks, with all successes as controls and scene-level uncertainty.
No automatic new auxiliary loss, selector or pooling descendant. A proposed
mechanism still needs a falsifiable objective/derivation, primary-literature
comparison, matched intervention and resource admission before training.
