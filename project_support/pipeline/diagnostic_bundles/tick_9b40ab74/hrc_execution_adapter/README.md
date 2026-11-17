# HRC execution adapter — prepared locally, not executed

This bundle supplies the previously missing owner-side orchestration for M208-HRC / hierarchy-bottom-up-refined-token-composition. It references frozen model commit 9e543af623acd7fa9bd4a3f81ce79c932e98774a and the unchanged tick_86e41faa worker37782c1a/runtime4737e6f/template ea756a. No SSH, remote probe/stage, model/torch import, GPU/native computation, production execution binding/manifest/lease, shared ledger/queue edit or Git commit was performed during this preparation. All simulated requests/results/leases in tests live only in disposable fixture subdirectories and are removed after tests.

## External trust anchor before future use

adapter_release.json records the final adapter.py and remote_ops.py hashes. _release_details verifies only their internal consistency. It does NOT prove the release has been reviewed: someone able to replace source and release together could satisfy that check. Before any real invocation, the verified current root must compare the exact release AND preparation SHA256 against the references saved outside this bundle in the HRC candidate's evidence/authorized handoff, then verify source hashes. Do not treat this README, a self-reported hash or a rewritten release as that external anchor. The root will attach those immutable references when recording this preparation; this adapter deliberately does not edit that candidate record or create a circular self-hash gate.

Frozen preparation SHA: 4754db1a1c550c869596e0ca57cee99834239e8ed78e87ec65f68142f48c812a. The old preparation's token/deadline remain historical provenance. They are never rewritten to authorize a future execution.

## Future CLI (owning root only)

The following are future operations after external anchoring and real resource availability, not commands executed by this preparation:

    python -B adapter.py probe --gpu 0
    python -B adapter.py prepare --gpu 0
    python -B adapter.py stage
    python -B adapter.py pair

Physical --gpu may be 0 or 1 only and must be currently authorized. `prepare` runs a fresh read-only probe and refuses busy/locked/registered/reserved cards before creating any active execution files. If successful it exclusively creates the current `pipeline/diagnostic_bundles/tick_<current-token-prefix>/hrc_execution/` directory with prepare_request, native_manifest, execution_lease and a SEPARATE execution_binding that references the frozen preparation SHA. The remote stage is exactly `/data/songcl/Project/Cluster_project/pipeline/hrc_<current-token-prefix>`; no _r2 suffix, stale deletion or overwrite is supported.

`stage` stages only the 11 exact frozen diagnostic/model/YAML assets plus fresh manifest/lease into that new isolated remote stage and verifies hashes/lineage/runtime HEAD using CPU-only checks. It does not sync or alter the active runtime checkout. The candidate source commit remains 9e543af; runtime_code_commit separately records the freshly observed exact HEAD of the frozen known runtime root.

`pair` sequentially invokes four separate guarded processes: smoke/champion, smoke/candidate, resources/champion, resources/candidate. It is equivalent to these explicit calls:

    python -B adapter.py run --mode smoke --target champion
    python -B adapter.py run --mode smoke --target candidate
    python -B adapter.py run --mode resources --target champion
    python -B adapter.py run --mode resources --target candidate

Each step rechecks current owner/remaining time, candidate eligibility, canonical local slot state, fresh selected-card identity/idle/locks and unchanged runtime HEAD. A run needs more than 1020 seconds left; four such individual gates do not guarantee all four fit in one tick. The lease/deadline is never extended. If time expires or any prerequisite changes, preserve partial evidence and stop.

## Exact read-only recovery, including later ticks

    python -B adapter.py status --execution-dir <original-local-execution-directory>
    python -B adapter.py reconcile --execution-dir <original-local-execution-directory> --request-id <original-request-id>

status/reconcile require the CURRENT actual owning thread/environment/execution-mode/context/goal and the same pinned project/server/root contract. They may inspect an expired prior binding in a later tick without renewing or rewriting it. They do not require its old token to equal the current token and do not start a worker, acquire execution locks, kill a process or clear a hold. Mutating stage/run require the complete original six-field owner record to match the current owner exactly, plus current server authorization; the read-only path cannot make an old binding executable.

The adapter stores every mutation request before contacting the server. Requests are never replayed, even if a previous reply was missing. SSH timeout/nonzero, malformed/wrong-identity reply or remote subprocess uncertainty triggers a separate exact read-only reconciliation and then stops. A previous uncertain request also blocks further pair steps. Recovery exposes the original stage/manifest SHA, request ID/file SHA, mode/target, started PID, /proc start_ticks and exact argv, completed/result identity checks and GPU contexts. PID reuse, wrong argv, wrong mode/target/commit or missing artifacts are reported as identity false/unknown. Missing files or a disappeared PID do not prove the operation never ran.

