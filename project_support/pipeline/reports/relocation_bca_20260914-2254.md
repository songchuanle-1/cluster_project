# M196 User-Directed Relocation
2026-09-14 22:54 Asia/Shanghai.

- Request:run new M196 on server4 first;existing M194/M195 untouched.
- Decision:20260914-225126_manual.md.
- Destination server4GPU0 initially24532MiB free;foreign processes untouched.
- Code a490710624530115c3430a8c3693fd8c8d74208b already matched.
- No source checkpoint existed;restart same seed1999,not resume or tuning.
- Source PID1968342 command/process-group identity verified before SIGTERM.
  Confirmed absent after destination launch;source log and experiment history retained.
- First stop invocation failed because noninteractive PATH lacked python,
  without stopping source. Absolute existing interpreter retry succeeded.
- Destination launched22:52:42 PID3237667;epoch1/50 step28 verified22:54.
- Log:/data/songcl/Project/Cluster_project/Cluster/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca_20260914_225242.log
- Queue,running and experiment record reconciled under monitor lock.
- M194PID2172354/server4GPU1 and M195PID3496122/server6GPU7 verified alive.
- No goal,capacity,schedule or scientific claim changed.
