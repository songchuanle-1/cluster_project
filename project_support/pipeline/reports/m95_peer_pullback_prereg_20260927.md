# Frozen peer/target query-state gradient pullback

Stable `m95-sample-context-support`, diagnosis only. The 26-row final-normalized
mask BCE probe found negative target/peer gradient cosine even in nonfragmented
controls. Its final-layer feature-space calculation omits the actual out_norm
Jacobian, and thus cannot establish an upstream query-state conflict.

On exactly the frozen 26-row TRAIN cohort, reconstruct each best native-positive
query's logits with the M95 checkpoint. Use torch autograd through the checkpoint
LayerNorm and the final mask dot product. Compute BCE-with-logits gradients on
missed target support (positive) and physically annotated same-class peers
(negative), separately, with respect to the *same pre-LayerNorm query state*.
Record gradient cosine and norms. As a matched control, use an equal-size,
index-first valid different-class physically annotated negative support.
Predefine `fragmented`, `other_limited`, `covered_controls`, `remainder`.

If conflict is also widespread in controls, it is not evidence of a
fragmented-specific deficit. This query-level calculation still excludes
Dice, prior decoder Jacobians and optimizer; never claim native full backward,
new intervention, causal repair or admission from its result.
