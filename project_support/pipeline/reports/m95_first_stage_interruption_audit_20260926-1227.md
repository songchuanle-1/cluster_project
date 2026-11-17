# M95 First-Stage Diagnostic Interruption

2026-09-26 12:27 Asia/Shanghai. Stable ID: `m95-repro-drift-boundary`.

The 11:07 scheduled native diagnostic used server-6 GPU7 under the exclusive
lease. Its exact-checkpoint, exact-item, full TRAIN-order producer reached step
3000 of the required step 3137, then the 2650-second per-command timeout
expired. It did not write a comparison result. The retained progress stream
is `pipeline/reports/m95_full_order_first_stage_progress_20260926-1204.jsonl`
(SHA256 `2b69f74692d8fafae016caf9edd288179b6eb85b1ecf73d493f135e96210dae5`).
The scheduled tick then timed out before updating its research ledger/report;
`.tick_unhealthy` is still present. No terminal experiment or admission resulted.

The manual continuation verified the same diagnostic source SHA256
`b29f5a17d471bf8e53a5c53bea07688b07a82062aa759a3ba1eb63d7373677cc`,
exact checkpoint/environment/data paths, GPU7 initially at 0 MiB/0%, and
acquired `/tmp/cluster_project_gpu7_exclusive.lock`. A fresh full-order run
reached step 600. Another user's GPU7 job then appeared (PID 1616985,
61,144 MiB; total GPU7 use about 65,007/81,559 MiB). Only our diagnostic
PID 1583600 was sent TERM; it exited, freeing its approximately 3,846 MiB.
The external job was not modified. The second progress artifact is
`pipeline/reports/m95_full_order_first_stage_interrupted_20260926-1225.jsonl`
(SHA256 `fe3acda15390c523aaee1bc124f8d8af66de85838f29d9b4e052ccbcd280e23f`).
Both runs stopped before row83; no first-stage numerical comparison exists.

The project allows two task slots on GPU7. The closure checker reserves its
`exclusive_gpu_slot` blocked kind for single-task-per-GPU allocations, so this
interruption is recorded as external GPU memory occupation with live evidence,
not as a queue-capacity block. A second queue slot does not make an exclusive
native diagnostic safe alongside the foreign 61 GiB process.

Resume only after a live occupancy check shows GPU7 safely idle, with an
exclusive lease and an uncontended window exceeding the observed full-loader
duration (about 45-50 minutes plus comparison/retrieval). Before repeating,
prefer a verified, hash-bound saved pre-target producer/RNG state if feasible;
otherwise a full restart is required. Do not resume the old partial stream
as though it contained an exact state. Preserve strict 26/65 failure and
six admission gates. This is an operational block on a numerical diagnosis,
not proof of an independent trainable mechanism or a reason to enqueue.
