================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M154-CTF-HCG-CSORT-GSC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M154-CTF-HCG-CSORT-GSC
  - Config: configs/Quard/ctf_hcg_csort_gsc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_gsc.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-31 19:50:32 | Finished: 2026-09-01 09:53:36 | Duration: ~14.1h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | 24/50   |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  Secondary metrics are unavailable because the monitor did not pull a local log.

## 3. Convergence Summary
  - Best recorded by the terminal ledger: mIoU=0.4930 at 24/50.
  - Early-stopped after 13 consecutive validations without a new best.
  - Adding a global K=1 scale weakened rather than extended the local hierarchy.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0036.
  - vs champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0090.

## 5. Conclusion
  - Conclusion: [failed].
  - Interpretation: scene-global context is too coarse for the cluster readback path and dilutes object-local information.
  - Recommendation: close the global-scale extension branch.

## 6. Crash Info (if crashed)
  - No crash. Normal early stop.
================================================================================
