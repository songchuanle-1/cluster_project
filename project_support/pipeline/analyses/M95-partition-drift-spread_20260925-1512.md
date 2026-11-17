# M95 Frozen Partition Drift Spread

The hash-verified paired captures were compared on server-6 CPU only. The
reference and candidate captures have SHA256 `f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025`
and `68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
Three synthetic analyzer tests passed. No native model forward was run.

Row 83 (1,332 points) has no changed level-0 assignment and no point with
final-feature max absolute drift above 1e-3, despite one thresholded mask
change. Row 174 (860 points) has one changed assignment, point 344, and 15
points above 1e-3. The changed point itself is above threshold; two unchanged
points in its original cluster and three unchanged points in its new cluster
are also above threshold. Nine other points above threshold are outside both
cluster neighborhoods. The old/new neighborhood groups can overlap.

Thus drift is not confined to the reassigned point or its two cluster
neighborhoods. Association with the changed hierarchy is a reproducibility
lead, not an intervention or a causal attribution. The original strict
comparator still fails 28/65 paired rows. The frozen row lacks the source
point coordinate and native distance row; cluster readback and decoder-query
states remain absent.

GPU7 was 100% utilized with 61,957/81,559 MiB in use, including foreign
PIDs 3694608 and 3122485. No GPU diagnostic or model admission was attempted.
Next, when GPU7 safely frees, verify checkpoint, manifest, code/environment
and producer identities; run changed-producer native cdist observation,
separately repeat the unmodified strict comparator, and capture cluster/query
boundaries with explicit provenance.

Evidence: `pipeline/reports/m95_partition_drift_spread_20260925-1510.json`
SHA256 `3c95f09ee64f3b94b7ebbf5ac7195f0253059090a5252a8f674c4c55f30a2069`.
