# D1 Candidate Assignment And Discrimination Audit

Protocol frozen 2026-09-11 11:18:00 Asia/Shanghai, before CPU replay.
Upstream review/design: 20260911-111300. Diagnostic, not a training experiment.

## Evidence And Scope
All 284 frozen diagnostic descriptions x baseline/M95 = 568 banks,
71 physical scenes, four descriptions per scene. No missing IDs, target
majority centroids, raw-superpoint joins or GT joins. No new inference.
Manifest SHA:84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468.
Assignment SHA:9442824e45979fa3891895a90edf7b993d666463773a72dd3e9fbd6b73c8aadd.
Protocol SHA:829ed87641dacd987a150fc56b4c82b876d8536704e3cf45171d361a5cf0c253.

Extracted actual source AST methods: dataset `get_sp_label`; each model's
`match_sampled_ins`, `_get_src_permutation_idx`, `loss_indi`. Package loss and
network hashes match checkpoint identity audits; source/data/summary/bank
hashes checked before use. No imports or changes to active model packages.
Current dataset labels independently checked against integer vote counts.

This is current CPU assignment applied to saved **evaluation** candidates.
It is NOT a replay of augmented training, historical targets or gradients
through the full network. Saved FPS/sample indices avoid recomputing FPS.
Raw coordinates are reduced to float32 superpoint centroids as in source.
Historical forward/code identity remains unproven, especially for baseline.

## Formula And Source Semantics
For superpoint s, assign c_s to the instance with strictly more than half of
its points. Otherwise c_s=199. Negative/ignored instance IDs can be majority
labels too. Each description here has one target ID c.

1. Gather query superpoint s_q = fps_seed_sp[sample_inds[q]], position x_q
   and label c_q.
2. Let mu be the unweighted mean of centroids of superpoints labelled c.
   This is not the point-weighted target center.
3. Select q0 = argmin_q ||x_q-mu||_2 using source torch.cdist/topk.
4. Set y_q=1 iff c_q=c or q=q0. Deduplicate nearest/target membership.
5. Let p_q=softmax(z_q)[1], M=sum_q y_q, w_q=1 for positives and .1 otherwise.
   Both saved configurations use the default eos_coef=.1.
6. Up to the implementation's tiny constant entropy term:

       L_indi = (1/M) sum_q w_q [
         -y_q log p_q - (1-y_q)log(1-p_q) + log(1+1e-6)]
       dL_indi/dz_q1 = w_q (p_q-y_q)/M
       dL_indi/dz_q0 = -w_q (p_q-y_q)/M

The formula is for one-description replay. Production divides the summed
batch loss by total matched instances across descriptions (and applies
distributed reduction when active). This changes magnitude, not sign.
Saved final-layer loss_weight[4]=.1; auxiliary layers reuse matching and use
their configured layer weights. Finite-precision entropy constant is
independent of logits; no derivative contribution.

Negative-label candidates receive a nonnegative derivative on positive logit,
even if the final mask is good. Positive labels receive a nonpositive derivative,
even for poor masks. These are **partial logit derivatives**, not a claim that
a full optimizer step must move a shared-network candidate in that direction.
Mask BCE/Dice and semantic alignment also supervise matched queries; sampler
and auxiliary losses also act. Current data do not isolate their causal effects.

`loss_masks` learns a separate quality score only for matched masks whose
superpoint IoU>.5. Inference selects softmax(`indis`)[:,1].argmax, not that
quality score. Bank field `score_logits` contains `indis`, NOT `scores`.
No claim that the discriminator was intended to estimate point IoU.

## Results
Usable means point-mask IoU>.5 using the existing threshold and union+1e-6.
Candidate counts are correlated within descriptions/scenes, not independent
statistical observations.

| Candidate-level category | Baseline /36352 | M95 /36352 |
|---|---:|---:|
| Positive and usable |2101|2113|
| Negative and usable |9096|5721|
| Positive and unusable |223|189|
| Negative and unusable |24932|28329|

