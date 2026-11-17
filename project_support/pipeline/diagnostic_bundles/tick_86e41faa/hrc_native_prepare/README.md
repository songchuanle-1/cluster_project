# HRC native worker preparation (frozen source, no execution binding)

Candidate M208-HRC / hierarchy-bottom-up-refined-token-composition, source commit 9e543af623acd7fa9bd4a3f81ce79c932e98774a. This directory contains a reusable diagnostic worker, runtime guard, unbound manifest template, and exact eight-source HRC package/native YAML snapshots. It does not contain an executable native_manifest.json or execution lease. No SSH, torch/model import, GPU execution, synchronization, queue or production-source edit occurred during preparation. Native correctness and resources remain NOT_RUN, efficacy UNKNOWN.

## Worker entry points

After a future owning root has supplied fresh validated execution bindings and staged these assets, use separate processes:

    python -B worker.py --lease execution_lease.json --mode smoke --target champion
    python -B worker.py --lease execution_lease.json --mode smoke --target candidate
    python -B worker.py --lease execution_lease.json --mode resources --target champion
    python -B worker.py --lease execution_lease.json --mode resources --target candidate

These are future remote-stage commands, not commands authorized to run from this preparation directory now. A given mode/target writes exclusive output/config/result names; do not rerun over existing outputs. The worker never invokes SSH, sync, reset, checkpoint resume or a formal training launch.

## Native protocol and observations

Setup uses the exact package selected by the native YAML basename, asserts both Network identity and its precise package.network module (preventing resolver fallback), constructs original AdamW/PolyLR and loads only the original backbone pretrain via gorilla.load_checkpoint. The old trained-M95 full checkpoint is SHA-checked for lineage only; this runtime has no setup() or torch.load initialization function.

Smoke retains native tools.train.train, original TRAIN loader (batch2, workers4, persistent, drop_last), two real batches, original loss/backward/grad clipping/optimizer steps, seed1999, epochs50 and scheduler max_iters70. Only the private work_dir and CLI-default dist=False are adapted. It observes three original FFNs once each per forward and each optimizer step's finite gradients/weight changes; HRC's fixed-child mean twice per forward with untouched original return objects, detached CPU-float64 sum/count reference at the frozen 1e-6 tolerance, native feature/output gradients, per-batch padding and both adjacent-empty/real-point-empty slots. It preserves fixed child-slot weighting, including empty-slot FFN bias.

Raw banks, IDs and child maps are cloned/fingerprinted then checked unchanged after the same full forward; CSORT must receive the exact original raw-bank tensor objects. Cross-process raw-bank fingerprints are observations, not an invented bitwise-repeatability gate. Original HCG is called once and its native-loss point-message gradient is observed. Fine refinement must equal the original raw-fine plus the captured original fine-FFN output without recomputing the FFN.

The dependency probe runs after normal model.forward has produced native loss and before native loss.backward. It uses a fixed nonconstant token/channel readout only on coarse IDs actually reached by composed ids2[ids1[ids0]]. autograd.grad requests the first Linear weights in fine/middle FFNs with retain_graph=True and allow_unused=True. M95 should yield None (the original YAML restricts hierarchy injection to the final layer); HRC should have finite nonzero paths. Exact observed zero fails the frozen probe; no readout/seed selection is implemented. Every tensor-gradient callback returns immediately while probe_active, so probe traversals are not recorded as native backward. Before/after .grad identity/version/value SHA, optimizer/scheduler state SHA and CPU/CUDA RNG equality guard isolation. No probe.backward, zero_grad or optimizer step is used. Wrappers/hooks are restored in finally.

The resources function AST is identical to the reviewed worker_v2 implementation: original fvcore handler hashes, bs1/lang1, one FLOP trace, warm20/repeat100 and unchanged input/parameter flags. Resources installs none of the smoke hooks, mean observers or probes. Candidate and champion input/batch fingerprints must be compared by the future owner before accepting paired evidence.

Smoke peak allocated/reserved includes diagnostic hooks, reference computations and the additional autograd.grad probe. It cannot be reported as pure TRAIN memory or compared to the control as a pure training increment. Separate no-observer/no-probe TRAIN pair memory remains UNKNOWN and is supporting evidence if later needed, not a newly added admission gate. The established predict resources protocol remains unchanged.

## Future owner binding requirements

Only a verified current foreground owning root may generate a native_manifest.json from manifest_template.json and a separate execution_lease.json. This preparation creates neither authorization nor a lease. The root must run its existing canonical actual-thread/token/deadline/goal/context/pending/current-resource guard before staging and before dispatch; child preparation identity is not execution authority.

Fill only actual current binding fields: current_token, tick_generated_at, deadline_at, stage, physical_gpu, gpu_uuid, allowed_gpus, context_sha256, pending_sha256 and runtime_code_commit. Stage must be /data/songcl/Project/Cluster_project/pipeline/hrc_<current_token_first8>. Runtime checkout stays /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1; runtime_code_commit is its freshly observed exact HEAD, not automatically the candidate's source commit. Do not sync or modify an active root to stage diagnostics. Candidate sources are loaded from the hash-bound staged candidate_model under their exact independent package name.

The lease must carry project=cluster_project, thread_id=01a159c5-29ab-7a22-ba7f-e79174757253, native_manifest_sha256, token, generated_at, deadline_at, server_id=server-4, physical_gpu, gpu_uuid, allowed_gpus, goal_sha256, context_sha256 and pending_sha256. All fields must match the fresh manifest and current owner; no older tick binding may be copied. The owning root must verify current authorization/allowed cards, pinned server identity and current empty registry/queue/process state for the selected card. Existing protected/external jobs must not be stopped or displaced.

The runtime itself requires server4 hostname dl04-MS-7E06, only physical0/1 with their fixed UUID map and current allowed_gpus membership; manifest/lease hash/token/generated/deadline/context equality; a generated-to-deadline window <=3600 seconds and 300<actualremaining<=3600. It independently queries the selected physical index/UUID and requires no contexts/low memory/utilization before locking, acquires all original training/diagnostic/exclusive nonblocking flock files for that same physical card, checks idle again, rehashes all source/data/pretrain/native-train/lineage/diagnostic assets and exact runtime HEAD, then sets CUDA_VISIBLE_DEVICES to that card UUID. It never relies on stale preparation resource observations. Any occupied card or lock failure aborts without sharing, eviction or fallback.

Assets in the template are frozen known hashes from the reviewed protocol, not new remote observations; future runtime verify must recheck them. The local static validator does not verify unavailable remote data/checkpoints, runtime imports, locks or GPU behavior.

## Local static verification

    python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_86e41faa/hrc_native_prepare/validate_static.py

It only parses/compiles text, compares committed/staged source and YAML hashes and audits guard/probe/resource AST contracts; it imports no model or torch. Results and final file hashes are in preparation.json/static_validation.json. No production sources or shared ledgers are edited. These static checks and independent reviews do not constitute native/resource admission.

## Intentional remaining execution work

Fresh owner-side manifest/lease/stage binding and actual paired native smoke/resources are not implemented/executed by this bundle. No controller is supplied or implicitly authorized; use the existing owning-root guarded stage/dispatch workflow. Compare the actual two TRAIN batch fingerprints and predict input fingerprints across candidate/control, inspect real gradient/reference/probe/results, profiler unsupported operators and resource constraints, then generate admission only from complete evidence. Pure TRAIN memory support, if needed, requires a separate clean process pair.
