# Server-3 Resource Port

Owner token abdff23d5e2e40c3aadcde78f6b4fea9. User authorized server-3 GPU1
fallback while server-4 is blocked. No new training variant or M201 restart.
Keep M95 source/config/checkpoint, seed1999, original TRAIN groups0/60/101/124,
two repeats, batch2, loss, existing numerical controls and all earlier FAILs.

Verified target: sysu311-MS-7C59, RTX3090 GPU1,
GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0, total24268MiB, driver470.182.03.
The existing project_cluster environment has no torch. Reuse, without modifying,
the existing3d-stmn environment: Python3.8/torch1.12.0+cu113/transformers4.31.0.
Record compatibility failures rather than silently changing model calculations.

Hardware-specific feasibility protocol, not a scientific acceptance change:
the old server4 literal30000MiB free guard cannot fit a24GB card. Require GPU1
no foreign NVML context, idle-equivalent free>=total-1024MiB, and all three
mapped GPU1 training/exclusive/transport flocks acquired before CUDA allocation.
Retain allocator fraction0.25, which is a smaller absolute allocation than on
server4. Respect the real foreground deadline. No reset, eviction or lock deletion.
Measure reference feasibility here; it is NOT full-model efficiency admission.
The original<=10G FLOPs, relative memory+15% condition and matched benchmarks
remain unchanged and must be remeasured on one device before any new admission.

Transport the unchanged Git commit f8457d3b657e66306a7fce1afb3d81d8ab874669
into a fresh isolated checkout; do not overwrite existing server3 code or the
user's dirty validate_pdc script. Transfer only the exact frozen M95 checkpoint
SHAfe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e.
No dataset replacement or validation selection. Adapt only server paths, GPU
mapping, resource guard and Python/PyTorch serialization API compatibility.
The frozen old adapter and its original failures remain untouched.