Remote run writes its durable request, launch PID/identity and stdout/stderr files before waiting. Popen.wait timeout does not call kill/terminate or relaunch; the frozen worker retains its own alarm. The adapter has no automatic uncertain-result acceptance/unblocking path: the root must inspect the exact evidence. It cannot restage/retry the same request or refresh the old lease. A fresh later-tick binding, if still authorized and eligible, uses a genuinely new stage and retains old failure history.

## Mutation guards retained

- Actual CODEX_THREAD_ID = owner.thread_id = execution_mode.target_thread_id = the fixed owning HRC thread; foreground mode; current token, generated/deadline window and actual remaining time; exact goal/context/pending hashes and authorization source hash.
- closure_policy.enabled and experiment-first enabled; current server enabled and dispatch_enabled; live whitelist/max1 equal this tick's snapshot server4 resource authorization. Only the fixed server4 host/hostname/runtime root and physical0/1 UUID map are accepted.
- The current HRC record must retain exact ID/M208-HRC/9e543af/goal/config/authorization and be validation, or resource/exclusive_gpu_slot blocked with resume_stage=validation. Training/complete/rejected/closed, human/scope/numerical/dispatch holds and implementation-revision changes are refused rather than bypassed using old preparation.
- Canonical running/claiming tasks and waiting tasks with pending_progress or canonical Interrupted claim;/Launch uncertain;/Process observed launch holds reserve a physical slot. int0 and string0 mean the same GPU. Missing/None/bool/invalid/whitelist-external assignment on those reserved tasks is uncertain and blocks. Ordinary waiting tasks, including unassigned/dependency/non-launch holds, do not reserve a physical slot or suppress independent diagnostics; canonical begin has already attempted dispatch, and a race is caught by fresh probe plus the native exclusive locks. Launch-uncertain requests are not treated as empty because NVML is momentarily idle. The adapter does not change scheduler state or take another task's slot.
- Parent/child manifest, lease and binding contents are reconstructed exactly from frozen template plus current binding, not just compared by their claimed hashes. The original runtime still performs pinned physical index/UUID checks, all three nonblocking training/diagnostic/exclusive flock acquisitions, idle observations before/after locks, fresh deadline/manifest/lease checks and all asset checks before importing torch/CUDA.

The server performs fresh-deadline/idle checks before any stage/Popen as well. Existing/foreign jobs, shared code, stale stages, checkpoints and queues are never deleted, reset, stashed, migrated or stopped.

## Native result boundary and intentional missing piece

The adapter saves RAW four worker execution objects with request/result identities. Its orchestration success/returncode/execution_completed checks are NOT scientific admission, do not fully validate raw native semantics or candidate/control pairing, and do not create a standard native_smoke JSON, a resource PASS summary, admission receipt, queue item or launch. Formatter/admission_ready are explicitly false. A future root must still review the true candidate two-loss/two-backward/optimizer/FFN/mean/dependency observations and control expectations, compare the two TRAIN batch fingerprints and identical resource input/handler/protocol evidence, then generate standard smoke and receipt via the established closure workflow. No fake/empty/preparation object may stand in for executed evidence.

The unchanged resources function uses original fvcore handlers, bs1/lang1, warm20/repeat100 and no smoke observer/probe. Smoke peak memory includes diagnostic/probe overhead and cannot sign pure TRAIN memory. Pure TRAIN memory support remains UNKNOWN; it is not a new admission gate. Efficacy remains UNKNOWN until formal training.

## Actual offline checks

    python -B -X utf8 -m unittest -v test_adapter_review test_remote_ops_offline
    python -B -X utf8 validate_static.py

Independent adapter fixtures plus remote process mocks cover owner/deadline/whitelist/policy/dispatch/candidate holds, queue GPU formats/uncertainty, successful four-step pair order, busy/lock refusal without leases, old-binding read-only recovery, trimmed binding fields, request replay prevention, incorrect request/result/PID identity and timeout without kill/restart. The initial fixture test failure (missing mocked /proc) was fixed in the fixture; no real remote process was contacted. Earlier meaningful implementation findings (GPU string comparison and cropped owner schema) were fixed and rerun; review artifacts preserve them. All local fixtures explicitly inject transport/clock/env and do not impersonate an owner against production paths.

Final hashes, actual command/results and independent review are recorded in preparation.json, static_validation.json and independent_review/. No production active binding or native evidence is included.
