# Prediction-blind all-query support diagnostic

Stable ID `m95-sample-context-support`. On the exact M95 TRAIN capture
SHA256 `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`,
reuse the frozen 16 no-acceptable-mask and 16 size-matched covered
expressions from `m95_native_mask_population_20260927.json` SHA256
`71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea`.

No target labels choose the support: form the Boolean union of all 128
existing native query masks (`saved logits > 0`). Keep the deployed query
fixed and replace the final feature by the pre-encoder fused feature on
that union. Recompute logits with M95's learned `out_norm` and require the
unedited full-logit reconstruction <=1e-4. Compare against unchanged final
features and a size-matched control support circularly shifted by half
the superpoint width. Record union/shifted coverage of physical target
only *after* the intervention for evaluation. Report support prevalence,
the per-expression IoUs, strict >0.5 fixes/breaks, paired signs and
scene counts in both groups; no tuning or per-row arm selection.

This is only a prediction-blind frozen-checkpoint support-availability
test. All-query union may be nearly the entire scene and hence cannot
demonstrate a selective mechanism. Do not call it an admissible mask
readback/selector or a training benefit.
