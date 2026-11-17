# Frozen modality disagreement diagnostic

Stable `m95-sample-context-support`, diagnosis only. A distinct possible
information source is pointwise disagreement between native projected 2D and
3D superpoint features before fusion. Unlike positive-mask union or geometry,
this is computed without query selection, target labels or inference-time
oracle. Test whether it is enriched at missed target support beyond
physically annotated same-class peer support; a nonspecific discrepancy
cannot justify a new fusion path.

Freeze the existing 256-row M95 TRAIN capture and the preselected 26-row
valid-semantic physical-peer cohort. For the best native matcher-positive
query in each row, use its missed target mask only for retrospective
evaluation. Score each superpoint by `1-cosine(projected_2d, projected_3d)`
without learned scale or threshold. Compare its mean over missed target
against (a) all physical same-class peers, (b) first equal-size valid
different-class physical superpoints in support order, and (c) covered
target where available. Report signs and raw means by frozen groups:
fragmented (2), other_limited (1), covered_controls (2), remainder (21).

Primary screen requires both fragmented scenes' missed-target mean to exceed
same-class peer and different-class controls. If not, this observable is not
specific there. Even a positive result would require independent scenes,
same-forward mechanism/placebo, native backward and efficiency before
admission. Neither target labels nor best-positive selection may enter the
proposed inference-time signal.
