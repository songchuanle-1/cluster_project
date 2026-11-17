# Fine Exchange Saved-Storage Diagnostic

Tick19aeaa5c23b8475ebe2148a0fdcf4e6b;cluster_project only.
This is a finite efficiency diagnosis,not a new model or parameter search.

Question:does the admitted zero-new-parameter fine exchange nevertheless
retain an N*K*C donor-feature storage for backward,including masked padded
neighbor slots? This is distinct from prior cutoff/rotation/continuity tests
and from the pending trained self/nonself mask diagnostic.

Freeze production K32,H8,C256,float32. Cases:single leaves with N16,N64,N128,
and N128 split into16leaves of8. Use exactly seeded1999 synthetic Gaussian
positions/features;no training data,checkpoint or validation selection.
Prediction:the maximum noninput floating saved storage is N*32*256*4bytes
and has a saved[N,32,8,32]view. It doubles from N64toN128 even with no new
parameters. The16leaves case has only N*8valid graph edges but still reserves
N*32feature slots. Record data,do not assert VRAM or total peak from this.

Use the actual unchanged source build_graph/exchange,not an alternative
attention implementation. torch.autograd.graph.saved_tensors_hooks records
references without cloning. Deduplicate by underlying storage pointer;
separate input aliases,integer/bool graph buffers and new floating storage.
Read saved-storage sizes before backward. This is retained forward storage,
NOT allocator peak,all training activations,CUDA memory or a resource PASS.

For each case compare hooked forward/gradient to the same source without
hooks,and a no_grad forward. Require exact outputs,finite nonzero gradients,
and original float32 tolerance1e-6 for the matching gradient. Record all
actual source shapes/strides/storage sizes and reference counts. EightCPU
gradient executions and twelveCPU exchange calls are not native network
backward/forward or optimizer steps. No CUDA/FPS/native network/preprocessing.

Register this diagnosis before source-level profiling or broad review.
Verify owning lease/deadline/goal,strict known-host SSH hostname,all nine
source hashes and deployed config. Execute on server4CPU with CUDA hidden
and one thread;do not use its GPU1 without explicit authorization. Do not
modify source/config/seed/schedule/ongoingM203,add chunks/checkpointing,
admit a model or claim memory savings before a matched native GPU test.

Complete only this finite accounting question if controls agree;preserve
unexpected measurements. Native lifetime/memory and useful mask content
remain unknown and continue under existing stable IDs after actual idle
authorized GPU release. Do not rerun this fixed profiling as new progress.
