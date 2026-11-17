# Same-Capture Native Feature Diagnosis

Frozen native capture e4a7e63605bb60d9e9a543cd22ac2635a37627ee3db22d870122e1a254342e08
contains four unchanged M95 network forwards, TRAIN groups0/60/101/124 in
two batches and two repeats. No optimizer step. Analyze all records on CPU
with CUDA hidden, and report actual expressions/scenes/valid-point denominators.

For each distinct first-repeat batch strictly load its captured cluster module
state. Test CPU identity repeat and query-order reversal with the bank fixed;
report native-GPU versus CPU replay differences rather than changing precision
or thresholds to declare cross-device equivalence. Preserve all original FAILs.
Construct one diagnostic-only same-shape method clone: replace just the padded
point global mean with the valid-point mean, retaining original state, query,
bank, indices, tensor shapes and dtype. Measure valid-point message changes.
This tests mean-path sensitivity on real learned inputs, not task harm or a
proposed normalization-only successor. Do not inject the message difference
into the final decoder as though intervening through its intervening ILA layers.

Also describe the pairwise cosine of the three refined, composed-gather scale
messages, expression-balanced on valid points; this is descriptive redundancy,
not a causal proof, admission criterion, or new mechanism. Recompute the final
captured query/inst_feats inner product and report its CPU/GPU rounding error.
No validation selection, model modification, new sample, backward, training,
new novelty claim or gate promotion is authorized by this diagnostic.

The first analyzer stopped on scan_ids indexing: capture metadata and the
unchanged dataset collate_fn show scan_ids is per-scene while ann_ids and native
features are per-expression. Preserve the first source/attempt, and expand
each scan_id by its recorded scenes_len in a separate v2 analyzer. Assert the
expanded count equals ann_ids and feature batch size before running controls.
This fixes the denominator mapping only; no numerical test or model changes.
