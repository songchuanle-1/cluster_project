# Native-positive support complementarity (diagnostic only)

Stable ID `m95-sample-context-support`. Freeze the 256-expression TRAIN M95
capture SHA256 `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`
and its artifact/manifest hashes. Before reading this result, select the 16
mask-limited expressions (`max native query IoU <= 0.5`) and 16 previously
frozen target-size-matched covered controls. The prior all-query union screen
found four fragmented limited expressions, IDs 64, 82, 96, 104.

For each expression, take the union of the unchanged checkpoint's native
matcher-positive query masks. Compare target recall and precision against
the retrospectively best single positive (maximum target TP, then minimum
FP, then query index), the all-query union, and a fixed-index equal-count
negative-query union. Report query count, TP, FP and per-scene denominators.
Primary question: is the extra all-query target support in the four frozen
fragmented rows present *within* the native matched-positive set, or only
in unmatched predictions? Count-matched negatives are a sanity control,
not a causal placebo, because matcher membership is target-dependent.
Fail the complementarity interpretation if positive union does not add
target recall or has the same nonspecific precision collapse as all-query
union. Explicitly report any covered-control harm and undefined arms.

This is a retrospective GT-localized diagnostic of an existing matcher,
not an inference-time rule, new-model backward, novel mechanism or training
admission. Do not introduce a ranking, union inference, generic bag loss,
numeric loss scaling, or score-gate successor from this readout.
