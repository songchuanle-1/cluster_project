# Mask-limited target-seed residual

Stable ID `m95-sample-context-support`. Reuse the immutable 256-expression
TRAIN native capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
Cross-check the exact eight target-seeded selected failures and four
same-target-seeded-query-limited rows from
`m95_target_seed_query_counterfactual_20260927.json` SHA256
`22d0b83e3d3a4dd4cce7487193de02a356b4d0373505eb2fa35286a2781dfb3c`.
For those four rows only, count any *non-target-seeded* query with native
IoU > .5. Use the frozen selected query, target set, sampled seed indices,
FPS superpoints and physical-instance labels. Report each row, the best
mask IoU, seed identity, indicator-score rank and scene denominator.

If non-target-seeded adequate masks exist, "mask-limited" means only
target-seeded masks; the overall query population has a valid mask and the
remaining distinction is ordinary ranking/positive-set definition. If
none exist, the native forward is truly mask-limited for that expression.
Neither case supplies a deployable signal: IoU and physical target identity
are GT oracles, not inference features. No selector, matching loss, PIRS,
or seed-coverage variant is admitted on this diagnosis.
