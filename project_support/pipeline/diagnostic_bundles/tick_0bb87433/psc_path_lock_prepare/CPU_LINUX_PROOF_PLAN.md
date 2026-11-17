# PSC direct Popen lock proof plan — NOT RUN

This packet is a disabled local draft. No remote root, activation, proof result,
kernel lock, GPU occupancy, resource PASS or actual launch is claimed. The
prospective code root is
`/data/songcl/Project/Cluster_project/Cluster_psc_20261106`, source
`0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d`. This file grants no deployment,
binding, source promotion, queue change or training action.

The old HVD proof exercised `_hvd_gpu0_locked_exec` and overrode a Bash helper.
It proved that helper's lock inheritance, not the executable reached by
`closure.safe_launch` lines 451–452. Canonical new cluster launches call
`subprocess.Popen(["python", "tools/train.py", cfg, "--gpu_ids", "0",
"--num_gpus", "1"], cwd=root, env=env, stdin=DEVNULL, stdout=out,
stderr=STDOUT, start_new_session=True)` with the normal default `close_fds=True`.
Popen resolves a real PATH executable and cannot invoke the old Bash function.

## Isolated proof artifact and setup

1. On a permitted Linux CPU foreground session, reserve a fresh **project-local**
   proof directory with no GPU use. Verify the current owner/deadline and pinned
   host/UID if the proof is done on server4. Do not use original `/tmp` lock
   files, real source/config trees, real training entrypoints or real one-shot
   markers. Never signal, unlink locks or clean a previous uncertain proof.
2. Freeze a separate proof executable from this wrapper's exact reviewed
   function bodies with a literal **proof-only** binding. Keep its own
   `kind="proof"` acceptance and proof constant separate from the production
   artifact. Its code root, source fixture, Python entry, three lock files,
   marker and activation paths must all resolve inside that one proof directory.
   Never add an environment/CLI switch to the production wrapper, never let a
   production binding read a proof fixture, and never edit this frozen draft.
3. Make the fake conda prefix contain an executable `bin/python` that delegates
   via `exec /usr/bin/python3 "$@"`. The fake `tools/train.py` is a CPU sentinel,
   containing no model/Torch/CUDA imports. Populate a tiny fixture Git repository
   at the proof root. Bind the actual fixture HEAD, source hashes, interpreter
   realpath/hash, sentinel-config hash and actual precreated three lock
   `(st_dev,st_ino)` pairs. The proof stage mode is 0700 and files are owned by
   the actual non-root UID. Make `proof-wrapper/bin/python` mode 0755.
4. Use a shell conda fixture that deliberately prepends its own env/bin on each
   `__conda_activate`, and use the draft shim's exact activation/priority
   functions with only literal proof paths/name substituted. Also perform an
   independent real-conda CPU check under the verified original initialization:
   source a proof-bound shim; run the exact canonical
   `conda activate project_cluster`; confirm `type -t python=file`,
   `type -P python=<proof executable>`, and a delegated `python -B -c` observes
   the expected original conda interpreter. A fixture cannot establish the
   real-conda behavior by itself.

## Exercise the actual executable path

5. The outer shell sources that proof conda_source and activates conda, then
   runs `python -c <launcher>`. That non-training invocation must delegate to
   its literal original Python. The launcher copies `os.environ`, sets the
   same canonical PYTHONPATH/LD_LIBRARY_PATH/TMPDIR policy within the isolated
   fixture, and uses **the exact Popen argv/cwd/env/stdin/stdout/stderr/session
   arguments above**. Do not call a lock helper directly, override a shell
   helper, use `shell=True`, pass locks from the parent or use `pass_fds`.
6. The CPU sentinel records its own PID, PPID, argv, UID, executable, cwd and
   `/proc/self/fd` observations. It must see exactly one retained FD per bound
   lock inode, each FD with FD_CLOEXEC clear. Verify `/proc/locks` contains three
   real FLOCK WRITE records for those `(device,inode)` pairs. Prefer matching
   `/proc/locks` dev major/minor/inode rather than names alone. The sentinel PID
   must equal the PID returned by direct Popen, proving no forked lock guardian
   replaced the actual exec target.
