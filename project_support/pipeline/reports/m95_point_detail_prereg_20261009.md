# Native Point Detail Field: Preregistration

Created 2026-10-09 Asia/Shanghai, before the new native readout.
Stable ID: m95-native-point-detail-field.

Hypothesis: original superpoints are adequate supports, but mean pooling removes
within-superpoint point evidence. A query-conditioned point field can represent
the annotated boundary without changing partitions, query selection, attention
routing, matching, augmentation, schedule or numeric hyperparameters.

This is NOT a re-partitioner, seed-consistency loss, centroid-graph edge loss,
mask-quality ranking, new selector or repeated cluster injection.
The prior original-superpoint oracle >0.969 refutes an irreducible-support
explanation; it does not establish exact point homogeneity or test a point field.

Sampling: the existing prediction-blind 31 TRAIN expression manifest plus native
loader companions, checkpoint M95 with its recorded SHA256. Keep every row and
report missing supports. No validation outcomes select this mechanism.

First test: retain native point features before scatter_mean. Record point/SP
counts, mixed target/background superpoints, target point disagreement under
native majority-SP ground truth, and feature detail energy inside those mixed
superpoints. All metrics are point-to-point, never subtract SP-IoU from point-IoU.
Matched control broadcasts the per-SP mean point feature to the SAME points.
The control removes within-SP detail only. A cyclic within-SP permutation is an
additional alignment control. Two seed1999 repeats, strict 1e-6 for normalized
readouts and exact input/discrete identity; retain a failure rather than loosen it.

Expected mechanism direction: real detail has nonzero within-SP energy, the
broadcast control has zero, and there exist annotated mixed-SP boundaries.
No fixed task-benefit threshold or tiny-cohort significance requirement.
No mixed boundaries, absent native detail, a silent no-op, unexplained adverse
native results, or failed graph/resource/constraint checks prevent admission.

Conditional implementation: an independent query-to-point mask decoder reads
pooling-preceding point features and their SP-centered detail. Existing queries
and matches supervise the original SP path unchanged. Native point BCE+Dice
supervise the new field with the inherited mask-loss coefficients, not a searched
weight. Inference uses the unchanged selected query and evaluates only its point
field. Fine decoder dimension follows the backbone width (32), not a sweep.
All new trainable tensors must have finite nonzero native-loss gradients.

Matched intervention: same parameters, queries, target labels, inputs and RNG,
but replace point detail by its per-SP broadcast control. Compare point-field
variation and native gradients, not untrained mIoU as an efficacy claim.

Before training: compare baseline, champion and candidate on the identical
historical predict-mode resource protocol, bs1/warmup20/repeat100, fvcore total
FLOPs<=10G, median/P90 latency and peak memory. Report unsupported operations.
Freeze ScanRefer VAL mIoU vs .4894 baseline/.5020 champion, scene-clustered
uncertainty, point-boundary/nonboundary and unique/multiple target subgroups.
Material harm uses the existing .002 branch-stopping margin, with uncertainty:
intervals overlapping the boundary are inconclusive, not a fabricated PASS.
Noise floor unquantified until suitable paired evaluations exist. Memory+15%
requires +.003 mIoU to retain. No new dataset, labels or extra seeds.

Novelty is not verified at registration. Point refinement is established prior
art; examine originals and describe the complete mechanism difference honestly.
Registration is diagnosis, NOT admission or efficacy.
