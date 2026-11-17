# D1 Discriminator Margin And Gradient Audit

## Scope
All frozen284IDs/71physicalscenes permodel,568records,0missing. Uses the
original expansion banks, source-assignment gradients and ordering JSON;
no recapture, training or reserved-scene inference. Successes and bank
failures are explicit controls. Historically mined validation remains
exploratory; equal-scene samples do not estimate description-population rates.
Baseline historical forward identity remains unresolved.

## Derivation
For candidate q, z_q=(z0,z1), d_q=z1-z0, p_q=sigmoid(d_q), source label y_q,
weight w_q=1 if positive else0.1, M=sum y. Source loss is weighted binary
cross entropy plus its constant target entropy term. Its derivative is

    g_q = dL/dz1_q = w_q*(p_q-y_q)/M; dL/dz0_q = -g_q.
    dot(d_q) = -2*g_q.
    m = d_s-d_h; dot(m) = -2*(g_s-g_h).

The factor2 arises from updating both logits independently. h is fixed
at the highest-score member of G={IoU>.5} or H=G intersect{y=1}.
The GT-restricted choice is diagnostic, not a deployable selector.
Empty G/H is missing, not margin0. Identical s=h has velocity0.
Multiplying by positive batch/final-loss normalization rescales directions.

For selected-negative/eligible-positive, dot(m)<0 at finite nonsaturated
probabilities. Selected-positive/eligible-negative gives dot(m)>0.
Same-label pairs with m>=0 give dot(m)<=0, but contraction is NOT sufficient
to reverse their ranking under identical independent scalar dynamics.
For two positives, each solves d+exp(d)=2t/M+constant; the left side is
strictly increasing, so initial ordering is preserved for finite t.
For negatives, d-exp(-d)=-2eos*t/M+constant yields the same preservation.
Thus even the idealized flow cannot generally rank different-IoU positives.

Crucially, z=z(theta) implies dot(z)=-J*J^T*grad_z(L), J=dz/dtheta,
for plain parameter gradient flow on this loss only. Actual network Jacobian,
other losses, Adam, dropout and augmentation are not in this audit.
Current source labels represent seed identity, not desired mask-IoU ordering.
No claim that useful-negative labels are necessarily bugs.

## Results
| Model | Recoverable | H exists | H margin decreases | Selected negative with H | H absent |
|---|---|---|---|---|---|
|baseline|90|84|84|79|6|
|M95|111|99|99|97|12|

The remaining5baseline/2M95 recoverables with H have selected-positive
candidates. Their independent same-label margins contract but need not invert.
For best G, the margin increases in1/90baseline and4/111M95 recoverables;
these have selected-positive/eligible-negative labels. Other G margins
decrease89/90 and107/111. All per-ID probabilities, labels, margins, source
gradient errors and normalizers are in margin.json.

| Metric on recoverable H-eligible cases | Baseline (84) | M95 (99) |
|---|---|---|
|Median selected-minus-H logit margin|1.3978782743|1.7225106359|
|Median selected probability|.9142332847|.9291060470|
|Median best-H probability|.6409408525|.6084012600|
|Median margin velocity per-description M|-.2366726852|-.2324570835|

These are different conditional populations; do not interpret their median
difference as a paired effect. Common H-eligible243IDs/71scenes have
equal-scene meanmargin .8270482327baseline/1.0225298463M95, delta+.1954816136,
95%pairedscene bootstrap CI[-.0776196413,.5006364671].
This does not establish generally larger M95 margins.

On all284IDs/71scenes, recoverable+H+selected-negative counts79baseline/97M95;
paired scene-weighted rate delta+.0633802817, CI[.0140845070,.1126760563].
Usable but H absent6/12;delta+.0211267606, CI[-.0105633803,.0563380282].
10000resamples,seed1999. Intervals are exploratory, conditional on this
fixed sample, not independent confirmation. A single deterministic RNG stream
advances across metrics; differences from prior bootstrap endpoints reflect
different draws, not changed source counts.

## Verification
All568 NumPy analytic gradients agree with archived source float32 autograd
at atol1e-7/rtol1e-5;maximum absolute error7.21263487824e-8.
Independent scalar readback of gradients/margins/velocities passes568.
Four synthetic label-pairs have maximum loss FD error1.30467858739e-11
and direction FD error2.16461293334e-11. Permutation, tie and saturation
controls pass. Existing data exercises missing G/H and identical candidates.
No production source loss rerun in this tick; reuse hash-verified prior source
gradients. New scalar helper omits only the constant entropy term because
only derivatives are checked; absolute source loss equality is not claimed.
CPU helper .2908139000seconds; no full-model efficiency claim.
First executions exit0; no repairs or new GPU worker.

## Research Decision
Do not add a ranking loss on the premise that most errors have no corrective
supervision. For97/111M95 recoverables the selected negative and an available
usable positive already have opposing score-level corrective signals.
This is evidence about objective-level direction, not evidence that the
trained representation is separable or that gradients reach useful parameters.
The label/quality mismatch is real for some candidates but does not establish
the dominant cause of this observed selection gap.

Next targeted question: does the shared discriminator head's actual parameter
gradient still contract selected-negative/usable-positive margins, and how much
does candidate-feature coupling change the independent-logit result? First
inspect the exact head computation graph and availability of its input features.
If feasible, freeze a bounded fixed-case head-feature/Jacobian audit with
success controls; account for shared head parameters and other active losses.
Do not generalize head-only results to the full model, or launch another
unconditional score-statistic sweep. No new mechanism is admitted yet:
primary novelty, derived mechanism, matched intervention, generalization
and <=10G full-model resource admission remain required before enqueue.
