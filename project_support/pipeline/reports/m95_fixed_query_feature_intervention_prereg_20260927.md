# Frozen fixed-query feature intervention

Stable ID `m95-sample-context-support`; source is the same M95 checkpoint
SHA256 `fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`
and TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
Freeze the 16 no-adequate-mask expressions and 16 size-matched covered
controls exactly as in `m95_native_mask_population_20260927.json`.

For each expression, reconstruct M95 logits from the learned out_norm,
captured pre-norm query, and final feature; require absolute max difference
<=1e-4. Keep the *deployed query index* unchanged. Intervene only on the
captured final feature vector at the physical target superpoints, replacing
them with the corresponding pre-encoder fused feature vectors. Recompute
the deployed query mask by the unchanged `logits > 0` rule, target IoU,
TP/FP/FN and paired change. Matched controls: (1) replace the same number
of same-category non-target superpoints (deterministically first in
superpoint order); (2) retain the original features unchanged.

This is an oracle support intervention using labels, not an executable
training or inference mechanism. Report expression/scene denominators,
no-negative cases and signs. Improvement only in this oracle arm suggests
a recoverable feature readout *under inaccessible target support*, not
a usable proposal or admission. No threshold tuning, no learned adapter,
no model/queue changes.
