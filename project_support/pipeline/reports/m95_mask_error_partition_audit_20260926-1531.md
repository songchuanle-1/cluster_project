# M95 Frozen Mask Error Partition

2026-09-26 15:31 Asia/Shanghai. Read-only server-6 CPU analysis of the
same frozen 256-expression TRAIN capture used for the pair-union bound.
The capture SHA256 was
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`;
all native artifact hashes, scene/annotation bindings, query axes and
best-single IoUs were checked. Three focused CPU tests passed.

For each expression's *oracle best existing single mask*, target false
negatives and false positives are counted on the identical native
superpoint support. The 16 rows without a >0.5 mask (16 scenes) split:
7 FN-dominant, 8 FP-dominant, 1 tie; zero with no target overlap.
Mean best-mask precision is 0.6674 and recall is 0.7011. For the
240 rows with an acceptable mask (209 scenes), 50 are FN-dominant,
99 FP-dominant and 91 tied; mean precision 0.9139, recall 0.9503.
This stratifies by the observed outcome, so it cannot identify a
causal correction or predict a deployable classifier.

In particular, neither monotone expansion nor contraction is a
common correction for the 16 limited cases. The earlier oracle union
rescued only 2/16. This does not disprove a genuinely new geometric
mask-generation mechanism, but provides no diagnosis, matched
intervention, backward/resource result or independent package for one.
Keep the six gates and queue unchanged. The next useful test must
predefine target-blind mask/geometry features and a same-support
matched negative control before examining corrections.

Evidence: `pipeline/reports/m95_mask_error_partition_20260926-1529.json`
SHA256 `5fc51cd7e4672d4ee1d65079eaf1001bbe10a4acafbe84a75503ed293feb7410`;
`scripts/m95_mask_error_partition_20260926.py` SHA256
`cfb627cdcf14e95ae4e4c2176541710deb583baa3637232f0992301460e2a000`;
`scripts/test_m95_mask_error_partition_20260926.py` SHA256
`74acc3e8fa8b0cfbc4b9735d5f7461ec9dd7e55b4b6404668a77c9c8168a2fa0`.
