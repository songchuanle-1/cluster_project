# Executable Closure Contract

For a snapshot with experiment_first.enabled=true, use experiment_first.md
for admission and bounded research completion. Its explicit authorization
replaces only the old scientific pre-admission and repeated operation approvals.
Native YAML configs, hard resources/data/bans, append-only revision evidence,
receipt identity, safe sync and verified native progress remain mandatory.
Receipts without profile=experiment_first retain the original gates below.

Enabled by project pipeline/closure_policy.json. Existing running experiments
are not retroactively rejected. New waiting entries require admission receipts.
Never lower goal constraints to satisfy this operational contract.

## Durable Work

Maintain pipeline/research_work.json as:

```json
{
  "schema_version": 1,
  "candidates": [{
    "id": "stable-hypothesis-id",
    "stage": "validation",
    "next_action": "Run native TRAIN capture and persist component incidence",
    "evidence": [{"path": "pipeline/reports/result.json", "sha256": "<sha256>"}]
  }]
}
```

Stages: diagnosis, design, implementation, validation, admission, deployment,
training, complete, rejected, blocked. Keep the same ID when advancing an
existing idea.
Event mode MUST continue due work even when candidate budget is zero; it does
not authorize extra training or override a goal-phase hold. Complete the next
executable validation before starting another review of the same hypothesis.
When due work and capacity-gap design are both ready, use design mode, resume
due IDs first, and continue the admission loop within the same tick. Candidate
budget limits new admissions, not the number of distinct diagnostic attempts.
The per-tick target is candidate_budget, not every open GPU slot. Postflight
compares queue identities against the begin snapshot, checks receipts for new
admissions, and rejects additions above that budget. Reactivating an inactive
historical queue ID counts as an admission; dispatching an already waiting task
does not. Newly archived experiment IDs still consume the budget. A receipt file
or ledger stage alone is not admission: the task must actually be queued on an
authorized dispatch server. Existing native-progress verification still applies.
Successful same-tick archives also count toward quota, once per experiment ID.
Finalization retains code_commit, admission_receipt and the current run's launch
proof before removing the queue entry. Credit requires completed archival,
done_complete/done_earlystop, verified launch and valid receipt/gate hashes on an
authorized server. Crashed, unknown or incomplete archives do not earn success
credit; historical archives do not count toward a new tick. Missing proof is not
inferred from a filename or an older run.
During an acquired foreground tick, the gated dispatcher also checks the bound
snapshot budget before syncing or launching a new admission. Fresh preflight
does not reuse the previous tick's budget; already queued work retains its place.
An unsuccessful gate or a stage transition alone must not end the tick while
another executable test or independent evidence-backed hypothesis remains.
Stop at admission target, exhaustion of defensible alternatives, external
blocker, goal-phase hold, or the tick time limit; record evidence and resume
conditions for anything unfinished. Never fabricate a PASS to fill capacity.
Stage training requires queue launch_verified=true and native step evidence.
Rejected requires concrete disconfirming evidence; do not reopen under a new ID.
Blocked requires blocker, retry_after (timezone-aware ISO date), unblock_condition
and evidence of attempted alternatives. Missing native capture is executable work,
not an external blocker. Derivation and literature review are recommended research
support, not dispatch blockers. Record their limitations honestly and never assert
novelty from an empty search.
An exclusive native diagnostic may be blocked only after its non-GPU work is
complete and every authorized GPU slot is occupied. Record
`blocker_kind: "exclusive_gpu_slot"` and `required_server` on the stable ID,
with the frozen manifest and occupation evidence. The context builder skips
repeated research invocations while the queue remains full and wakes it on a
queue opening, regardless of retry_after; the diagnostic runner must still
verify live GPU idleness and acquire its exclusive lease. Missing evidence,
an unknown GPU assignment, or an actually available slot cannot justify a
fake block. A queue opening never grants training admission.
When a queue opening exists but foreign compute or graphics load occupies all
authorized devices, postflight accepts only a fresh `exclusive_gpu_occupation`
observation collected with `gpu_occupation.py <project> --token <token> --server <server>`.
The proof and original raw query log must be hash-bound to the candidate,
current foreground token/snapshot, server identity/configuration and exact GPU
whitelist. Both GPU/compute queries must succeed and include every authorized
device; observed utilization, memory, compute PIDs and canonical reservations
determine availability, not a claimed summary. Evidence must be within this tick
and at most five minutes old. Missing/stale/unknown observations or any available
authorized device still reject a resource block. Collection is read-only on the
server and does not change jobs, hardware, admissions or scheduling.
For a capacity-gap design tick with no admitted variant, persist each testable
unfinished route under one stable ID with a concrete next diagnostic or resource
test. Run available tests immediately; subsequent event ticks resume the same
ID before starting another review. Reject a realization only with disconfirming
evidence, not because a required test has not yet run.
When `mode=design` and `candidate_budget>0` with no due IDs, candidate creation
is itself the first durable action: write a stable `diagnosis` candidate before
broad route review or abort, then execute its first discriminating test in this
tick. Conceptual similarity to a closed family is not disconfirming evidence;
only a reproducible test result can support rejection. A review that creates no
candidate progress cannot be reported as route exhaustion.
No new evidence/stage change fails postflight; timestamp-only edits do not count.
Hashes establish artifact identity, not scientific validity.

