# HRC HEAD74f execution adapter — prepared, not executed

This new bundle forward-binds the unchanged M208-HRC mechanism to source commit 74fcd21df0af9a971792038ffe251af1ffea2604. Commit9e to74f adds only the independent nine PSBR files; HRC nine source/config bytes and all preexisting tracked blobs/modes are identical. See the native commit_lineage.json. The old native/adapter preparations and results remain immutable historical provenance.

The only core changes from the frozen HRC adapter are adapter.FROZEN/PREPARATION_SHA/TEMPLATE_SHA/COMMIT and remote_ops.COMMIT. All method/function ASTs, guards, candidate ID, M208-HRC, HRC package/YAML, selected-card identity, 3-lock/dual-idle checks, request persistence, uncertainty/no-replay/reconcile behavior and original worker/resources/RNG/probe logic remain unchanged. The two31-fixture source files are exact old bytes, but the new package has its own actual offline validation results. Old mock/static PASS is not inherited as a new result.

The frozen native preparation is pipeline/diagnostic_bundles/tick_37695e94/hrc_native_prepare_head74f, SHA 87ef65ab7ac065688879bc0587a26ef1704d001a8190086ba55b2d005f6ae8e1. It has current owner preparation metadata and null execution fields. Neither historical nor current preparation timestamps are an active execution lease.

Before actual use the verified owning root must compare exact preparation.json and adapter_release.json hashes against externally saved candidate evidence. _release_details checks internal consistency only: replacing source and release together could satisfy it. This bundle does not edit candidates/queues or create its own external trust anchor. Future owner must use fresh current token/context/deadline, current allocation and idle resources. GPU1 remains unavailable to this task under the current GPU0-only human allocation, even though the unchanged capability map supports physical0/1.

Future root CLI after external anchoring and actual resource availability:

    python -B adapter.py probe --gpu 0
    python -B adapter.py prepare --gpu 0
    python -B adapter.py stage
    python -B adapter.py pair

probe may observe busy, while prepare/stage/run refuse busy/locked/registered/reserved cards and stale/wrong ownership or authorization. No production invocation of these commands was made in this preparation. The execution directory remains tick_<currenttoken8>/hrc_execution and remote stage hrc_<currenttoken8>; exclusive creation and replay refusal remain in force. Existing stages/bindings are not deleted, renamed, overwritten, restaged or renewed. A fresh later token is required when a prior stage already exists.

The guard retains current owner/environment/context/pending/goal/human authorization, policy, whitelists/max1, exact candidate/commit/config and human/scope/numeric/dispatch holds. Ordinary waiting does not reserve a slot; claiming/running or canonical waiting uncertainty does. Three exclusive locks and two idle observations precede torch/CUDA. Remote mutation requires remaining unchanged deadline, exact request/manifest/runtime identities and fresh idle checks. An SSH timeout/malformed/nonzero reply remains uncertain; readonly exact request/PID-startticks/argv reconciliation reports it and never retries, kills, or renews an old binding.

pair invokes four raw workers sequentially: smoke/champion, smoke/candidate, resources/champion, resources/candidate. Every step rechecks deadline/ownership/resources; the original >1020-second run gate is unchanged, and four gates do not promise all work fits one tick. Native train uses the original YAML/pretrain and two real TRAIN batches. The unchanged resources function uses original fvcore handlers, bs1/warmup20/repeat100 and unsupported disclosures. Smoke peak includes observer/dependency-probe overhead; pure TRAIN memory is UNKNOWN, not a new gate.

The saved raw execution_completed/returncode/identity checks are not full native semantic or sample/batch/input pairing validation and are never an admission PASS. No standard result formatter, native_smoke/resource PASS, receipt, queue item or dispatcher action is implemented. Future root must review four true results, candidate loss/backward/optimizer/FFN/mean/dependency controls, unchanged common initialization, two TRAIN fingerprints and identical resource input/handlers before established standard summaries/admission. Native smoke/resources/pairing are NOT_RUN and efficacy UNKNOWN.

Actual offline commands (results saved separately):

    python -B -X utf8 -m unittest -v test_adapter_review test_remote_ops_offline
    python -B -X utf8 validate_static.py

All tests inject fake transport/process/NVML, fixtures and clocks inside disposable directories under this new bundle. No SSH, torch/model import, GPU, /tmp production locks, production lease/staging, shared state or old artifact mutation was performed. Fixture source and actual31-run evidence, exact source hashes and port provenance are recorded in preparation.json. Future root still needs external anchoring.
