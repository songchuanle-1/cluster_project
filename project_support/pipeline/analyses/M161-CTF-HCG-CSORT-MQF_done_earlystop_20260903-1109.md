================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M161-CTF-HCG-CSORT-MQF | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M161-CTF-HCG-CSORT-MQF
  - Config: configs/Quard/ctf_hcg_csort_mqf/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqf.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-09-02 20:07:58 | Finished: 2026-09-03 10:16:49 | Duration: ~14.1h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4920 | 26/50   |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  Secondary metrics are unavailable because the terminal log was not pulled locally.

## 3. Convergence Summary
  - Best recorded by the terminal ledger: mIoU=0.4920 at 26/50.
  - Subsequent no-improve count reached 11 and triggered monitor early stop.
  - The run improved steadily through the early epochs but plateaued close to the
    no-cluster baseline rather than the CSORT champion.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0026.
  - vs champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0100.
  - vs aligned receiver-message PMD (M157=0.4990): gamma = -0.0070.

## 5. Conclusion
  - Conclusion: [marginally effective versus baseline, failed versus champion].
  - Interpretation: static foreground-mask retrieval does not solve context dilution;
    its small gain is insufficient and may reflect generic recurrent capacity.
  - Recommendation: retain M162 as the paired shuffled semantic control, but do not
    expand the plain foreground-pooling branch. Continue testing contrast, reciprocal,
    exclusive-ownership, and temporal-delta mechanisms already in queue.

## 6. Crash Info (if crashed)
  - No crash. Normal monitor early stop.
================================================================================
