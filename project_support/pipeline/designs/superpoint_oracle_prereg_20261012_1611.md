# Superpoint Expressibility Diagnosis

## Frozen Question
Stable ID: m95-native-superpoint-oracle-ceiling
Hypothesis ID: native-superpoint-quantization-forces-localization-failure
The unchanged frozen 32-scene/128-expression TRAIN population contains targets
whose best possible binary union of native superpoints cannot reach IoU 0.5.
This is not the earlier complete-erasure hypothesis or a repetition of mixed
boundary incidence. It tests an exact representational ceiling, not model gain.

## Test And Controls
Use the original dataset, original config, original frozen manifest and seed1999
on server-6 CPU, CUDA disabled. Reconstruct each actual native TRAIN target and
superpoint assignment. For support j let a_j be target count and b_j non-target
count. Optimize sum(a_j)/(target_total+sum(b_j)) over selected supports, using
descending a_j/b_j prefixes (b_j=0 first). Report native majority IoU, exact
oracle ceiling, gap, expression and scene denominators and mixed supports.
Verify the optimizer by exhaustive enumeration on small controlled partitions;
include an intentionally merged 1-positive/3-negative support with ceiling .25,
a perfectly split control with ceiling 1, and a case where majority is
suboptimal. Repeat original native sampling twice, compare physical masks and
support counts, and retain any differences. Do not change the native dataset.

## Falsification And Scope
Reject only the forced-IoU-below-.5 premise if all frozen ceilings are >=.5.
A positive gap or low ceiling is diagnosis only, not an admitted mechanism.
Do not infer unseen population incidence, trained efficacy, novelty, native
whole-model backward or resource PASS. Point-refinement prior art and failed
PDC/BEI remain in force; no successor is admitted merely from this diagnostic.
Any supported independent structural route requires its own matched controls,
native backward, resources, independence and goal constraint review.
