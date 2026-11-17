# M95 Cluster Token Scatter Localization

## Identity and scope

On authorized server-6 GPU7 (0% / 0 MiB before each run), key-based SSH
recovered the read-only M95 checkpoint from the original SCM admission
staging path. Its full SHA256 is
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`.
Frozen manifest and config passed their embedded hashes. The trained M95
model source passed its package hash guard. An isolated diagnostic bundle
contained the current manifest helper after the historical bundle's older
helper failed at import time; no failed attempt executed a model forward.
The diagnostic script was extended only with pre-hooks and reversible
scatter substitutions, not model source edits.

Rows 83 and 174 each used one transformed TRAIN item, four repeats per
arm under the native loss path and fixed seed 1999. The transformed item
hashes differ from their frozen full-scan native-input hashes. Therefore
these tests do not reproduce or explain the historical row-83 mask flip.

## Matched interventions

With only network coordinate scatter on CPU, each item's coordinate
hash stabilizes but raw 3D features remain variable. With all network
scatter on CPU, raw/fused features and final-layer point/query inputs
stabilize. Yet all three cluster-token scales, cluster message, `ila`
query input, and final encoder output still have four distinct hashes.
The `ila` source input has one hash. This pattern holds independently for
both items.

Replaying the first cluster message makes both `ila` inputs and final
encoder output byte-stable. Replaying the first three per-scale token
tensors stabilizes the cluster message and final output. Finally, moving
the shared cluster bank's `scatter_mean` reduction to CPU stabilizes all
three token tensors, message and final encoder output in all four repeats
for both items. The matched intervention localizes this fixed-item
repeatability path to cluster-token aggregation. It does not establish a
general trained task benefit, a novel mechanism, or historical full-scan
causality. Selected query and implicated query mask are invariant across
all arms/repeats of both transformed items.

Receipts (SHA256):

- `pipeline/reports/m95_cluster_cpu_trace_row83_20260926-0412.json`
  `367c946e5e6ef66aabfcba1f6829454f21fe04e237cd015653b492a911f75d04`
- `pipeline/reports/m95_cluster_cpu_trace_row174_20260926-0412.json`
  `6989c4b5e5c186c6de7f44c9f6280c7a77f24a58b3836f50c3d6f52edc647fff`
- `scripts/m95_fixed_batch_scatter_forward_20260926.py`
  `9a585748c73bb4b538496fdc734ace9d86876b0791d8b828dfcf9715b6ac4479`

The row-83 and row-174 receipts each passed checks for checkpoint
identity, 24 rows in six four-repeat arms, different frozen item hash,
and fixed-token stability. Python compilation passed.

## Gate and next action

The unchanged full-scan strict comparator still fails 26/65 paired rows;
the two selected masks and queries did not change in this control. No
new model has diagnosis, matched mechanism control, native backward,
resources, independence and goal constraints passed together. Zero of
two queue slots are admitted.

An item-only attempt using `scripts/m95_frozen_item_replay_20260926.py`
first traversed only 128 manifest-subset batches, so the recorded full-scan
steps 2751/3137 were not reached. A corrected full-loader pass with model
initialization but no model forward was still CPU-heavy after 23 minutes;
an exact-PID TERM stopped it. A target-only hashing retry was likewise
stopped by exact PID near the tick deadline, with no completed target
receipt. Neither attempt binds the historical item. Do not infer hash
equality from the absence of a result.

Next, reproduce the original full-scan dataloader order with progress
receipts and fingerprint the target items at steps 2751/3137, without a
model forward but with the same trained model initialization before
shuffling. Optimize the item-only pass while preserving transform RNG;
verify an early control position before the target steps. Require
exact `native_input_sha256` equality before any historical attribution.
If bound, run a matched fixed-item CPU-cluster-bank versus native
intervention with the unchanged strict comparator and a pre-registered
task-relevant readout. Do not propose a pooling/selector variant or relax
the historical tolerance merely to make the comparator pass. If exact
binding is not reproducible, persist the observed mismatch and keep
historical causal attribution blocked.
