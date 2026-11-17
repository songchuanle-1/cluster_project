# Same-Prefix Native Suffix Controls

The first full-forward paired test completed12forwards but pair0 full-mask
repeat max differences are large(4.09/30.63/31.03), despite stable selected
queries/loss. Preserve it as inconclusive for all-query alignment; do not claim
a unique cause such as query permutation without identifiers/evidence.

For each SAME two frozen TRAIN batches, execute ONE unchanged native forward
and capture exact last-encoder inputs, last-decoder inputs, raw cluster bank,
query identities and all original Criterion arguments/output including labels,
sample indices, prior auxiliary outputs and unchanged CSORT. Freeze these
same-forward tensors and the bank. Re-execute the original last encoder,
decoder and Criterion for M95/uniform/content twice, replacing ONLY the point
readout. Assert replay encoder inst input equals the frozen cluster inst input;
all last-decoder query/sample metadata and earlier auxiliary outputs stay fixed.
This propagates interventions through the real ILA/mask/loss path without
resampling the upstream query bank. Report original-vs-replay and replay repeat
differences under the original1e-6 boundary; failures remain failures.

After this paired diagnostic, one content-condition native SUFFIX backward may
measure finite nonzero loss gradient into the cluster message and existing CTF
parameters. Prefix/bank are frozen, so it is explicitly NOT a full new-model
native backward gate. No new trainable tensor, optimization, training admission,
production edit, precision change or population performance claim. Preserve the
4new and12old strict float32 failures regardless of this test's result.

Use same GPU1 idleness/identity/flock/deadline/0.25allocator guards. If the
suffix's current in-place implementation fails autograd or resources, preserve
the exact failure and preregister at most one causal local realization repair;
do not relabel the whole hierarchy hypothesis rejected.
