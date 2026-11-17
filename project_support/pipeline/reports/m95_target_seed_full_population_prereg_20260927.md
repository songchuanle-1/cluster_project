# Full-population physical target-seed failure controls

Stable diagnostic ID `m95-sample-context-support`. The 128-row exact-input
TRAIN cohort has three persistent target-seeded mask failures, but no
same-physical-target successful expression controls. Before treating this
as a new information path, independently screen the frozen 256-expression
M95 full-TRAIN native capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
No new model forward, intervention, training or GPU allocation.

Validate producer/checkpoint/manifest, all 256 manifest indices, 128 query
slots, and superpoint bounds. Bind selected query seed using the audited
native `fps_superpoints[sampled_seed_indices[selected_query]]`, then
`physical_instance_labels`. Match a failing target-seeded selected query
(`ious[selected_query] <= .5`) to successful target-seeded expressions of
the same scene AND same target physical-instance set. Report failures,
independent scenes, paired groups, mean observed IoU difference and all
paired row identities; separately report same-scene controls with other
targets as an intentionally insufficient comparator.

If same-target controls are absent, no same-target pairing is available and
this route cannot claim a matched causal control. If present, different
language and query selection remain confounders: no novel mechanism follows
from an observational pair. Existing same-target description consistency,
mask-quality/PIRS and generic ranking remain closed, regardless of outcome.
No validation benefit or six-gate PASS may be inferred.
