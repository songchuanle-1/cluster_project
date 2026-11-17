# M95 Identity Query-State Capture Contract

2026-09-23 19:15 Asia/Shanghai. Event-mode CPU/static continuation.
No native execution, mechanism, efficacy, or admission result.

The exact M95 decoder's last layer returns `query` before
`indi_embedding(query)`, which supplies `pred["indis"]`. The opt-in
`--capture-identity-query` hook saves that query tensor in the existing
manifest-bound artifact and requires `--capture-match-causes`. It checks
batch/query axes, finite states, sampled FPS seed indices and physical
superpoint IDs, equality of recomputed indicator logits to native logits,
and equality of query count to criterion sampled positions. Existing output
without the flag retains its former semantics. The saved query vectors are
not a new model feature or intervention.

Eight synthetic identity-binding tests, four matcher-binding tests and six
existing manifest tests pass locally; Python compilation passes. PyTorch is
absent locally, so the score-head equality and hook have not been exercised
in native forward. Producer/test hashes must be verified on the authorized
host before an opt-in run; neither is deployed by this tick.

For manifest indices 11, 23, 79 and 253 (four failure-selected scenes),
extract each positive/negative exact-mask class with the same physical
seed instance ID. Preserve all query indices, not only one favorable pair.
Within each class report final query-state cosine distance and raw
indicator-score difference for all positive-negative pairs; split by
native nearest-GT versus member cause, sampled seed index, exact criterion
coordinate equality and coordinate distance. As a negative control,
compare distinct physical IDs in the same expression matched on coordinate
distance where support exists; report missing support, ties and scene
denominators. Do not use target labels or score outcomes to choose a pair.
The four classes have zero exact seed-index pairs in the prior static
report, so an exact-seed-index effect is unidentifiable there.

Reject a representation-collapse explanation for this subset if the
same-physical-ID discordant pairs have distinguishable final query states,
or if any apparent closeness disappears after coordinate and matcher-cause
stratification. If coordinates/cause/control support is absent, report the
explanation as unidentified, not confirmed. Four outcome-selected TRAIN
scenes cannot establish a population mechanism or validation benefit.

Server-6 GPU7 targeted read-only check: 42,025 MiB used, 39,055 MiB free,
one foreign 41,996 MiB process, 37% instantaneous utilization. No process
was touched. Defer native capture until actual occupancy, SSH, runtime,
data, checkpoint and source provenance are verified. No enqueue/sync.
