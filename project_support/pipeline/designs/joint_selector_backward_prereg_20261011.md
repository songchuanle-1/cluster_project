# Full Native Graph Backward

Stable candidate m95-native-joint-mask-selector remains validation.
Reuse the first1 and first2 native groups of the pre-existing frozen32-scene
manifest. Seed1999, original checkpoint, unchanged input tensors, native
batch collate, valid-superpoint support and native matched target masks.

Build the complete unchanged native model loss graph in eval loss mode.
At every original criterion call (final and auxiliary), replace only the
original indi component by the joint query/mask marginal loss.
Keep original indi coefficient, matched-count normalization, auxiliary layer
coefficients and all other losses/architecture/schedule unchanged.
This is a diagnostic graph, not a production model or training launch.

Compute joint-component gradients and full modified-loss backward into every
trainable original model parameter. Report finite/nonzero gradients separately
for decoder indication heads, native mask/query paths and backbone.
Repeat the SAME collated native tensors twice at batch1 and batch2.
Fixed absolute1e-6 loss/gradient repeat threshold. Retain every failed repeat;
do not change the threshold or call detached double operator checks a repair.

No optimizer step, predict FLOPs/latency protocol or efficacy gate is covered.
If all backward checks pass, the next required work remains independent
whole-mechanism/primary-literature review, complete native matched controls,
model/config isolation and matched prediction resource measurements.
