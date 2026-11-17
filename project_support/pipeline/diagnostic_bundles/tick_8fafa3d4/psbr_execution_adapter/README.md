# M209-PSBR execution adapter preparation

**PREPARED_UNEXECUTED_EXTERNAL_ANCHOR_REQUIRED.** This is an orchestration source
port, not execution, native evidence, paired validation, admission or a queue entry.
No SSH, GPU, torch, remote probe/stage/run, production binding/manifest/lease or
shared ledger mutation occurred in preparing it. All native/resource/efficacy
results remain **NOT_RUN / UNKNOWN**.

The only core implementation differences from the frozen reviewed HRC adapter
(`adapter.py` 0f0663ec..., `remote_ops.py` 3b914701...) are candidate/path/string
constants. The complete replacement list, old hashes and occurrence counts are
in `port_provenance.json`; exact transformed-source and AST checks prove no
additional guard/control-flow changes. Old HRC code, fixtures, historical reviews,
results, leases and native package remain unchanged. The PSBR tests were rerun
independently; old passing outcomes are not reused as new outcomes.

PSBR stable ID is `hierarchy-parent-segmented-bidirectional-token-state`, experiment
M209-PSBR, commit `74fcd21df0af9a971792038ffe251af1ffea2604`, and native config/package
end `_ctf_hcg_csort_psbr`. FROZEN points to this tick's separately frozen PSBR
native preparation SHA `1e1de105f34ce4f6f87fe862bf35ee2c7c0bf26bf7404b0550559534a0e7472e`,
worker 05ab6ac1..., runtime b6698c77..., and template f90e2662.... Every prepared
file and all staged diagnostic files are rehashed by the unchanged source guard.

## External evidence anchor is mandatory

Before invoking this program, the actual owning root must save and independently
compare this exact `preparation.json`, `adapter_release.json`, adapter and remote
source hashes against externally stored candidate evidence/handoff. The parent
owns those ledger writes. `_release_details` checks internal file consistency
only; it does **not** prove prior review or authorization, and it does not enforce
a `candidate.execution_adapter` external anchor itself. Do not treat this release
as a self-signed execution permit. No circular self-hash or weaker fallback was
added. The actual-owner guard must be reached with the real current environment;
a child/test environment cannot authorize production execution.

This adapter supplies probe -> prepare -> stage -> four raw runs and precise
read-only status/reconcile. It creates no active binding/manifest/lease on import.
`prepare` can create them only after real current actual-owner/context/deadline,
current candidate/policy/authorization/server/snapshot checks and a verified idle
card. The local execution output is a fresh current tick's `psbr_execution`
directory; remote stage is `psbr_<current-token-first-eight>`. Neither is this
preparation directory. Old preparation tokens are provenance, never fresh leases.

## Preserved safety and recovery contract

All original mutation safeguards remain: actual root thread/environment/execution-mode
identity; exact current goal, owner, context and pending hashes; unchanged real
deadline; enabled experiment-first/closure, server and dispatch; exact server4
host/hostname/root; allowed physical GPUs 0/1 and UUID map; snapshot/live whitelist
and max-one-task-per-card equality; current PSBR ID/config/74f/version/authorization;
validation or eligible resource-blocked lifecycle; no human/scope/numerical/revision
hold; and immutable native sources/release hashes. No authorization or scheduling
policy was widened.

Running/claiming tasks and waiting tasks with pending-progress or canonical
launch-uncertain holds reserve a card. Unknown/illegal/outside-whitelist GPU
assignments on those reserved tasks block conservatively, including string/int
GPU equivalence. Ordinary waiting, unassigned or dependency-held tasks do not
reserve a physical slot. Canonical existing work still has priority; fresh remote
NVML and three independent physical-card lock checks protect later races.

Prepare/stage/run reject busy GPUs, unknown identities, old mutation bindings,
insufficient real remaining time or changed source/runtime HEAD. A read-only probe
may report busy and creates no binding; its observation does not authorize a
mutation. Preserve active
HAP/CGCA/foreign jobs; there is no kill, eviction, migration, cleanup, reset,
checkout, synchronization, schedule change or lease extension operation here.
Native runtime retains acquire-before-torch, exact UUID/environment agreement,
three flock locks, dual idle observations and original asset checks. Candidate
commit and actual independently observed runtime checkout HEAD remain distinct.

