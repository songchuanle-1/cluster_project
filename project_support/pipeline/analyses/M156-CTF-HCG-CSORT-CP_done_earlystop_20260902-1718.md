================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M156-CTF-HCG-CSORT-CP | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M156-CTF-HCG-CSORT-CP
  - Config: configs/Quard/ctf_hcg_csort_cp/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cp.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-30 13:07:52 | Finished: 2026-09-01 03:51:06 | Duration: ~38.7h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | 22/50   |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  Secondary metrics are unavailable because the monitor did not pull a local log.

## 3. Convergence Summary
  - Best recorded by the terminal ledger: mIoU=0.4950 at 22/50.
  - Early-stopped after 11 consecutive validations without a new best.
  - Coarse-pair-only CSORT did not reproduce the full adjacent-pair result.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0056.
  - vs champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0070.
  - Together with M152-F1=0.4940, neither isolated adjacent-scale pair is sufficient.

## 5. Conclusion
  - Conclusion: [failed].
  - Interpretation: CSORT's seed-1999 peak depends on the coupled adjacent-scale objective, not either pair alone.
  - Recommendation: close isolated scale-pair variants.

## 6. Crash Info (if crashed)
  - No crash. Normal early stop.
================================================================================
