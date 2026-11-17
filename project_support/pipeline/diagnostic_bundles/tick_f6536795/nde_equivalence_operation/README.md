# Separate revision1 equivalence operation, pending independent review

Default invocation is NOP. No SSH/GPU/native operation was executed by author.
Original adapter, worker, stage and old packages are untouched. EQ calls only the
already staged exact equivalence_diagnostic.py --lease execution_lease.json.
It does not add a mode to original worker or call TRAIN2 or resource measurement.

The root wrapper requires byte-exact operation_release.json matching its static
release_template.json; this release is absent pending independent review. After
review root may create that separate release and explicitly use --execute-root
--operation run. --operation reconcile reads the exact stage/request only.

The existing reviewed Adapter.guard(1020,0,mutation=True), _binding, project lock,
local project slot check, prior-request terminal check, real probe and original
three-lock/free20000MiB/max1/overlay policy are reused. The EQ entry itself uses
unchanged native.acquire for all3 locks/resource checks. Remote launches also
require unchanged deadline remaining>1020 seconds. Original condabase/hash and
SSH key/strict host verification come from unchanged reviewed SSHTransport.

Remote helpers are loaded from exact pinned reviewed remote_ops bytes supplied
in the payload. No helper is rewritten. This module dispatch permits only
EQ run/reconcile; original run/stage/probe are rejected. Request/start PID and
start_ticks/argv, stdout/stderr, result and completion journals use separate EQ
names. Local root intent/request are exclusive-create. Any existing intent or
attempt causes read-only reconciliation and never launch/replay. Timeout leaves
uncertainty, never signals, kills or restarts. Reconcile requires original
request/command/PID identity and completed result hashes to establish terminal.

The operation writes only new local EQ journals and staged EQ journals. Existing
native smoke/resource results are not relabeled or mixed. Result must retain
mode revision1_equivalence, current owner/source/runtime/UUID/manifest/entry
hashes, native_TRAIN_steps=0 and native_data_loaded=False. Original EQ controls
and tolerances remain in the unchanged staged entry.
