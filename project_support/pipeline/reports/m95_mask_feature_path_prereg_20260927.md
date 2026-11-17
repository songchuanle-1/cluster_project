# Mask-path feature-gradient census, frozen TRAIN capture

Stable ID `m95-sample-context-support`. Native decoder mask prediction is
`logits = normalized_query @ final_superpoint_features^T` (M95 `dec.py`);
criterion matches physical seeds and applies BCE+Dice on each native
matcher-positive query. The 16 no-acceptable-mask expressions all retain
a positive query with corrective final-logit gradients in
`m95_positive_coverage_20260927.json`, SHA256
`a81b30f58c039cf52bc26c00e345408113c96a935fd0290a7502e799f5a0c7ce`.

For the same frozen 256-expression/220-scene M95 capture SHA256
`68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a`,
select each limited expression's best native-positive query as pre-registered
above, and all 16 target-size-matched covered controls from
`m95_native_mask_population_20260927.json` SHA256
`71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea`.
Verify artifact hashes, query state and final feature shapes, and reconstruct
every saved final mask logit within numerical tolerance before examining
gradients. Replay native BCE+Dice over all matched queries; differentiate
the selected positive query's mask loss into both query state and final
superpoint feature source. The mask readout has a LayerNorm query, so do
not assume captured query states are already normalized without checking.

Report finite/nonzero source gradients and scene denominators; matched
controls only assess gross path availability. A gradient here does not
prove training can resolve the failure; cancellations across auxiliary
layers, semantics, scene distribution and optimizer remain unmeasured.
No new mechanism, resource/independence PASS or training follows.