7. While the sentinel is held on a bounded CPU-only file/pipe handshake, a
   separate contender opens each lock inode independently and must receive
   EWOULDBLOCK/EAGAIN on LOCK_EX|LOCK_NB. Try an exact second Popen through a
   fresh proof executable/marker pointing at the same fixture lock inodes; it
   must exit75 before sentinel entry. If an already consumed marker is used,
   it must refuse instead of launching. Do not mistake marker-only rejection
   for observed kernel contention.
8. Give the sentinel its normal handshake release; it exits naturally and
   Popen waits without kill/terminate/signals. A timeout records an uncertain
   PID and stops further mutation/replay. After natural exit, verify every
   original fixture inode remains unchanged and all three flock acquisitions
   now succeed and are closed normally. No file deletion is needed. Reusing
   the consumed entry still refuses even though the locks are free.

## Negative controls and passthrough

9. In isolated fixtures only, test GPU1, wrong config, duplicate/missing GPU
   arguments, extra `--resume`, absolute/`./tools/train.py` aliases, prefixed
   `-B`, another cwd, another UID binding, wrong source HEAD/hash, changed
   runtime YAML, wrong original interpreter, replaced/symlink lock and absent
   preexisting lock. They must refuse before sentinel entry, without creating
   or truncating locks. Repeat lock contention with each of three locks held
   separately so early partial acquisitions are proven naturally released.
10. Test non-training `python -B -` with stdin, `-B -c` and harmless `-m` plus
    space/glob/dollar/empty argv. Verify exact argv/stdin/return-code delivery
    to the literal original interpreter and no lock acquisition/marker change.
    Test hostile `PSC_PROOF_MODE`, `PSC_SKIP_LOCKS`, replacement path/config
    variables, `GIT_DIR`, `GIT_WORK_TREE`, `GIT_CONFIG_COUNT` and PYTHONPATH.
    There is no proof/bypass environment interface; system shebang `-I` protects
    wrapper stdlib imports. This is cooperative launch protection, not a
    sandbox against an account deliberately running arbitrary code or replacing
    its own reviewed files. No claim of universal training interception.
11. Save commands, frozen hashes, full stdout/stderr, Popen and actual sentinel
    PIDs, FD metadata, three `/proc/locks` records, contention errnos, unchanged
    inode identities, natural return and released-lock observation in a fresh
    result. Root/peer reviews actual evidence before any production rendering.

## Separate future production rendering

The current `python` has DRAFT_ENABLED=False, production-draft kind, absent inode,
runtime-config/interpreter/activation hashes and no code-file mapping. The shell
has an explicit unfilled executable hash. These are deliberate hard refusals.

After real native paired/resource admission and independent review, root may
render a **new** production artifact bound to the actual deployed PSC tree,
exact eight code hashes, Git0ccc, deterministic canonical-adapted YAML hash,
fixed original conda Python realpath/hash, server4 UID1001, original three
preexisting inode identities and reviewed activation receipt. The new shim
embeds that executable's actual hash. Final wrapper has only production literals
and no proof mode. Installation preserves source/common init/protocol and never
changes Python argv/precision, resumes an experiment or modifies the scheduler.

Canonical admission/source/GPU0 UUID/free>=20000MiB/projectmax1/foreign-overlay
checks still precede new launch. Locks add a cooperative race boundary and do
not prove current physical availability. A one-shot marker is consumed before
exec and must never be removed automatically even if exec fails. After the
unique actual Popen, verify actual trainer PID/starttime/cmdline/cwd, three
kernel flock FDs and increasing native TRAIN steps. The Bash proof, this plan,
a PID alone or a successful source command cannot substitute for those checks.