### Focused Work And Carryover

After the tick's receipt-backed admission quota is met, or within 180 seconds of
the original deadline, unchanged executable backlog may be carried to the next
tick without manufacturing per-candidate progress. Keep every candidate's stable
ID, evidence, stage and specific next_action; record this small object in
research_work.json only when carryover is needed:

```json
{
  "tick_handoff": {
    "tick_started_at": "<exact context.generated_at>",
    "reason": "admission_budget_met",
    "candidate_ids": ["unchanged-stable-id"],
    "resume_condition": "Resume the saved next_action in the next owning tick"
  }
}
```

The other allowed reason is tick_deadline_near. List exactly the old executable
candidates whose stage/evidence did not advance, not blocked/terminal/new IDs.
Old tick handoffs are history and cannot authorize a new deferral. Handoff requires
real progress elsewhere in this tick, never an entirely unchanged design cycle.
Postflight still validates all artifact hashes, revisions, limits and launch
proof. It does not silently remove or complete the backlog; the next tick resumes
it normally. Before quota/deadline, continue the selected candidate instead of
touching every pending ID merely to satisfy bookkeeping.

When `research_on_capacity_gap` is true and the design tick still has an
unfilled whitelist slot and has not met its own admission quota, postflight requires an actionable unfinished
candidate, or `research_work.design_cycle` with `stop_reason` (one of
`independent_routes_exhausted`, `external_resource_blocked`,
`tick_deadline_near`, `goal_phase_hold`, `no_information_gain`), `attempted_ids` including a
candidate advanced in this tick, hashed `evidence`, and a concrete
`resume_condition`. A failed screen alone is not evidence that all routes
are exhausted. The agent must substantiate the chosen reason in its
review/report; this structural check does not certify the scientific claim.
`tick_deadline_near` requires the scheduler's deadline_at to be within 180
seconds; `external_resource_blocked` requires a durable blocked candidate
with retry/unblock conditions. The local scheduler continues a capacity-gap
postflight failure within the remaining tick window when research state
changes, and marks it unhealthy if it cannot make progress.
At the deadline boundary the scheduler runs postflight against the existing
report and research ledger once more; a valid deadline disposition is not
mistaken for a model timeout. The stop_reason is the exact machine-readable
value `tick_deadline_near`, with details in the report and resume_condition.

### Evidence-Based Early Stop

`no_information_gain`, or `independent_routes_exhausted` before the last 180
seconds, may close without waiting for the deadline. In addition to the fields
above, require `no_gain_reason`, a timezone-aware `retry_after` within the next
four hours, and `attempt_results` with at least two distinct candidate IDs and
two genuinely independent hypothesis IDs. Each result has `candidate_id`,
`hypothesis_id`, `test`, `result`, and hashed `evidence` created in this tick.
These candidates must have changed evidence/stage this tick and be rejected
with disconfirming evidence or blocked with true retry/unblock conditions.
No executable diagnosis/design/implementation/validation/admission/deployment
candidate may remain. Do not invent a resource block to avoid an available test.