Current thresholds are inherited unchanged: prepare requires >360s, stage >420s,
and each raw worker run >1020s remaining; native worker itself has its own shorter
alarm. Remote wait is 660s and transport timeout 900s. These are per-operation
bounds, not a guarantee all four runs fit one tick. Never extend the original
deadline or call a deadline shortage a GPU shortage.

An SSH/local timeout, nonzero, malformed reply, missing local result or missing
completion is uncertain. Read-only reconcile reads the exact original stage,
request ID, mode/target, manifest, logs, PID start ticks and fixed worker argv;
it distinguishes expected started/completed/raw-result identities. Existing
requests are never replayed or stale files deleted. Same PID without matching
start ticks/argv/request is not proof. Under a fresh actual current owner,
read-only status/reconcile may inspect an old same-project/PSBR binding past its
deadline. It never renews the old lease or makes old stage/run mutations legal.
`--local-only` lists local records only and cannot establish remote termination.
No uncertainty is silently converted into PASS or absence of execution.

## Future entry points, not executed in this preparation

After external anchoring and actual-owner/resource authorization:

```text
python -B adapter.py probe --gpu 0
python -B adapter.py prepare --gpu 0
python -B adapter.py stage
python -B adapter.py run --mode smoke --target champion
python -B adapter.py run --mode smoke --target candidate
python -B adapter.py run --mode resources --target champion
python -B adapter.py run --mode resources --target candidate
python -B adapter.py status
python -B adapter.py reconcile --request-id <exact-original-request-id>
```

Choose only an actually authorized idle physical GPU; these GPU0 examples are
not an idle claim. `pair` performs the same four raw runs sequentially. It is not
a pairing comparator. `--execution-dir` supports exact older diagnostic output
for read-only recovery; mutation writes remain confined to this current tick's
canonical `psbr_execution` directory. Each command must retain real deadline and
current ownership. None was executed here.

## Raw-result and admission boundary

`run` requires exact base identity/model package, terminal returncode zero and raw
`execution_completed`. That is process/result provenance only. Full native losses,
criterion backwards, optimizer/Wh/Wx/Wo gradients/updates, actual parent-domain
observations, input paths and resource measurements still need semantic review.
The native worker's own specific assertions do not replace cross-result pairing.
The adapter does not manufacture or default semantic flags to true.

No standard `native_smoke` formatter, common-parameter/two-TRAIN-batch/resource
pair comparator, receipt, candidate admission, queue write or dispatcher is
implemented. Both actual complete native batch fingerprints and common named-
parameter names/count/hash must be compared across real champion/candidate
results. Standard resource pairs need actual same-input signatures, original
handler files/unsupported reports and all 100 measured values. Offdiagonal/Jacobian
probe remains NOT_IMPLEMENTED in the frozen worker; generic source coupling is
not a measured native derivative. Smoke peak includes diagnostic observers and
is not pure TRAIN memory, which remains UNKNOWN without a separate support run.
No new pure-memory or probe admission requirement is introduced by this adapter.

## Offline validation

Run from this directory:

```text
python -B -X utf8 -m unittest test_adapter_review test_remote_ops_offline
python -B -X utf8 validate_static.py --write
```

31 newly executed mocked orchestration fixtures cover old identity/context/hold,
deadline, busy/lock, unknown/reserved GPU, ordinary-waiting, uncertainty/no-replay,
cross-tick read-only recovery, original request/PID/argv/result identity and the
successful mock four-run path. They use disposable fixture directories and mocked
SSH/NVML/processes, not the production root/locks or GPU. Passing fixture flags
are simulated test data, not native smoke evidence. Tests do not import torch.
Static checks additionally compare the complete allowed source transformation,
release/native file hashes and unbound/no-live-artifact boundary. Root's actual
current-owner prepare integration is separate, and should refuse both cards while
the existing trainings still occupy them before transport is invoked.

Independent reviews are external artifacts anchored by the parent after this
preparation freezes; the frozen preparation is not rewritten to hash a review
that itself hashes that preparation.
