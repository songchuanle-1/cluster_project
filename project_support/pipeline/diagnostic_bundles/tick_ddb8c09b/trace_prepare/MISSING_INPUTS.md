# Readiness: BLOCKED; source preparation only

At 2026-11-09T21:30Z the ops/peer feasibility packets leave these execution
inputs unverified. This list is actionable input to root/ops; it is not an
execution request.

1. Current metadata actual receipt and peer review, bound to this tick, proving
   exact rendered production YAML, admitted dataset/build-loader source hashes,
   project Python/Torch/pointgroup origins and binary identity, and approved
   ordinary interpreter import/shim path. Never run the consumed Python wrapper.
2. Existing readable train annotations, complete scene-graph cache, labels,
   local tokenizer assets and selected ScanNet/CLIP file identities. Cache
   completeness must include every scene/annotation in the finite scheduled
   prefix; reject missing cache, fallback parser generation or downloads.
3. Current CPU/RAM/pids/cgroup/sharing-capacity observations and an explicit
   reviewed admission budget for batch2/fourworkers/defaultprefetch/elastic/
   max_npoint2500000. Historical GPU resource results do not satisfy this.
4. Exact installed `dataloader.py`, `_utils/worker.py`, pin-memory code and
   stdlib multiprocessing process/finalizer source hashes and lifecycle proof.
   The private fields and done-event/None cooperative worker exit path used by
   the prototype must be reviewed against those exact sources. Vendored source
   is not installed-source proof.
5. Source review of partial Process.start failure capture, inherited
   faulthandler/event FDs, finite-prefix exhaustion, no pin-memory thread in the
   CPU-only runtime, and bounded cooperative cleanup. A live/unknown worker
   must never reach DataLoader/multiprocessing destructor or normal finalizers.
6. Root policy for an owned worker that does not exit cooperatively. The draft
   preserves PID/start/stage evidence and bypasses carrier finalizers, but
   deliberately cannot guarantee worker termination without permission to
   signal it. No foreign/protected PID may be signalled.
7. Bound anonymous event/fault FDs, hard byte limits, outer read-only supervisor
   protocol and a root review of the no-persistent-write audit guard. The guard
   cannot by itself prove absence of direct native-code filesystem writes;
   trusted native import/cache paths and allowed transient IPC must be pinned.

No FROZEN packet should be emitted until all are satisfied. Default execution
is NOP. Preparing source, AST-compiling it and testing that default NOP do not
import Torch, execute dataset code or establish runtime feasibility.

## Metadata receipt now available

The locally read ops receipt is
`ops_prepare/worker_trace_metadata/metadata.actual.json`, SHA-256
`43b914a5aaefb8e1e471a369c799a5468e1125d0899c9c641e19c299046a9113`.
Its SSH transport is terminal/rc0, but observation is
`OBSERVATION_INCOMPLETE_OR_PROVENANCE_BLOCKED`: the train-directory enumeration
hit `DIRECTORY_ENTRY_COUNT_BOUND` at its5000-entry cap. It did not reach the
installed shutdown sources, import lifecycle, host budget or cgroup limits.
This is a bounded metadata-harness block, not a dataset failure or resource
observation.

New verified facts are the exact rendered YAML and existing readable
19,617,196-byte train annotations, 77,743,218-byte scene-graph cache and labels.
The graph cache SHA is
`e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08`.
Cache graph-key completeness has not been checked. Local tokenizer.json,
vocab.json, config.json and tokenizer_config.json were observed. merges.txt,
special_tokens_map.json and added_tokens.json were absent; this is not by
itself proof the valid fast-tokenizer.json path is unusable. No remote import
or tokenizer execution occurred. Existing DGL config was observed, but its
backend contents/import behavior were not reached.
