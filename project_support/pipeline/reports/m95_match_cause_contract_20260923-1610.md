# M95 Native Matcher-Cause Diagnostic Contract

2026-09-23 16:10 Asia/Shanghai. Event-mode continuation of three due
diagnosis IDs. CPU-only source audit and synthetic tests; no model execution.

## Source And Scope

- Native criterion `loss.py`, lines 350-387 and 483-532: query positions are
  `seed_pos[b][sample_inds[b]]`, where seed positions gather native
  `sp_coords_float` by `fps_seed_sp`. GT centroids are computed from masked
  native superpoint coordinates. For each GT, `match_sampled_ins` adds one
  nearest query, then instance-member queries excluding *all* nearest indices.
- `native_manifest_capture_20260922.py` lines 310-317 and 391-415 saves
  positive query indices, sampled seed indices and FPS superpoint IDs, but
  does not save `sampled_pos`, `obj_pos`, per-GT nearest indices or membership
  groups. The hierarchy positions have a separate producer and cannot fill
  these missing fields.
- A new read-only checker verifies a separately captured row's native query
  and GT axes, nearest-distance consistency (including ties), exclusion of
  global nearest queries from membership, and equality to native positives.
  Five synthetic cases pass. This is a contract test, not observed M95
  matcher-cause evidence.

## Bounded Native Follow-Up

When server-6 GPU7 is available and host/runtime/data/occupancy checks pass,
instrument the *existing* criterion call on the fixed M95 checkpoint, seed
1999 and frozen TRAIN manifest. Bind each row to manifest scene/annotation ID,
checkpoint and source hashes, query index, native sampled position and
instance label, ordered GT object ID and centroid, nearest query per GT,
post-exclusion membership per GT, and positive vector. Assert the captured
outputs match the unmodified native matcher. Preserve the 256-expression
denominator and 40 outcome-selected failures; report missing rows and
scene-level strata separately. Never mix hierarchy FPS coordinates with
criterion coordinates. Do not infer population benefit from this subset.

For the six positive-outside-target-seed discordant classes, classify the
native matcher cause only after this binding. Reconcile seed labels and
same-class peers; report ties and dual causes. If a positive label is explained
by nearest-GT assignment, that is not by itself evidence of label error.
Independently capture query states for the four same-physical-ID classes,
matching exact seed indices/coordinates where possible, before considering
representation collapse. The supervision axis still needs an expression-level
causal unit and matched native-positive, objectness and listwise controls.

## Disposition

All three IDs remain `diagnosis`. No implementation of a new mechanism,
native backward, resource measurement, independence result, admission,
deployment, queue entry or training progress. GPU7 observation: 42,025 MiB
used, 39,055 MiB free, one 41,996 MiB foreign compute process; no process
was touched. Empty capacity is scientifically justified for both slots.
