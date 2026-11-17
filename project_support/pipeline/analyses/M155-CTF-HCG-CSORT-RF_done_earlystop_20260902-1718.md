================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M155-CTF-HCG-CSORT-RF | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M155-CTF-HCG-CSORT-RF
  - Config: configs/Quard/ctf_hcg_csort_rf/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rf.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-09-01 01:50:12 | Finished: 2026-09-02 10:02:18 | Duration: ~32.2h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | 24/50   |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  Secondary metrics are unavailable because the monitor did not pull a local log.

## 3. Convergence Summary
  - Best recorded by the terminal ledger: mIoU=0.4950 at 24/50.
  - Early-stopped after 11 consecutive validations without a new best.
  - Moving CSORT from raw cluster centroids to refined post-CTF tokens did not improve alignment.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0056.
  - vs champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0070.

## 5. Conclusion
  - Conclusion: [failed].
  - Interpretation: refined-token operand alignment is not the missing factor; the original CSORT operand is preferable.
  - Recommendation: close the refined-token CSORT branch.

## 6. Crash Info (if crashed)
  - No crash. Normal early stop.
================================================================================
