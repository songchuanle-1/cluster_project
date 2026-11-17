# PSNC operational preparation — unexecuted

Candidate hierarchy-parent-spectral-nonlinear-token-coupling / M210-PSNC is bound to actual independent source commit43dce016c1a1713c2a5dab7061810dc2efde8954, direct child of74f. The nine added source/config Git blobs were read and checked against the original frozen PSNC preparation302432f1. Main Cluster HEAD and empty index remain74f; its28protected status entries and active remote checkout are untouched. HRC and admitted PSBR74f FIFO are preserved.

This is a new version-bound operational packet. It is not the old disabled draft with an old lease replayed. The model9bytes and whole native worker69e2 are unchanged; the new runtime verifies the Git-derived source_version_binding against its fixed commit/source map and manifest before assets, and only physical server4 GPU0. The native runtime checkout HEAD is separately observed at prepare and verified before each stage/run; it may remain74f while the independent candidate package43 is staged by hash. No synchronization/checkout modifies that active root.

Implemented API: Adapter.guard/probe/prepare/stage/run/pair/run_pair/status/reconcile. Importing the module connects nowhere. probe/prepare require explicit physical0. The full chain reads the actual foreground owner/environment/thread/mode, current context+pending hashes, unchanged deadline, project/native-check authorization, candidate43/config/goal/eligible state and scoped holds, current server dispatch+snapshot whitelist/concurrency, and frozen native packet. It pins songcl@192.168.1.115, strict SSH host keys, expected hostname dl04-MS-7E06, fixed root and GPU0 UUID958e741a. GPU1 is rejected before inventory. Registered/claiming/running/launch-uncertain occupancy, two real idle checks and three native locks remain protected; ordinary unassigned waiting is not falsely reserved. Canonical begin/FIFO policy remains the owner's responsibility.

The adapter uses original successful PSBR guarded transport/staging/run/reconcile. Mutation binds a fresh original current owner6fields, manifest SHA, lease SHA, physical GPU/UUID, runtime HEAD and request ID. Each remote run verifies stage/assets/source, original request identity and idleness before starting the original worker; the worker acquires locks and verifies again before torch. No stale request is replayed, deleted or killed. Timeout is uncertain rather than proof of death; exact original request/mode/target/PID/start_ticks/command/result identities are read-only reconciled before further mutation. Full raw results are kept; this adapter does not format standard PASS, receipt, queue, or task efficacy.

The module/preparation/release are reusable across ticks. prepared_under_parent_token/generated/deadline in preparation are historical provenance only and are not compared to the next current owner. All actual operation-time identity/deadline/policy/GPU fields are read fresh. New prepare creates a new tick directory and binding. Explicit old execution_dir allows current-owner read-only status/reconcile of an old binding even after its lease deadline; mutation still requires exact current owner/token/context/deadline and cannot renew/replay an old lease. `status --local-only` is a local summary, never proof the remote request did not run.

Static release is a reviewed module/version hash catalog, NOT a fresh execution lease, human authorization, GPU grant or idleness proof. This preparation contains release_template.json and no adapter_release.json. `_release_details` requires a materialized catalog exactly matching the template, all source hashes, and external current candidate.execution_adapter.preparation+release exact path/SHA anchors. The entire externally anchored preparation file map is checked. Current policy authorization and fresh owned lease remain independently required.

After independent review, the owning root may safely materialize only the static catalog with an exclusive local copy (no remote/lease effects):

    from pathlib import Path
    origin=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_42ce600b/psnc_operational_prepare')
    with (origin/'adapter_release.json').open('xb') as stream:
        stream.write((origin/'release_template.json').read_bytes())

Its expected SHA is the exact release_template SHA. External candidate.worker_preparation.preparation must point to native/preparation.json (not this root preparation); candidate.execution_adapter.preparation points to root preparation.json, and .release to root adapter_release.json. No active release was automatically materialized by this package. These refs are source review anchors, not new human permission prompts.

Minimal owning-root actual local guard integration after those static anchors exist:

    import importlib.util
    from pathlib import Path
    origin=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_42ce600b/psnc_operational_prepare')
    spec=importlib.util.spec_from_file_location('psnc_adapter', origin/'adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    class NoTransport:
        calls=0
        def call(self,*args,**kwargs):
            self.calls+=1
            raise RuntimeError('Transport disabled for local guard audit')
    transport=NoTransport()
    try: module.Adapter(transport=transport).prepare(0)
    except module.Refused as error: print(str(error))
    assert transport.calls==0

Do not override CODEX_THREAD_ID. With the actual candidate eligible for validation/resource block and HRC registered on GPU0, prepare rejects in _local_idle with `Selected GPU has registered running task`, before probe, mkdir, manifest or lease. If policy/identity/anchors/holds are not ready, an earlier refusal is correct and must be reported as observed, not bypassed to force that message.

Future actual commands, only when current owned guard and physical GPU0 are truly idle:

    python -B -X utf8 adapter.py probe --gpu 0
    python -B -X utf8 adapter.py prepare --gpu 0
    python -B -X utf8 adapter.py stage
    python -B -X utf8 adapter.py run_pair
    python -B -X utf8 adapter.py status --execution-dir <original-local-execution-directory>
    python -B -X utf8 adapter.py reconcile --execution-dir <original-local-execution-directory> --request-id <original-request-id>

Native source verifies the original asset hashes/backbone pretrain and exact staged package, then original M95/candidate TRAIN2. Standard resources remain bs1/lang1/warm20/repeat100 with unchanged historical fvcore handlers and full unsupported dictionaries. No dropout/precision/tolerance, source9bytes or worker69e changed. Actual native/resource/transport are NOT_RUN; pure TRAIN memory and task effect remain UNKNOWN. Future four raw results still need semantic review/pairing and independent constraints before canonical summaries/admission.

Offline evidence: independent_offline_run_v1.json records40actual mocked orchestration cases (old31 plus GPU0/user/release boundary cases); packet_static_validation.json adds11version/hash/command-construction checks with network/process audit events0. Their simulated leases/releases are temporary fixtures, not production execution artifacts. independent_test_port.json is the earlier migration snapshot, not final pass evidence. Do not interpret offline checks as native PASS. Peer reviews live outside this frozen map to avoid cycles.
