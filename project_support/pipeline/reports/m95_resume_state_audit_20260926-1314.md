# M95 First-Stage Resume-State Audit

2026-09-26 13:14 Asia/Shanghai. Stable ID: `m95-repro-drift-boundary`.
This is a read-only code/provenance review, not a native forward or an
admission test.

The hash-bound script `scripts/m95_full_order_first_stage_20260926.py`
reconstructs the TRAIN dataset, shuffled batch-2 loader (zero workers),
checkpointed M95 model, and seed 1999, then executes every preceding
model loss forward until row83 at step3137. It records progress every 100
steps, but neither the progress JSONL nor the interrupted process stores
the loader permutation/cursor, transformed batch stream, NumPy/Torch/CUDA
RNG state, or complete producer/model execution context. The previous
attempts stopped at steps 3000 and 600. Their progress events are not
checkpoints and cannot be used for exact continuation.

The verified remote loader source
`framework/dataset/__init__.py` (SHA256
`eb3f092f427ec70c62adfa5c7e4586335fbc925ea76d175ef33387f9fa4da33c`)
uses shuffle and drop_last in TRAIN mode. The verified remote dataset
`framework/dataset/scannetv2.py` (SHA256
`2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d`)
uses NumPy random transforms in `transform_train`. The script also resets
the seed before each loss forward, so simply skipping earlier forwards or
loading a saved row83 batch would remove the original-order execution
context being measured. Capturing pre-target states at future boundaries
could be investigated, but equivalence requires a paired uninterrupted
control with the same frozen inputs, source hashes, stage tensors, and
readout. No such receipt exists. No state-checkpoint shortcut is validated.

At this tick's live SSH checks, server-6 GPU7 had an external PID 1916226
using 61,138 MiB; the card used 61,147/81,559 MiB at 68-70% utilization.
The PID changed since the prior audit, but the occupation remained. No
foreign process was touched. The authorized exclusive native diagnostic
cannot safely start under this occupation. No model candidate passed the
six admission gates; the strict 26/65 comparator remains unchanged.

Resume after verified GPU7 idleness and an exclusive lease with an
uncontended window greater than 50 minutes plus retrieval. Use a fresh
full-order run with sufficient outer timeout and unique result/progress
paths. Treat interruption as incomplete. Only consider a checkpoint
shortcut after an independent equivalence control, not as a reason to
admit a numeric-scatter or ranking variant. Independently screen new
task mechanisms against the closed-route evidence.
