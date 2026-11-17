# Frozen Numerical Localization

Stable candidate: m95-hierarchical-mask-feature-path-audit.
Additional diagnostic only: no mechanism revision, training, precision change,
backend selection or admission. Preserve the previous 39 controls and 12 FAILs.

Reuse exact frozen fixture functions, seed1999, both trees, C256/head8, float32,
chunk5 and checkpointFalse. Inspect dense/grouped QK, probabilities, value
accumulation and fused output independently; reconstruct the dense path exactly.
Supplemental explicit-selected and SDPA MATH are diagnostic comparisons only.
Evaluate float64 on the SAME float32 inputs and already-computed float32 scale
weights: independent 1e-10 agreement tests arithmetic, not production precision.
Retain/report original 1e-6 float32 verdict. Do not select a passing backend.
If reconstruction fails, do not attribute stages. If float64 disagrees, preserve
algorithmic uncertainty. Agreement supports arithmetic-path sensitivity only,
not native correctness, resource advantage, task gain or training admission.

Pinned server-4 CPU, one thread, CUDA hidden, no optimizer or full-model forward.
Save source hashes, raw output and actual deltas. Native learned-feature capture,
native backward, whole-model resources, novelty and trained mIoU stay unknown.
