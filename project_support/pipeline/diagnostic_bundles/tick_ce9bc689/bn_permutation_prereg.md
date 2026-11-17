# Conditional FLE BatchNorm Row-Permutation Control

Registered after first-block alignment located the first numerical difference at
unet.u.blocks.block0.conv_branch.0: same coordinate-aligned input, train-mode
BatchNorm output maxdiff9.5367431640625e-7. Do not infer the kernel implementation.

One fresh ORIGINAL native FLE train forward/backward/clip captures this BN's
actual output cotangent. Then three isolated clones of the identical original
BN state/weights/mode process the EXACT saved input: A, exact-A repeat, and B,
where B changes only row order to the second previously observed native order.
Match input/output/cotangent by exact sparse coordinates. No seed/backend/epsilon
change, no optimization, VAL, new model or admission. Fixed native cotangent and
original parameter requires_grad flags are preserved for all three VJPs.

Replay A/B must reconstruct prior native A/B at existing1e-6 tolerance, exact-A
identity must be0, and one zero-cotangent input/weight/bias VJP must be exact0.
If A-vs-B alone reproduces nonzero aligned output, row permutation is a sufficient
local numerical cause in this fixed batch. This is not a trained noise floor,
whole-model causal attribution, proof of atomic operations or proposed fix.
No retries until matching. Retain all failed and partial results.
