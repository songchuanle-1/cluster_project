# Origin of target support missed by native positives

Stable diagnosis `m95-sample-context-support`. Same frozen 256-expression M95
TRAIN capture and 16 limited plus 16 size-matched covered controls. On the
four previously frozen fragmented rows, define target support missed by the
union of native matcher-positive masks. For each missed superpoint covered by
at least one other query, classify each covering query using the captured
FPS seed -> physical superpoint -> physical instance chain: target-seeded
and matcher-negative, non-target-seeded, or matcher-positive (contract
violation). Report the disjoint per-superpoint counts (any target-seeded
negative, only non-target-seeded, uncovered) and query counts, including the
other limited and covered controls. Do not reselect the cohort using outcome.

Hypothesis: if native-positive union misses target support that remains in
target-seeded matcher-negative queries, existing matching omits a potential
training path; if it is only in non-target-seeded queries, a seed-identity
constraint blocks the simple positive-set-union interpretation. A matching
disagreement alone is not a proposed loss; it requires a separate
prediction-blind mechanism, matched intervention, placebo and all six gates.
Target labels are used only for this diagnostic readout. Do not deploy
oracle query identity or relabel generic mask-aware matching.
