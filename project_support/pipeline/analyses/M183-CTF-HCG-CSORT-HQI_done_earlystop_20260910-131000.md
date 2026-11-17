================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: M183-CTF-HCG-CSORT-HQI | State: done_earlystop
================================================================================

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_hqi/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hqi.yaml
- Server: server-4 | GPU: 1 | Former PID: 2939408.
- Local launch registry: 2026-09-09T12:08:49, retained.
- Logger start: 2026-09-09 12:08:47.898; end: 2026-09-10 12:40:45.686,
  both server-4 local clock. Duration: 24h31m57.788s.
- State: done_earlystop. Explicit trainer marker, process absent, GPU1 idle.
- Local archive: Checkpoints/server-4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hqi/20260909_120847/20260909_120847.log
- Remote/local SHA256: d2fcedfc902e9274687c0f6327c311536b735e97a31d1f3eefc73d421a4cc80e.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | 0.49154922366142273 | 14 |
| Acc@50 | 0.545 | 14 |
| spmIOU | 0.455 | 14 |
Acc/spm are rounded metrics paired at the exact best-mIoU epoch, not maxima.
Prior admission: 9.787698252G, 894.117MiB inference allocation versus matched
M95 893.367MiB; one scene, not a universal training-peak claim.

## 3. Convergence Summary
- One exact logger, 24 completed validations; best first at epoch14.
- Ten genuine post-best validations at epochs15..24. No monitor early kill.
- Final epoch24 mIoU=0.48065418004989624, Acc50=.536, spmIOU=.442.
- Explicit terminal marker: early stopping at epoch24 after10 no-improvement.
- Early rise then plateau/decline. Prior tick correctly preserved patience9.
- Initial monitor deathwatch1/3 is only a process-absence heuristic; direct
  immutable terminal evidence supports scoped finalization without fabricating
  repeated monitor ticks or modifying the generic deathwatch threshold.

## 4. Comparison
- vs baseline .4894: +.0021492237.
- vs M95 champion .5020: -.0104507763.
- vs target .5100: -.0184507763.
- HQI changes query initialization, unlike terminal readout candidates.
  Single seed and shared hardware do not isolate causal effects or robustness.

## 5. Conclusion
- Above baseline but unsuccessful versus champion; no superior HQI mechanism.
- Fixed ancestor context at query initialization did not support the intended
  gain in this run. Close this HQI branch without numeric tuning, automatic
  rerun, or combination with unproven terminal readouts.
- Preserve existing independently admitted M184-M191 graph ablations.
  Preserve checkpoint and exact logger; keep goal/seed/schedule unchanged.

## 6. Crash Info (if crashed)
- No crash; repair attempts0. Trainer stopped normally.
- Finalization will retain launch/history, remove only M183 ownership and add
  one ledger row using the verified archive and this paired analysis.
================================================================================
