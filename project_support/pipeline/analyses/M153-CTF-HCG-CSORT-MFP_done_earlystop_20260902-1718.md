================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M153-CTF-HCG-CSORT-MFP | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M153-CTF-HCG-CSORT-MFP
  - Config: configs/Quard/ctf_hcg_csort_mfp/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mfp.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-31 07:45:52 | Finished: 2026-08-31 23:50:28 | Duration: ~16.1h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5000 | 22/50   |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  Secondary metrics are unavailable because the monitor did not pull a local log.

## 3. Convergence Summary
  - Best recorded by the terminal ledger: mIoU=0.5000 at 22/50.
  - Early-stopped after 13 consecutive validations without a new best.
  - The combined objective approached but did not exceed the CSORT champion.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0106.
  - vs champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0020.
  - vs M119-MFP=0.5020: gamma = -0.0020.

## 5. Conclusion
  - Conclusion: [effective versus baseline, failed to combine].
  - Interpretation: CSORT and masked feature prediction do not stack; both appear to regularize the same cluster-token bottleneck.
  - Recommendation: close the CSORT x MFP combination branch.

## 6. Crash Info (if crashed)
  - No crash. Normal early stop.
================================================================================
