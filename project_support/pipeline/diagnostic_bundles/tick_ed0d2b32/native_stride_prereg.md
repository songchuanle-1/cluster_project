# Actual Native M95 Stride Provenance: Finite Continuation

Stable ID native-train-prefix-repeatability-audit; same hypothesis and no
implementation revision/new architecture. Exactly two fresh ORIGINAL M95 native
train-mode forward/backward/clip processes, frozen existing epoch16 checkpoint,
first two TRAIN groups, seed1999, batch2, native trainable flags. No optimizer,
scheduler, VAL, backend flag change, tuning/clearing caches or retry-until-diff.

At the ACTUAL first strided SparseConv3d (unet.conv.2), observe the existing
CONV_CPP forward-cache descriptor immediately before and after that call.
Save exact input/output features, coordinates, weight, actual output cotangent,
input gradient, and its original ImplicitGemmIndiceData tensor fields, including
pair_fwd/pair_bwd, masks and argsort arrays. Queries/hooks must return native
outputs unchanged. Retain source/hash/RNG checks and lifetime GPU three locks.

CPU analysis aligns output coordinates and canonicalizes both incidence tables:
pair_fwd columns follow output coordinate order; pair_bwd output IDs are
remapped to the same canonical ranks. Compare coordinate sets, native numerical
outputs, masks/sort order and actual selected descriptors. Raw row permutations
are not arithmetic errors. Different descriptors are only association; equal
descriptors do not prove identical execution. Do not assert a unique atomic cause.

On the first256 lexicographically ordered output coordinates, compute a float64
mathematical reference from ORIGINAL weights/input/pair_fwd in fixed kernel order,
only after verifying actual weight layout. Report error, not a new native
tolerance PASS. This is a consistency diagnostic, not a production precision
change, resource admission or estimate of trained benefit.

After these two processes, conclude this finite reproducibility audit with what
is identified and UNKNOWN. Do not let an optional unique-kernel explanation
become an indefinite prerequisite for the point-feature mainline. Future causal
tests require exact saved-prefix/native-flag controls; keep1e-6 and1e-12 gates.