```json
{
  "stop_reason": "no_information_gain",
  "attempted_ids": ["route-a", "route-b"],
  "no_gain_reason": "Describe what the two executed controls ruled out",
  "resume_condition": "Name the new evidence or resource condition to revisit",
  "retry_after": "<timezone-aware time within four hours>",
  "evidence": [{"path": "pipeline/analyses/review.md", "sha256": "<hash>"}],
  "attempt_results": [
    {"candidate_id": "route-a", "hypothesis_id": "mechanism-a",
     "test": "<actual test>", "result": "<observed result>",
     "evidence": [{"path": "<test evidence>", "sha256": "<hash>"}]},
    {"candidate_id": "route-b", "hypothesis_id": "mechanism-b",
     "test": "<actual independent test>", "result": "<observed result>",
     "evidence": [{"path": "<test evidence>", "sha256": "<hash>"}]}
  ]
}
```

Hashes and distinct IDs validate structure, not scientific independence.
Foreground finish saves an evidence-sensitive cooldown only after postflight
passes. The next tick still monitors/checks goal. Changes to goal, queue,
research artifacts or a due retry invalidate the short path; no-change ticks
reuse deterministic reports without another literature/design pass.
An active executable candidate also keeps the design tick open until the
deadline approaches: persisting a draft alone does not close the loop.
An independent-routes-exhausted assertion made while substantial scheduler
time remains is not accepted as a successful capacity-gap close. Continue
research in this tick; if no defensible route can be found by its deadline,
retain the negative evidence and report an honest incomplete result.

## Research Reserve

For closure-enabled, capacity-gap research projects, the context builder defaults
`goal.pipeline_policy.research_reserve_target` to 2. Explicit 0 disables it.
Preparation is enabled only with healthy preflight, goal return code 0, authorized
capacity and fill_to_capacity=true. It does not lift any textual research freeze,
project constraint or permission requirement.

The actionable reserve counts executable/unclassified pending IDs and already
waiting/claiming tasks once per experiment ID. Recognized human/resource holds
with evidence, blocker, next action, aware retry time and unblock condition are
parked separately; include human_revision_authorization in human holds. Parking
does not change their stage, authorize a revision or reopen a frozen direction.
Malformed/unknown blocks must be reviewed, not silently hidden.

The typed numerical_control_failure is also parked when its scope is
implementation/inconclusive, the same required hold fields exist, and its evidence
files and hashes verify. It is a research hold, never human/GPU permission or a
failed hypothesis. These IDs remain in the pending total and keep their frozen
controls and evidence. Recheck unchanged holds at most once per four hours;
changed evidence/wake_paths, goal or servers wake sooner. Missing or damaged
evidence returns the ID to review, not to silent waiting.

All unfinished IDs, including parked ones and queued tasks, count toward
goal.pipeline_policy.research_pending_limit (default max(8, 2 * reserve target)).
Training and terminal history do not count. reserve_budget is bounded by the
actionable target deficit, total pending headroom and max_candidates_per_design_tick.
Postflight rejects new unfinished IDs above the total limit; existing over-limit
records are preserved, never deleted or relabeled to create space. Zero pending
limit prevents new unfinished work, not advancement of existing work. Explicit
reserve target 0 disables reserve preparation and this reserve limit.
When reserve_only=true, candidate_budget remains 0: prepare source/CPU controls,
implementation and honest gate evidence without adding queue entries or launching
training. GPU diagnostics still require an actually available authorized lease.
No more than reserve_budget new stable IDs may be created in a reserve-only tick.
Do not demand a new train run or consume the full deadline to finish preparation.
Preserve a concrete next test and hashed evidence; a document-only review or
timestamp edit is not candidate progress. Finish after bounded preparation,
actual blockers, a phase hold or the real deadline.

With remaining preparation budget, candidate-specific external holds do not stop
independent authorized research. They also do not justify another copy of the
same blocked route. An external-block cooldown cannot hide available independent
reserve preparation; validated scientific no-gain cooldowns still apply.
When queued work fills the preparation target or the total pending limit is
reached, only blocked work means waiting: first/changed waiting is event mode,
unchanged waiting is steady. Due retries run event checks without requiring fake
candidate progress. Available executable work still advances. Force-design
cannot bypass the total limit, goal phase, permissions or science gates.
Human-only cooldowns are capped at four hours; resource/mixed cooldowns at two
hours, both bounded by the earliest retry. Terminal history never becomes pending.

