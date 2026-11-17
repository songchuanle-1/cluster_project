# M234 archived whole-byte event index

The local implementation diagnostic completed at 2026-11-09T19:35:54.870667Z.
Both exact archived files were scanned from byte zero to EOF; their size and
mtime stayed stable and their full scanned SHA-256 hashes matched the original
terminal archive receipt. No SSH, native imports, unpickling, GPU work, training,
or source/configuration changes were performed.

| Archive | Bytes scanned | CR/LF/CRLF separators | Matching lines |
| --- | ---: | --- | ---: |
| registered_stdout | 2,671,896 | 18,329 / 95 / 0 | 2 |
| actual_native_logger | 929,903 | 0 / 921 / 0 | 0 |

Total coverage is 3,601,799 bytes. Neither the 8 MiB per-file nor 16 MiB total
limit truncated the scan. Neither event storage nor displayed event/context
lines were truncated. Byte offsets are zero-based and end-exclusive; line
numbers treat CR, LF and CRLF as record delimiters.

The stdout events are:

1. Line 18,378, byte range [2,666,942, 2,667,163): the progress record for
   Train[2/50] batch 4295/4686 contains
   `ERROR: Unexpected segmentation fault encountered in worker.`
   This is a terse worker-fault notification, not a worker Python/native
   traceback. The next record contains a NUL byte. No faulting native frame,
   failed sample, annotation or worker stage follows this notification.
2. Line 18,422, byte range [2,671,645, 2,671,733):
   `RuntimeError: DataLoader worker (pid 3815203) is killed by signal: Segmentation fault.`
   Its preceding context is the parent model stack: `hier_postprocess.py:87`
   followed by installed PyTorch `signal_handling.py:73` and
   `_error_if_any_worker_fails()`. This agrees with the existing installed-source
   finding that the parent's SIGCHLD handler reports a different process's
   death; the model frame is not the worker's native fault location.

Both events fall within the already-observed final 128 KiB. The newly examined
earlier bytes contain no additional matches for the declared worker-failure,
segmentation-fault, SIGBUS/bus-error, Python fatal/faulthandler, native-backtrace,
allocator-corruption or abort patterns. The native logger has no matches for
these declared patterns anywhere in its complete file. Thus this diagnostic
closes the earlier-byte coverage gap but does not reveal a previously hidden
worker stack. This is a bounded pattern-index finding, not evidence that no
unlogged native fault, memory pressure or other system event occurred.

The targeted duplicate check covered the terminal, installed-source/system,
fresh CPU and fork CPU diagnostic bundles (342a6a92, 14977661, eb845403,
d2045281), using archive-name and full-byte/event-index searches and their
existing diagnosis/receipt files. No earlier complete-byte fatal-event index
was found in that targeted scope. The old receipt explicitly decoded only
131,072 trailing bytes per file. This does not claim exhaustive review of
unrelated project history.

The current tick owns this new local analysis only. The original M234
launch/source/runtime/GPU identity and archive ownership remain historical;
nothing was retokened. Native root cause remains **UNKNOWN**. Historical crash
reproduction and training repair are both **unverified**. Existing fresh/fork
CPU measurements were not repeated.

Evidence:

- `scan_archived_logs.py`: SHA-256
  `09c139645fc6cea3190e355d60691991bf0aa198da091c8060231c3d2fc1ca83`
- `scan.actual.json`: SHA-256
  `ffaa339538689a4647b25c5f6f185763afbf292beb5263a11b16bdd41f36cf45`
- Source runner defaults to NOOP; executing requires `python -B` and
  `--execute-local`, the exact current owner and an unexpired lease. The actual
  file is exclusive-created and execution refuses replay.
