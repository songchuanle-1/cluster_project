# Within-object modality control

Stable `m95-sample-context-support`, diagnosis only. A higher 2D/3D
disagreement on missed target versus same-class physical peers might
describe generally poor 2D coverage at the target, not the missing
fragment specifically. On the same frozen 26-row TRAIN cohort and
unchanged best native-positive query, match each missed target superpoint
to a distinct *covered target* superpoint by nearest native query logit,
with support-index tie break and no reuse. Compute `1-cos(projected_2d,
projected_3d)` on both sides; report target-missed minus target-covered
per row and the predeclared strata. Rows lacking covered target support
remain undefined, without replacement.

The hypothesis requires both fragmented rows to have positive
within-target differences and no identical 2/2 pattern among
covered controls. A null or reversed result would disconfirm a
fragment-local information-loss reading of the two-scene signal.
Matching labels are retrospective controls only; no model change,
inference-time GT, new backward or admission.
