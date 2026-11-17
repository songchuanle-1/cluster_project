# M95 physical-target supervision-mass diagnostic

Stable ID: `m95-sample-context-support`. This is a diagnostic, not a
candidate training objective. Freeze the 128-expression, 32-scene TRAIN
population, transform seed 1999, checkpoint, input fingerprints, selected
seeds, and native focal score gradients in
`m95_target_seed_size_native_20260927.json`; compare to the earlier native
direction capture by expression and seed identity. Small repeated-forward
floating-point differences are allowed; gradient values are not asserted
bitwise identical. For each expression compute the sum of
absolute target-seed score derivatives divided by the physical target
superpoint count. Also compute the mean absolute derivative per target seed
where at least one is present. Zero-seed expressions remain zero for the
first measure and undefined for the second.

Prediction: if failures uniquely lack focal target supervision beyond
physical target size, the first measure should be lower for failed
expressions than successful expressions *within the same scene*. A lower
per-seed derivative is a separate intensity mechanism; compare it
separately and report the zero-seed denominator. Scene is the unit, not
seed/annotation. Report sign counts and means over mixed-outcome scenes,
not a fitted threshold or a training efficacy estimate. A reversed or
mixed sign defeats this specific shortage rationale; it does not prove
that all other independent mechanisms are exhausted. Never use this
post-hoc to retarget focal labels or revive the rejected bag objective.

The existing native artifact is reused read-only; no new GPU task,
candidate model, queue entry, or admission is implied.
