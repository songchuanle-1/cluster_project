# Trace v2: root review pending, no freeze or execution

The old ddb8c09b source is unchanged. This tick owns the new diagnostic source,
not M234's original launch or the historical evidence. Installed lifecycle
evidence is reused at its original owner/hash:
`remaining.actual.json` SHA
`c0e2feded9c6e6552ffb7e3f5c3401bb529ee0ad75b84cf257afc5ee77763cd4`.

## Concrete remaining inputs

1. Successful current constructor v2 actual SHA/status, its guarded file
   identity records, exact module origins and authenticated readonly uname
   policy. Constructor v1 stopped at an audit restriction during import; it
   did not reach the dataset constructor.
2. Root's CPU capacity admission and final genuine source/supervisor review.
   No more installed lifecycle source queries, all-directory manifests,
   large PTH hashing or model/training gates are needed.

The supervisor observes current host/sharing/cgroup-ancestor capacity before
forking. The packet supplies the reviewed thresholds. A capacity failure
starts no carrier or worker. Optional project-Python pidfd absence does not
block cooperative operation: the system-Python supervisor owns mandatory
pidfds and performs bounded escalation. Both sources default to NOP.

## Minimal invocation protocol

Root runs the reviewed supervisor using ordinary system Python with
`--execute-reviewed` and a bounded JSON stdin object:

    {"execute_root":true,"carrier_source":"<exact reviewed source>","packet":<completed packet>}

The source SHA must match packet.carrier_sha256. The supervisor creates
anonymous memfds, a private transient IPC directory and one direct fork/exec
of the ordinary conda Python3.10 interpreter. No consumed wrapper is executed.
The supervisor passes the source and packet through memfds and uses the
native user-site/import environment proven by constructor v2. It does not
create remote source/cache/log files or use SSH itself.

The JSON result is bounded at32MiB. It contains full captures up to declared
per-FD bounds as base64; root should save that result locally and print only a
small parsed summary. Capture limits are2MiB per event FD,64KiB per fault FD,
64KiB status and512KiB each stdout/stderr. Any truncation is explicit. Root
must not treat a transport rc0 as diagnostic PASS.

## Operational changes

- Installed DataLoader fbd260c9 creates workers inside iterator __init__.
  The wrapper retains that iterator before calling the original constructor,
  suppressing destructor fallback if construction raises.
- Installed Popen._launch forks before BaseProcess.start assigns _popen.
  The new fork wrapper records actual PID/start immediately in the parent,
  retaining done-event/index-queue references from before Process.start.
  SIGUSR1/SIGCHLD exceptions are deferred across this capture window. The
  child also writes its identity to its dedicated FD before bootstrap.
- Exactly ten batches are taken from the original BatchSampler iterator.
  Default batch2, four workers, prefetch2, persistent=True and original
  augmentation remain configured. Scheduling is capped at ten batches total,
  so no additional prefetched batch lies outside the consumed ten.
- Transparent wrappers add no RNG draws or data changes. They retain sample/
  annotation identity, RNG digests and the requested stages. Every original
  function is called once with its original inputs and returns its original
  result. Faulthandler is installed before bootstrap and reenabled in the
  worker init callback after installed Torch signal handlers and seeding.
- Each real trusted scene/CLIP load validates its resolved native root,
  original first-sorted-substring scene selection, and records before/after
  dev/ino/size/mtime. It does not inventory or hash every large data file.
- The audit guard permits the exact authenticated platform.from_subprocess
  uname-p helper and verified /dev/null character device, using constructor
  v2's policy. Arbitrary subprocesses, network and persistent writes stay
  denied. No compatibility module or parser/tokenizer fallback is substituted.
- Normal cleanup sets only owned done events, sends None and joins. Carrier
  os._exit bypasses DataLoader/multiprocessing destructor termination paths.
  The supervisor requests cooperative stop, then escalates only exact
  diagnostic-owned pidfds with SIGTERM/SIGKILL if needed. Every signal is
  recorded. Unknown ownership is preserved without signal or automatic retry.
  Pidfds and event identities also cover the one authenticated readonly helper.

The original seed is1999, but omitted model/profile/epoch/CUDA-parent history
changes RNG consumption. This is not historical input reconstruction. A stage
enter without exit is a last observed boundary, not proof of faulting
instruction. Clean short execution cannot prove historical repair, operator
clearance, efficacy or authorize restart. Root cause remains UNKNOWN.