Unchanged recognized resource blocks are rechecked at most once per hour;
human-evidence/authorization blocks at most once per four hours. Add project-local
`wake_paths` for actual intake/resource evidence files that can unblock a candidate.
Changes to those file contents, goal or servers wake earlier; resource queue
changes also wake earlier. An exclusive_gpu_slot block retains its existing
queue-opening behavior. Unknown blocker kinds retain their original retry rule.
Timers are a fallback, not evidence of release. Never kill, reset or delete locks
because a retry is due. A new candidate or changed evidence can still be handled
while an unrelated blocked candidate remains deferred.

## Implementation Revisions

Record the scope of a negative result:
- implementation: a particular layer, connection, initialization or implementation
  failed; the underlying mechanism has not been falsified;
- inconclusive: sampling, numerical uncertainty or incomplete evidence prevents a
  mechanism conclusion;
- hypothesis: a matched task-relevant test contradicts the core causal premise.

Novelty alone never gives admission. A small patch may be a legitimate realization
of the same novel mechanism without being a new contribution itself. Conversely,
a new name or an arbitrary numerical sweep is not a new mechanism.
For implementation/inconclusive outcomes, keep the stable ID in implementation or
validation with a bounded revision_history instead of declaring the whole family
rejected. Freeze a specific defect explanation, one local causal change and a
discriminating control BEFORE seeing its result. Default maximum is two revisions,
configurable by pipeline_policy.max_implementation_revisions. Lack of improvement
on a few untrained batches, or a local task-gradient conflict alone, is a risk
signal rather than population efficacy evidence. Investigate a reversal that
directly contradicts the mechanism; do not discard it or fabricate PASS.

```json
{
  "revision_history": [{
    "revision": 1,
    "failure_scope": "implementation",
    "reason": "The residual writeback bypasses the intended mask",
    "change": "Move the SAME writeback behind the validity mask",
    "prediction": "Invalid positions stay unchanged; the native new path still has gradients",
    "preregistered_at": "<timezone-aware time before the new test>",
    "failure_evidence": [{"path": "pipeline/reports/original_failure.json", "sha256": "<hash>"}],
    "result": "pending",
    "evidence": []
  }]
}
```

After executing the frozen test set result to passed/failed/inconclusive and add
hashed result evidence. Do not erase an earlier result, rewrite a frozen protocol,
change the hypothesis, or reset the revision count by renaming a candidate.

`evidence` is the append-only archive. When it includes source/protocol inputs
frozen before registration, set `result_evidence` to the nonempty subset of actual
test outputs after execution. All archive hashes still validate; every selected
output must exist in the archive and postdate preregistered_at. Do not touch input
timestamps or remove an input to satisfy the result clock. Legacy records without
result_evidence retain their original all-evidence timestamp check. A pending
revision can add this classification without dropping any prior evidence/results;
completed revisions remain immutable. This only fixes archival typing: a failed
test remains failed, and extra revisions, gate changes or historical reopening
still require their existing authorization.

A candidate may reference `implementation_revision_authorization` as a hashed
project-local artifact for one extra revision. The artifact must bind the verified
owner, explicit human reply, candidate ID, unchanged goal hash, default revision
count and digest of that completed history. Only `additional_revisions=1` is
accepted. This does not raise the project default, reopen rejected work, change
scientific gates or authorize a commit, deployment or training exception.
The begin snapshot also binds the authorization reference. An unchanged stage,
fully completed revision history and unchanged bound grant are historical records:
later goal, owner or default-budget changes do not invalidate their preservation.
All artifact hashes, grant identity and immutable outcomes still validate. A new
revision, changed stage, pending result or admission must meet the current scope;
an older snapshot without the grant binding does not receive this exception.

Recheck affected scientific, native, resource and independence gates for the
current code; every required gate must remain valid. A revised admission receipt
adds candidate_id and implementation_revision_sha256=closure.revision_digest of
the latest passed revision, alongside its existing goal/commit/evidence binding.
Old receipts cannot admit a newly changed realization.

