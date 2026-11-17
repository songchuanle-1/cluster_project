# Executable Closure Contract

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
training, rejected, blocked. Keep the same ID when advancing an existing idea.
Event mode MUST continue due work even when candidate budget is zero; it does
not authorize extra training or override a goal-phase hold. Complete the next
executable validation before starting another review of the same hypothesis.
Stage training requires queue launch_verified=true and native step evidence.
Rejected requires concrete disconfirming evidence; do not reopen under a new ID.
Blocked requires blocker, retry_after (timezone-aware ISO date), unblock_condition
and evidence of attempted alternatives. Missing native capture is executable work,
not an external blocker. A literature service outage may be blocked after recording
alternate-source attempts. Never assert novelty from an empty search.
No new evidence/stage change fails postflight; timestamp-only edits do not count.
Hashes establish artifact identity, not scientific validity.

## Admission Receipt

Write pipeline/admissions/<id>.json, point queue entry admission_receipt to it.
Required: id, config, code_commit (full git SHA matching queue and local HEAD),
goal_sha256, decision {path,sha256}, gates object. Each gate has passed:true and
nonempty evidence:[{path,sha256}]. Required gate keys:
diagnosis, derivation, literature, controls, native_backward, resources,
independence, constraints. Use real outputs; never convert unverified work into PASS.
The agent still must conduct substantive scientific review and record limitations.
Commit tested candidate code before computing the receipt. No automatic git add/commit.

## Deployment And Launch

Use pipeline_monitor's gated dispatcher for new launches. Its project lock protects
queue mutation. A missing receipt, changed goal/hash/commit blocks dispatch.
Sync uses a temporary git ref and merge --ff-only with autostash disabled.
Divergence or conflicts block deployment; never reset/clean/stash to clear them.
Only candidate YAML deployment paths are adapted; no broad config rewrites.
Only launch inside whitelist/capacity rules. Preserve foreign jobs and existing runs.
The process must show increasing native Train[epoch/total] steps in its unique log.
A live process without that evidence remains pending_progress, not closure success.
Do NOT restart it blindly. Reconcile exact config/PID/log on the next event, verify
new steps and absence of crash markers, then update queue+experiment under lock.
If process died, follow the existing bounded crash-repair procedure.

## Tick Completion

closure.py runs after steady/event/design work. It checks preflight success,
fresh six-section report, fresh seven-section memory (<200 lines), durable work,
hash-addressed evidence and pending launch checks. A failed model execution or
postflight remains unhealthy even when reconcile-only succeeds.
Unhealthy ticks continue recovery next hour; no permanent three-failure shutdown.
Blocked research can finish a tick honestly without admitting an experiment.
