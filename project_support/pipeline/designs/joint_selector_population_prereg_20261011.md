# Broader Frozen TRAIN Diagnostic

Continue stable m95-native-joint-mask-selector without changing its joint
operator, tolerance, seed, checkpoint, loss normalization or inference.
First31 cohort result: three recoverable failures, all one scene; this does
not establish generality. PIRS/control native-dtype adapter failure preserved.

Reuse the already-frozen point_detail_population_20261009/result.manifest.json:
32 scenes, first four native expressions per selected scene,128 expressions.
Native groups, original object IDs, annotation/source hashes must match.
Do not select new scenes based on a result. Include all128 expressions.

For same detached native tensors also rotate the original valid superpoint
target-support vector by one index: same target size, altered correspondence.
This is a synthetic diagnostic placebo, not an extra annotated target.
Report actual gradient difference, not merely nonzero gradient.
Record all posterior/likelihood ranking improvements and deteriorations,
scene concentration and saturation. Existing native point/mask labels only.

The joint loss marginalizes the query identity for an ENTIRE mask.
A critical diagnostic is posterior responsibility saturation: one full-mask
likelihood can suppress almost all queries, despite native multi-query target
support. If saturated responsibilities leave existing correct matched-query
mask gradients numerically absent, the intended multi-hypothesis supervision
is not established; preserve the failed realization rather than tune a
temperature, likelihood weight, support size or query count.

Next test if this diagnosis survives: full native graph backward on fixed
batch1 and batch2 plus exact controls; then resource/independence/goal gates.
No admission or trained efficacy is implied by any detached-tensor result.
