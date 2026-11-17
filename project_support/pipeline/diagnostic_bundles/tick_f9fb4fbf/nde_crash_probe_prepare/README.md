Default-denied NDE SIGSEGV localization bootstrap
================================================

Only crash_probe_bootstrap.py is new. Reuse exact0747 model, b37fe5 worker and348024 active runtime without any byte changes. No model revision, resource counter/AST, YAML, seed, numeric dtype, precision, RNG or torch flags change.

Fresh operational copy must change ONLY DRAFT_DIAGNOSTIC_DISABLED=True toFalse, then independently review the actual active bootstrap SHA. Extend a fresh staged manifest diagnostic_files with that actual active bootstrap and independent review JSON. Do not alter original source/runtime/worker hashes. Native runtime.verify will check the extended files. Request is separate (not self-hashed into manifest), binds actual manifest and original lease hashes, active bootstrap SHA, original worker/runtime SHA, exact fresh six-field owner, and original worker argv. Independent review JSON must contain passed=true, bootstrap_sha256, owner, fault_localization_only=true and be manifest-hashed. No preparation file is an active request/review/lease.

Explicit new diagnostic request JSON fields: operation=candidate_resources_fault_localization; fault_localization_only=true; admission_evidence=false; comparable_resource_or_latency_evidence=false; owner={token,thread_id,generated_at,deadline_at,context_sha256,pending_sha256}; native_manifest_sha256; execution_lease_sha256; bootstrap_sha256; worker_sha256; runtime_sha256; independent_review_file (stage-local basename); independent_review_sha256; original_worker_argv=[<exact stage>/worker.py,--lease,<exact stage>/execution_lease.json,--mode,resources,--target,candidate].

Actual guarded invocation after independent review and fresh original20000MiB/GPU0 slot/three-lock preparation:

    /home/songcl/.conda/envs/project_cluster/bin/python -B -X faulthandler <exact fresh stage>/crash_probe_bootstrap.py --diagnostic-request <exact stage>/<new reviewed diagnostic request.json>

Bootstrap confirms server4 hostname, exact GPU0UUID/root/source/runtime/manifest/lease, freshness, original hashes and reviewed manifest extension before original entry. It enables stdlib faulthandler(all_threads=True) to stderr, line-buffers stdout/stderr, and writes a new exclusively-created fault_localization_markers.jsonl. Original worker argv is installed unchanged; runpy.run_path(exact worker,run_name=__main__) then executes the original worker and original acquire/resource logic. Original cooperative locks and memory checks run in that worker.

At most64 markers capture entry before/after, setup/resources call/return and first selected imports of torch/numpy/gorilla/tools.train/framework/pointops/spconv. Import wrapper returns the original object; Python exceptions re-raise as the same object; hooks/argv restore on normal/Python-exception exit. Native SIGSEGV is not intercepted or recovered; faulthandler preserves the terminating fault. The real command/interpreter flags/bootstrap and original-entry hashes are captured before entry.

All output and any resources_candidate_result.json from this instrumented invocation are FAULT_LOCALIZATION_ONLY, never comparable timing/resources/technical-admission evidence. Preserve failure bytes and timestamps. No control/replay/remediation is performed by the bootstrap.