An already rejected/closed historical candidate needs explicit, hash-addressed
human reopen authorization, even if it has no revision_history. This is checked
at postflight and against the owned snapshot before dispatch, not just during a
local revision. This generic revision policy is not reopen permission. Core-hypothesis
falsification, exhausted revisions, project bans and validation-based tuning are
not repair permission. Record what was falsified and what remains unknown.
Never silently reopen old families, select the best patch on validation, expand
training beyond current authorization, or alter ongoing runs.

## Admission Receipt

Write pipeline/admissions/<id>.json, point queue entry admission_receipt to it.
Required: id, config, code_commit (full git SHA matching queue and local HEAD),
goal_sha256, decision {path,sha256}, gates object. Required gate keys have
passed:true and nonempty evidence:[{path,sha256}]:
diagnosis, controls, native_backward, resources, independence, constraints.
Optional research-support keys are derivation and literature; missing or incomplete
optional keys do not block dispatch. Use real outputs; never convert unverified work
into PASS.
The agent still must conduct substantive scientific review and record limitations.
Commit tested candidate code before computing the receipt. Do not stage or commit
without user permission covering that operation and file scope. Existing explicit
project-level standing permission may be reused within its exact bounds; do not
invent a per-candidate approval requirement on top of it. Preserve unrelated work.
Metadata-only consent or a request to continue design is not code-commit consent.
When explicit commit permission is required, surface the exact candidate and
tested file bundle plus the requested operation once in the owning chat. Record
an unambiguous human confirmation under that project's authorization contract;
do not require a special phrase or a human-written JSON file. Local commit
consent does not grant push, admission or training permission. Conversely, do not
request those permissions again if they are already explicitly authorized in the
project scope; scientific checks verify evidence, not a new human approval at
every step. Never create or broaden a standing authorization from a heartbeat,
generic repair request or model-authored record. A blocked-action
table or repeated heartbeat request is not authorization. Preserve hashes and
negative evidence; never silently commit unrelated files to clear the gate.

## Gate Calibration

The required gates decide executability and falsifiability, not expected quality:
- diagnosis: a prediction-blind, task-relevant mechanism deficit or information
  gap with an explicit causal hypothesis;
- controls: the intervention changes the intended quantity relative to a matched
  control that differs only in the claimed mechanism;
- native_backward: the new path is reached by the native training loss, every new
  trainable tensor receives finite nonzero gradients, and the path is not a
  silent no-op;
- resources: parameter count, time and memory stay inside the lightweight Pareto
  budget;
- independence: physically independent package/config with no cross-variant
  imports;
- constraints: goal.json constraints and bans are satisfied.

Pre-training gates MUST NOT require a fixed task-level effect size (such as
+0.05/+0.02), validation mIoU gain, or significance on a tiny scene cohort.
These quantities do not predict a newly initialized variant's trained quality.
Pre-register the mechanism readout, paired control, sampling unit, repeatability
check, and expected direction before examining outcomes. Require a real,
task-relevant diagnosis and a reproducible control-separated intervention;
an exact no-op, a reversed mechanism, or an unexplained adverse native result
must be investigated, not passed by changing the threshold. One batch can
establish graph activity and resource feasibility, not population benefit.

Before launch, freeze a post-training evaluation plan in the candidate design
or receipt: primary ScanRefer mIoU, champion and baseline comparators, the
lightweight Pareto condition, evaluation split, scene as the clustering unit,
and a predeclared material-harm rule for meaningful subgroups. Estimate an
evaluation noise floor from independent repeats or an appropriate paired
reference; if unavailable, report that uncertainty is not quantified instead
of inventing a constant. Compute scene-clustered intervals only when enough
independent scenes exist; with inadequate data or intervals crossing the
decision boundary, label the outcome inconclusive and collect more evidence.
A single adverse scene is a diagnostic flag, not an automatic veto. Training
results, not a pre-training probe, decide efficacy and harm. The official goal
target remains unchanged.

The new policy is prospective. Preserve old freezes, outcomes and rejection
records. If a prior route failed *only* an obsolete magnitude threshold, review
the same stable ID against the new gates, check all other disconfirming evidence
and independence, and collect fresh pre-registered controls as needed. Never
silently relabel an old failure as PASS, clone it under a new ID, or disturb a
running experiment.

## Deployment And Launch

