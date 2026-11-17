# Root wrapper handoff

Default NOP and local metadata preparation only were run by the author.
No SSH, dataset/native code or workers were executed.

`run_trace_once.py` sends only a small fixed bootstrap on the SSH command line.
The supervisor source, carrier source and final packet travel as one JSON stdin
object. The bootstrap verifies source and canonical-packet SHA256 literals
before executing the reviewed supervisor. The complete bounded result is saved
locally; the wrapper prints only path/hash and a small status summary.

Root invocation after a successful approved current constructor actual and
genuine final source review:

    python -B -X utf8 run_trace_once.py --execute-root --constructor-actual ABSOLUTE_ACTUAL --constructor-sha256 SHA --review ABSOLUTE_REVIEW --review-sha256 SHA

The review must contain matching owner, passed=true, material_concerns=[],
independent reviewer_thread_id, frozen_sha256, wrapper_sha256,
body_sha256 (trace_supervisor.py), carrier_sha256 and finalizer_sha256.
`FROZEN.json` freezes source only. It explicitly supplies no execution readiness.
The wrapper validates the actual PASS and review before assembling packet.final.

`finalize_packet.build_packet` consumes the actual constructor's terminal
transport/PASS, complete cache coverage, guarded source/cache/tokenizer stat
identities, exact module origins and authenticated uname policy. It does not
invent import shims, enumerate data directories or hash PTH contents. A later
approved constructor revision uses the same actual result schema; its path
must be inside the current tick.

The root-authorized CPU guards are measured before any carrier starts:
host MemAvailable and every finite cgroup ancestor memory headroom >=64GiB,
/dev/shm available >=16GiB, affinity >=4 CPUs, finite ancestor pids headroom >=8.
The diagnostic's soft RSS budget is64GiB. The result retains actual prelaunch
capacity, process RSS observations, sharing capacity and capture truncation.
This is one standalone CPU data test, not a GPU resource/model/training gate.

Execution exclusive-creates packet.final.json, trace.intent.json and
trace.actual.json. Existing intent/result forbids replay. A local SSH timeout
preserves transport artifacts/PIDs without signalling or retry. Remote
supervision has its own bounded exact-owned cleanup. Latest root launch is
00:02Z, before the00:11Z lease deadline.

Root must inspect inner carrier status, worker fates, fault captures, signals,
native-stage observations and truncation. SSH rc0 alone is not diagnostic PASS.
No new full training, resume, revision, repair or historical-root-cause claim
is produced by this wrapper.
