================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M152-CTF-HCG-CSORT-F1 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M152-CTF-HCG-CSORT-F1
  - Config: configs/Quard/ctf_hcg_csort_f1/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_f1.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-31 00:07:44 | Finished: 2026-08-31 17:49:48 | Duration: ~17.7h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4940 | 28/50   |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  Secondary metrics are unavailable because the monitor did not pull a local log.

## 3. Convergence Summary
  - Best recorded by the terminal ledger: mIoU=0.4940 at 28/50.
  - Early-stopped after the patience criterion was reached.
  - The fine-pair-only CSORT scope did not recover the full champion behavior.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0046.
  - vs champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0080.
  - vs full adjacent-pair CSORT: removing the coarse pair loses 0.0080.

## 5. Conclusion
  - Conclusion: [failed versus champion].
  - Interpretation: CSORT cannot be reduced to the finest 256-to-64 pair; the full adjacent-scale structure is load-bearing at seed 1999.
  - Recommendation: close the fine-pair-only scope branch.

## 6. Crash Info (if crashed)
  - No crash. Normal early stop.
================================================================================
