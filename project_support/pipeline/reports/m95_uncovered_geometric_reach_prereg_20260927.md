# Frozen M95 missed-support geometric reach

Stable ID `m95-sample-context-support`. On the unchanged SHA-bound
256-expression TRAIN capture and exact scene-to-superpoint coordinate
binding, use the previously selected 16 mask-limited and 16
target-size-matched covered expressions. For each target superpoint
missed by all 128 native masks, compute the Euclidean distance from its
physical centroid to the nearest target superpoint in the union of
the existing 128 positive query masks. This use of target labels is
strictly retrospective. Compare with the nearest-target-positive
distance for unseen non-target superpoints, matched to the same
expression. Normalize distances by the median first-neighbor spacing
of *all scene superpoints* to report dimensionless reach. In each
expression record target/background medians, the count of missed target
superpoints within one local scene spacing, and missing/undefined
cases. Validate scene bytes and native physical superpoint indexing.
Report all preselected rows and scene denominators without changing
any model, mask or query.

If missed target superpoints are systematically close to native
positive support while equally uncovered background is distant,
a new local, prediction-blind propagation source might be plausible;
if not, locality cannot justify a repair. Even a positive result
cannot isolate target identity or improve inference. It is a
GT-localized diagnostic, not a causal forward intervention, gate
receipt, or training authorization. Do not infer a distance cutoff
by sweeping these rows.
