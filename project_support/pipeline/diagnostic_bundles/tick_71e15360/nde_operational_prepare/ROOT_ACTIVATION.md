# Root activation and hash order

This package is disabled and contains no active release. Keep it and the native
prepared packet unchanged. Runtime is the already deployed parent
`/data/songcl/Project/Cluster_project/Cluster_nsd_20261107`, commit `f625...`.
Candidate `46adb...` is supplied through the frozen stage overlay. No new root
clone and no `SERVERS.yaml` edit are needed.

Use two NEW sibling directories, for example `nde_native_active` and
`nde_operational_active`. Creation is metadata-only. Do not call an operational
entry until the exact resulting files have an independent activation review.

1. Copy the native packet to `nde_native_active`. In copies of `worker.py` and
   `native_runtime.py`, replace exactly the one
   `DRAFT_EXECUTION_DISABLED = True` with `False`. Do not alter the source files,
   common-init, loss, original precision, gradient/update or resource functions.
   The ten runtime fields in the manifest template stay NULL.
2. Preserve the copied `source_version_binding.json` bytes as author/source
   provenance. In the active manifest template, update only the two changed
   `diagnostic_files` hashes and set `draft_execution_disabled=false`. All other
   diagnostic hashes, original protocol and source references remain exact.
3. Save the active native `preparation.json`: copy its author record, update
   `prepared_file_hashes` from the active files and
   `draft_execution_disabled=false`. Its own hash is not in that map. Save an
   active native FROZEN map last, including the active preparation; keep the
   disabled FROZEN untouched. None of this is an execution binding or lease.
4. Copy `adapter.py`, `remote_ops.py`, and `run_nde_operation.py` to
   `nde_operational_active`. The remote and launcher bytes stay exact. In the
   active adapter, change only:
   - `DRAFT_EXECUTION_DISABLED` True to False;
   - `FROZEN` to the active native project-local directory;
   - `PREPARATION_SHA`, `TEMPLATE_SHA` to the actual active native hashes;
   - `CURRENT_BINDING_SHA256` as determined below.
5. Save an active `current_binding.json` before the adapter anchor: copy the
   disabled binding, retain the exact current six-field owner and all
   source/runtime/root/UUID/resource/base-conda policy. Change
   `mother_FROZEN` and `mother_native_preparation` to the actual active native
   files. `activation_files` remains the unchanged remote/launcher hash map.
   The binding does NOT contain the adapter hash, so this is acyclic.
6. Set the adapter's current-binding hash. Save the active `release_template.json`
   with actual active native preparation/template hashes, source-binding hash,
   current-binding path/hash and adapter/remote hashes; set only its
   `draft_execution_disabled=false`. Save active operational preparation with
   `candidate_id`, `code_commit` and the actual package hash map. Its map must
   include adapter, remote, launcher, current-binding and release-template,
   without its own hash or `adapter_release.json`.
7. Obtain an independent review of these exact activation bytes and metadata
   changes. Only after it passes, save `adapter_release.json` as a BYTE-EXACT
   copy of the active release template. The adapter requires JSON equality.
   Root then records current candidate anchors:

```python
candidate["goal_sha256"] = "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
candidate["worker_preparation"] = {
    "preparation": ref(active_native / "preparation.json")
}
candidate["execution_adapter"] = {
    "preparation": ref(active_operational / "preparation.json"),
    "release": ref(active_operational / "adapter_release.json")
}
```

The candidate remains validation, not admitted. `ref` is a real project-relative
path and recomputed SHA256, never a supplied or old hash. Root's current
`protected_assets_before.json` must already exist; the launcher snapshots it.
It checks main HEAD f625, index and prior sources/ledgers/work/memory around each
operation. Do not edit work/memory while an operation is in progress.

Root-only calls after reviewed activation/anchors:

```text
python -B -X utf8 <active-operational>/run_nde_operation.py --execute-root --operation probe
python -B -X utf8 <active-operational>/run_nde_operation.py --execute-root --operation prepare
python -B -X utf8 <active-operational>/run_nde_operation.py --execute-root --operation stage
python -B -X utf8 <active-operational>/run_nde_operation.py --execute-root --operation run --mode smoke --target candidate
python -B -X utf8 <active-operational>/run_nde_operation.py --execute-root --operation run --mode smoke --target champion
python -B -X utf8 <active-operational>/run_nde_operation.py --execute-root --operation run --mode resources --target candidate
python -B -X utf8 <active-operational>/run_nde_operation.py --execute-root --operation run --mode resources --target champion
```

Every run requires more than 1020 seconds remaining. Root must preserve the
exact returned result/identity, PID, stdout/stderr and producer hashes. A failed,
timed-out or uncertain mutation is reconciled with its original request ID:

```text
python -B -X utf8 <active-operational>/run_nde_operation.py --execute-root --operation reconcile --request-id <exact-original-id>
```

Never replay a saved root/adapter/remote intent. `prepare` creates a NEW local
`nde_execution` binding/manifest/lease only after a fresh true resource probe;
`stage` uses new `nde_<current-token8>_gpu0`. Diagnostics verify and source the
original immutable base-conda script, never the expired NSD production shim.
No commands above grant training admission, queue insertion or trainer launch.
