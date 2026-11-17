# Native TRAIN point-order applicability

Stable `m95-sample-context-support`, diagnosis. Earlier 64-scene screen found
zero original first-point versus majority semantic mismatches but did not
establish whether native TRAIN sampling changes the first retained point.
Freeze the same 64 scenes. Check each physical scene point count against
the M95 TRAIN `voxel_cfg.max_npoint` and inspect the native
`transform_train`/`sample_rdn` path for any ordering step. A point count
strictly below the threshold implies the sample index is an all-true Boolean
mask, retaining original order; augmentation affects coordinates and RGB,
not semantic or instance point order. Report all counts and source hashes.
No model prediction, GPU, admission or training.
