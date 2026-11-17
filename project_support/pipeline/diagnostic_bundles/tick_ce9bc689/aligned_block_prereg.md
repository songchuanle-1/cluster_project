# FLE First-Block Coordinate-Aligned Localization

Registered after the sparse controls: M95 two fresh processes had equal frozen
inputs/weights but aligned first-stride output difference3.3378601e-6. FLE first
stride remained coordinate-aligned exact0 despite changing row orders. Hence
do not claim first-stride arithmetic divergence for FLE or blame BatchNorm yet.

Exactly two additional FLE ORIGINAL fresh native.train/backward/clip captures,
same frozen batch/checkpoint/seed/native flags. Save raw pre/post tensors only
for unet.conv.2 and unet.u.blocks.block0, keeping other observational hashes.
Record actual norm_eval and first-block BatchNorm training mode. Align each
first-block output to its preceding downsample coordinates; all SubM sparse
indices must preserve that row order/coordinate set, else alignment is invalid.
Determine the earliest coordinate-aligned floating difference within this block.
This discriminates row-permutation-only from actual early-block numeric drift.
No extra trials, kernel forcing, gate changes, production patch or training.
If the whole first block aligns exactly, the source remains deeper/unknown;
preserve that negative localization and do not claim a BatchNorm cause.