| Description-level category | Baseline /284 | M95 /284 |
|---|---:|---:|
| At least one usable negative candidate |248|259|
| Usable bank but no usable positive candidate |6|12|
| Recoverable selection failure |90|111|
| Recoverable, with usable positive candidate |84|99|
| Recoverable, without usable positive candidate |6|12|
| Selected candidate positive |174|161|
| Positive selected candidate fails IoU>.5 |9|9|
| Negative selected candidate succeeds IoU>.5 |6|6|
| Recoverable and selected candidate positive |5|6|
| Nearest seed outside target |34|35|

Thus 84/90 baseline and 99/111 M95 recoverable failures already contain usable
positive candidates. The absence of such candidates accounts for only 6/90 and
12/111 in this conditional replay. It cannot be called the dominant explanation.
Most recoverable selected candidates are negative (85/90,105/111); that is a
description of score ordering, not proof of why training produced that ordering.
M95 has fewer usable negative candidates overall but more descriptions with at
least one: counts and per-description incidence answer different questions.

GT-restricted positive-bank oracle mean: baseline .809144576, M95 .817176301;
unrestricted oracle .834245822/.848107879. Restriction still leaves substantial
headroom above selected .535914148/.502216606. This is not a deployable selector.

Paired physical-scene bootstrap, 10000 resamples, seed1999, descriptive95%
intervals for M95-minus-baseline (denominator284, equal-scene weighting):
- Any usable negative incidence: +.0387324 [+.0035211,+.0739437].
- No usable positive incidence: +.0211268 [-.0105634,+.0528169].
- Recoverable with usable positive: +.0528169 [+.0070423,+.1021127].
- Positive-restricted oracle mean: +.0080317 [-.0101902,+.0268952].
All estimates and both model intervals are in verification.json. These are
exploratory conditional intervals, not untouched-test evidence or p-values.

## Correctness And Resources
Eight synthetic cases per model source, all pass: majority/tie/ignored labels,
nearest outside target, deduplication, permutation, analytic CE gradient,
finite difference and usable-negative/poor-positive counterexample.
All568 records independently checked locally for assignment, four-way
contingency, oracle/index, selected label, flags and gradient signs.
Max autograd-vs-formula error: baseline2.9802322387695312e-8,
M955.960464477539063e-8; float32 atol1e-7/rtol1e-5.

Three nearest indices differ between source float32 cdist and direct float64
distance: baseline/M95 scene0328_00 object6 ann47, and M95 scene0553_00 object8
ann11. Additional float32/float64 full centroid reductions were checked. All
alternative indices were already target-positive: all three positive sets and
usable-positive counts remain unchanged. This bounded sensitivity check does
not certify historical GPU arithmetic. See rounding_check.json.

Initial synthetic run failed because harness used float64 while source labels
are float32. Repair1 used source-compatible float32, preserved model/source and
original failure logs; retry exited0. Bugfix111900. No training crash or restart.
CPU worker22.2948404653s, peak RSS623.36328125MiB, CUDA uninitialized.
One CPU thread; no GPU/production efficiency claim. Storage remains QxS banks,
raw point mapping O(N); no NxN attention or newly materialized QxN mask bank.
Helpers/protocol/review/design synced and hash-verified on bothservers under
/tmp/cluster_d1_assignment_20260911_1113; only server-4 ran CPU audit.

## Decision And Next Evidence
Do not equate seed assignment with final-mask correctness. Also reject the
stronger claim that missing positive usable candidates explains most failures.
Neither observation proves a bug, motivates label replacement automatically,
or establishes a new mechanism.

Next diagnostic: inspect score ordering and available semantic-alignment
supervision for existing candidates, with fixed positive-usable and negative
controls. Separate low target scores from confidently competing seeds and
separate shared-network gradient effects from target definitions. Do not
rebrand a scalar rescore, quality loss or known matching scheme as novelty.
No new mechanism admitted, no training/config change, no queue refill.

Core novelty/primary-paper comparison, causal matched intervention, robust
generalization and bs1 warmup20 repeat100 efficiency are NOT completed by this
audit. Reserved scenes remain unused and are only prospectively reserved;
the validation set was historically mined. No new dataset or annotation API.
