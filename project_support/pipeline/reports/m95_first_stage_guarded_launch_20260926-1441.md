# M95 Guarded First-Stage Launch

2026-09-26 14:41 Asia/Shanghai. Stable ID `m95-repro-drift-boundary`.
Only server-6 GPU7 is authorized. Its live memory and utilization were
0 MiB and 0% before launch; code root, conda environment and data root
were present. The script, config, checkpoint, manifest, saved row83 batch,
and original-order result matched their frozen SHA256 identities. The
remote wrapper has SHA256
`07cc7584446229a79cd0adf1e268a0416819deb37d61f42fdf313e4d96cc8bba`.

An exclusive `/tmp/cluster_project_gpu7_exclusive.lock` lease was acquired.
Remote wrapper PID 2858712 started the fresh full-order same-process
diagnostic. The remote clock reported 06:40:44 UTC at startup; a later
local observation found the progress stream at step 100/3137 and GPU7 at 3283 MiB
at 58% utilization. The remote run path is
`/data3/songcl/Project/Cluster_project/Cluster/pipeline/diagnostic_runs/m95_full_order_first_stage_20260926_1435`.
The wrapper writes `status`, `progress.jsonl`, `stdout.log`, and, only on
successful comparison, `result.json` and `result.sha256`.

The guarded wrapper checks for a foreign GPU7 process above 1024 MiB
every 15 seconds; if present it terminates only its own child and records
the interruption. It has no fixed 2650-second timeout. No model, queue,
checkpoint, or foreign job was modified. The stream is not a checkpoint,
and neither step 100 nor a live PID is a comparison result. Retrieve and
hash-verify the completed result or preserve the precise interruption in
the next tick. Keep strict 26/65 and all six admission gates unchanged.
