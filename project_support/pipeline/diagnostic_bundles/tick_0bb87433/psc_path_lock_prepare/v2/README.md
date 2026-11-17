# Reviewable one-shot Linux CPU runner — NOT RUN

All prior draft files and `preparation.json` are preserved. Only this new v2
directory was written. No SSH, proof execution, GPU/model import, deployment,
SERVERS/queue/main/index/goal change or production activation occurred.

`lock_core.py` is the **same byte artifact** intended for separately rendered
proof and future production entries. `entry_factory.py` embeds each entry's
literal absolute stage, UID, kind, binding hash and core hash in its executable
`bin/python`, whose shebang is `/usr/bin/python3 -I`. The entry checks ownership,
directory permissions, exact path/kind and both hashes before executing the
verified core bytes. There is no proof-mode environment/argv switch.

The proof uses the **real original conda Python and real original conda
activation**, with a completely isolated CPU sentinel `tools/train.py`, config,
small Git fixture and three new proof-only lock files beneath its own stage.
It never opens `/tmp/cluster_project_gpu0_*.lock`. These are fixture source/hash
checks, not evidence for the actual PSC source or deployed runtime.

The proof's outer delegated `python -B -c` uses direct
`subprocess.Popen(["python"] + exact_six_native_args, cwd=root, env=env,
stdin=DEVNULL, stdout=out, stderr=STDOUT, start_new_session=True)` with the
default `close_fds=True`. It does not call the lock helper, use `shell=True`,
override a Bash Python function, pass parent lock FDs or use `pass_fds`.

The sentinel reports actual PID/argv/cwd/interpreter and three retained
non-CLOEXEC FDs. Runner matches that PID with canonical Popen, checks three
actual `/proc/locks` FLOCK WRITE entries, opens independent contenders and
proves refusal75 through a second real direct-Popen entry. It releases the CPU
sentinel via a normal file handshake, waits for normal exit, then observes free
locks and unchanged inodes. Consumed-entry replay, each separately busy lock,
wrong arguments/source/config hash/UID and `-c`/stdin exact argv passthrough are
also exercised. All fixture artifacts are retained. No process is signaled.

Before execution, root/peer must review this entire v2 packet. Root then saves
a **fresh** immutable request from `proof_request.draft.json`, checks its actual
current owner/deadline, changes only `execution_authorized` to true, and hashes
that exact new request. This is CPU-proof authorization only; production remains
false. Stage must be the exact path derived from the current owner token:

```text
/data/songcl/Project/Cluster_project/pipeline/runtime/psc_path_cpu_<token8>
```

The planned root-controlled install creates that new stage with mode0700 and
copies the three frozen Python files plus fresh `proof_request.json`. It must
refuse an existing stage instead of overwriting/replaying. After pinned SSH
identity and current owner are verified, the explicit CPU-only command is:

```bash
/usr/bin/python3 -I -B <stage>/cpu_proof_runner.py \
  --request <stage>/proof_request.json \
  --request-sha256 <fresh-exact-request-sha256>
```

This document is a plan, not a remote command already executed. No installer,
SSH helper or production-enabling script is included. A timeout leaves an
uncertain PID/artifacts and fails without kill/terminate/replay. On success the
new `cpu_proof_result.json` still requires independent review.

Future production must use the identical frozen `lock_core.py` hash and factory
logic, with a **new, different** kind=production binding and entry hash. Bind the
actual deployed `Cluster_psc_20261106`/Git0ccc, eight actual source hashes,
deterministically adapted YAML, original Python hash/realpath, UID1001, actual
three preexisting production inode identities and actual activation receipt.
A CPU-proof binding cannot pass a production entry's literal kind/hash/path
checks. Production rendering is deliberately not performed here.

This establishes shared core bytes, **not identical full executable bytes**:
entry literals and binding files necessarily differ between isolated proof and
actual deployment. Root must verify the production render's literals/factory
output and core hash separately. It must retain canonical admission/UUID/
free>=20000MiB/max1/foreign-overlay checks and verify actual trainer three FDs,
kernel flock and native increasing TRAIN steps after the unique actual launch.
