# Target-seeded selected-mask extent audit

Stable ID `m95-sample-context-support`, diagnostic only. In the immutable
256-row TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`,
use the eight target-seeded selected failures from the full-population
screen. Check selected mask axis equals physical-instance superpoint axis,
selected seed mapping matches `fps_superpoints[sampled_seed_indices[q]]`,
and the recomputed unweighted target IoU agrees with native `ious[q]`.

For each target-seeded failure, partition target undercoverage
`FN/(TP+FN)` and mask contamination `FP/(TP+FP)` at the native
zero-logit threshold, recording TP/FP/FN and physical-instance target size.
Define an undercoverage-dominant failure as FN > FP and a contamination-
dominant failure as FP > FN; equality is distinct. Compare to successful
target-seeded expressions in the same scene, but keep distinct-target
controls explicitly unmatched. Report independent scene counts and the
full row list, not a significance test on eight selected errors.

If either pattern dominates, it remains ordinary mask prediction/quality
diagnosis, not a novel information path. A frozen existing GT mask is an
oracle for error partitioning only; it cannot be an inference-time signal.
No learned correction, admission, or validation improvement follows.
