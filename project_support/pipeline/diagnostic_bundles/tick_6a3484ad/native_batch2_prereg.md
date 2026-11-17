# Natural Batch2 Incidence After Padding Invariance Fails

Continue SAME hierarchical-padding-context-invariance-audit ID. The prior
2scene interface test passed all reconstruction/zero-scale controls but
violated padding invariance for all6prespecified cases. Preserve that result.

Next run ONE native loss forward with original training batchsize2 using
the FIRST TWO previously frozen scene groups, unchanged checkpoint/source/
seed/config/data. This is a diagnostic, not a training iteration. Capture
actual gather input features/masks/tokens/IDs/fine messages and the exact
native last-layer prefix. No norm-permutation helper or new math revision.

Record actual valid lengths, real padding fractions and masked feature
magnitudes. Reconstruct native gather/message/suffix first at1e-6.
For each row, run the EXACT unchanged gather on only that row's valid
prefix with identical valid tensors, weights, tokens and hierarchy IDs;
reassemble all cropped valid outputs into original padded shape. Compare
valid outputs and final same-prefix mask logits. This tests invariance to
the native batch's actual masked extent, NOT another model or masked-mean
patch. Different GEMM shapes may add roundoff; retain identity controls and
all-zero-scale null controls at1e-6, report this limitation.

No point IoU calculation with incorrectly shared multi-scene point indices.
Use raw mask logits and actual point-message changes;task effect/VALgain,
full-training harm, shared-baseline incidence and a uniform fix remain
UNKNOWN. No production operator change, backward, optimizer, VAL, admission
or training is authorized. Fresh identity/GPU0/3locks/current deadline.
