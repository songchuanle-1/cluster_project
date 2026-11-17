# Frozen feature-prototype oracle screen

Stable ID `m95-sample-context-support`; source is the unchanged 256-expression
M95 TRAIN capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`.
Use the same 16 no-acceptable-mask and 16 size-matched controls frozen by
`m95_native_mask_population_20260927.json` SHA256
`71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea`.

For each expression, recompute the final mask logits using the learned M95
out_norm and verify the full saved-logit axis within absolute 1e-4, before
testing. With physical labels for an oracle-only test, form an L2-normalized
prototype of all final features in the ground-truth referent. Score each
existing query by cosine similarity of its normalized query state with that
prototype. Select the highest-scoring query; break ties by the smallest
query index. Report the selected IoU and paired change versus deployed
selection, per-expression and scene denominators for limited and controls.

Repeat the *same* selection with a prototype from each existing
same-category non-target instance, then report whether the target-oracle
selection is specific beyond that negative-control family; no
category-oracle variants if no competitor is present. This is explicitly
non-deployable: the physical target prototype is forbidden at inference.
Even a positive oracle screen cannot pass diagnosis or controls for a
new method. A null/negative result rules out only this readout, not
all representation or new information routes.