Use pipeline_monitor's gated dispatcher for new launches. Its project lock protects
queue mutation. A missing receipt, changed goal/hash/commit blocks dispatch.
Sync uses a temporary git ref and merge --ff-only with autostash disabled.
Divergence or conflicts block deployment; never reset/clean/stash to clear them.
Only candidate YAML deployment paths are adapted; no broad config rewrites.
Commit identity is necessary but insufficient: verify actual tracked runtime
source before/after a fast-forward. Only the configured deterministic YAML path
mapping is accepted; changed model code, config values, untracked source or an
unavailable probe blocks dispatch without overwriting files. AdaRES marker sync
also verifies committed source/config blob hashes in bounded read-only batches.
Only launch inside whitelist/capacity rules. Preserve foreign jobs and existing runs.
LightText's explicit task-local `isolated_runtime` opt-in may select only an
already-tested private runtime on server-3 GPU1. `isolated_runtime.py` validates
the hashed owning-chat human grant, exact task/config/receipt/commit, tested
activation and unchanged goal/server boundaries before sync or launch. Ordinary
tasks retain their server runtime. Process discovery merges only that registered
task's exact PID/config/GPU from its validated private cwd; ambiguous scope fails
observation closed, without deathwatch or dispatch. Never fake cwd, relax source
integrity, or generalize this grant to another task/runtime/GPU.
The process must show increasing native Train[epoch/total] steps in its unique log.
A live process without that evidence remains pending_progress, not closure success.
Do NOT restart it blindly. Reconcile exact config/PID/log on the next event, verify
new steps and absence of crash markers, then update queue+experiment under lock.
If process died, follow the existing bounded crash-repair procedure.

Dependencies resolve from the live queue, then per-experiment records, then the
legacy CSV. A current retry overrides an older success. Only done_complete and
done_earlystop satisfy a dependency; missing, conflicting or corrupt evidence
must not silently become success.

Dispatch persists syncing before synchronization, launch_requested before the
launch call, and PID/log/pending_progress before probing progress. An interrupted
syncing claim with no launch evidence and no matching observed process may return
to waiting under the monitor lock. Legacy or launch-requested claims are held for
exact config/PID/log reconciliation, not automatically retried. Only verified
native progress promotes a known matching process and updates all three ledgers.
Preserve user holds. Read-only monitoring reports recovery conditions without
changing any ledger. Missing evidence is a recovery problem, not new permission.

Every dispatch pass rechecks the live task status and holds, including when other
GPUs remain free. Uncertain strict launches stay claiming and consume a concurrency
slot until reconciliation; they cannot be replayed in the same pass. Exact native
progress is authoritative, not the legacy basename-only process probe.
Early-stop archival requires an explicit successful observation that the PID is
gone. A live PID or unavailable probe retains active records and reports a stop
verification issue; neither satisfies dependencies as a completed experiment.

Terminal archival writes a local pipeline/archive_pending journal before changing
ledgers. Normal monitoring replays it under the project lock before new actions:
atomic experiment/CSV writes, idempotent rows and analysis paths, then exact-task
queue cleanup. Changed task/run identity or removed resource permission blocks
replay without overwriting newer work. Journals are removed only after completion.
Old records without a journal are not guessed or rewritten. Read-only monitoring
only reports pending archival, even when --reconcile-only is also supplied.
No remote launch, stop or sync is part of archive replay.

## Tick Completion

Foreground entry requires an enabled closure policy; it never enables one
automatically. `closure.py <project> --require-enabled` returns 2 and
`CLOSURE_NOT_ENABLED` if absent/disabled. The legacy optional invocation keeps
exit 0 for disabled projects but explicitly reports that no validation ran.
Only `CLOSURE_POSTFLIGHT_PASS` certifies an executed postflight. A deadline
permits deferring further research, not skipping candidate hashes, blocker
fields, stable IDs, durable progress or verified training disposition checks.

closure.py runs after steady/event/design work. It checks preflight success,
fresh six-section report, fresh seven-section memory (<200 lines), durable work,
hash-addressed evidence and pending launch checks. A failed model execution or
postflight remains unhealthy even when reconcile-only succeeds.
Unhealthy ticks continue recovery next hour; no permanent three-failure shutdown.
Blocked research can finish a tick honestly without admitting an experiment.
`check_goal.py` status codes 0, 1 and 4 are valid preflight outcomes; only
unexpected codes are preflight failures.
