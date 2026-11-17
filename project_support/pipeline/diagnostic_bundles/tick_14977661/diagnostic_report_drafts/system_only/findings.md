# M234 error investigation: system-only draft

This draft includes the saved system diagnostic and local source audits. The corrected journal/Apport follow-up actual was not present when this draft was prepared; add its actual outcome in a new draft label.

- The original terminal evidence identifies DataLoader worker3815203 SIGSEGV and the parent RuntimeError. The cause of that worker's native fault remains **UNKNOWN**.
- Installed PyTorch source now confirms the notification interpretation: `signal_handling.py` lines17–21 describes parent SIGCHLD handling; the traceback's handler calls the worker-status check. `hier_postprocess.py:87` is the interrupted parent frame, not a worker fault backtrace. Installed source hash: `f995b62e24df3a7e8fd8caa2ea94013e8a858b66531b15f00b5bfa045bc3424d`.
- Source/package metadata reports torch2.8.0+cu128, NumPy1.26.4 and SciPy1.15.3. The current pointgroup extension SHA remains `c86f516858d480e2583a437deb598279bc626e74975a060b17d75bf03f630033`; readelf records its build ID/dependencies. Current metadata and unchanged bytes do not establish the failure-time loaded ABI or culprit.
- `coredumpctl` was unavailable. Current core routing points to Apport. The two limited nonrecursive core-file scans found no candidate; they do not establish that no crash report/core exists elsewhere.
- The initial targeted journal query **failed** because `--kernel` was rejected. Its empty stdout is not a clean kernel/OOM result. The separate uname child was recorded uncertain; SSH/body return0 and `transport_passed=true` do not make every subcommand successful.
- The current shared-memory filesystem was nearly empty, with total101149011968 bytes. This postfailure observation cannot exclude failure-time shared-memory pressure.
- Static voxelization audit establishes an empty-vector API edge-case risk, but normal admitted data reductions/collation prevent empty coordinates from reaching that call. No reachable empty-input fault or cause-specific fix was established.

The diagnostic imported no Torch/model, loaded no checkpoint/data content, queried no GPU and changed no remote files/configuration. There was no restart, resume, signal, source change or repetition of passed native/data tests. No mechanism rejection or scientific efficacy conclusion follows.

Evidence:

- `system_diagnostic.actual.json`: `e96facd1018779a7071e81871ff6eea9e0d327d7a175f6590b087ac692753ed3`
- `operational_review/system_diagnostic_v2_actual_independent_review.json`: `dec119823807f8edf5c64623b04a04594385d23dc7768568044056bcea63a59f`
- `local_worker_source_audit/audit.md`: `6e46af6c6725855ede3755111119e6f29b60f32b1535b0a860bc38cefc4f7eb9`
- `local_worker_source_audit/voxel_preconditions.md`: `5b45de59f73cafa50a8c5b24659c840d9bee3f34f77da185961f506abf625ace`

Next: incorporate the real corrected journal/Apport follow-up, preserving access/tool/query limits. If it supplies no faulting worker stack or equivalent discriminating evidence, retain root cause UNKNOWN rather than propose a production change.
