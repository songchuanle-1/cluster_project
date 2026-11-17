# Prediction-blind support swap diagnostic

Stable ID `m95-sample-context-support`; use the unchanged M95 frozen TRAIN
capture SHA256 `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and 16 limited/16 size-matched controls from
`m95_native_mask_population_20260927.json` SHA256
`71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea`.

The target-only fused-feature replacement improved three limited masks,
but it used forbidden target labels. Here the replacement support is the
*deployed* query's existing `logits > 0` mask, chosen without target labels.
Hold the query index, learned out_norm, and all other final superpoint features
fixed. Substitute pre-encoder fused features only on that support, and
recompute the deployed mask and physical target IoU for evaluation only.
Reconstruct all saved logits to absolute tolerance 1e-4 first.

For a size-matched nonsemantic control, circularly shift the binary support
by half the superpoint count before replacement; no target labels are used
to construct either support. Report original and shifted support target
overlap *post hoc*, all 32 individual outcomes, per-scene denominators,
empty supports, improvement/harm and strict IoU >0.5 crossings. Never
select the better shift per expression or tune the offset to outcomes.

This is a fixed-checkpoint counterfactual, not a new model, proposed
training mechanism, or admission gate. A real deployable structural
candidate would still need matched causal controls, native full backward,
resources, independence, constraints and distinctness from closed
mask-aware readback/selector directions.
