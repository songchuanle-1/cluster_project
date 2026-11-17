# Conditional Sparse Boundary Control

Registered after the first M95 trace pair, before any sparse-control result.
M95 first divergent boundary: unet.conv.2, post-event38 after equal pre-event37.
Both output features AND sparse indices differ; therefore raw feature differences
cannot be called arithmetic errors until coordinate alignment.

## Fixed Procedure
Exactly two fresh original native train forward/backward captures per M95/FLE,
same frozen checkpoint, first two TRAIN groups, seed1999/batch2/native flags.
Capture unet.conv.2 pre/post sparse features/indices/spatialshape and actual
native output gradient. Report coordinate sets, row-order permutation, aligned
float differences and the original native target gradients.
No production edits, new VAL, optimizer/scheduler steps or backend switches.

After each native backward, run two original isolated unet.conv.2 forwards and
VJPs with new SparseConvTensor inputs, no preexisting spconv1 indice cache, same
saved original features/indices and fixed actual native cotangent. Match
cotangent by coordinate, never by uncontrolled output row order. Both fresh
processes of a model use process1's exact saved control bundle/hash. Compare
aligned output, input VJP and weight VJP. Original gradients remain unchanged.
No assumption that isolated fresh-cache scheduling reproduces fullmodel timing.

## Controls And Interpretation
Saved-output reload and coordinate alignment identity must be exact0; output
coordinate sets must match exactly. Test one zero-cotangent VJP per process;
input/weight gradients must be exact0. Preserve 1e-6 native and 1e-12 float64
controls, with no tolerance relaxation or repeated attempts to match.
Record input/cotangent/source hashes and actual counts. A nonbitwise result
locates reproducibility limitations but is not trained seedvariance, an atomic
kernel explanation, an efficacy estimate or new architecture admission.
Use live pinned server4GPU0 plus lifetime three locks/currentticklease only.
