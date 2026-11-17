================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M159-CTF-HCG-CSORT-GEO | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M159-CTF-HCG-CSORT-GEO
  - Config: configs/Quard/ctf_hcg_csort_geo/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_geo.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-09-02 04:00:41 | Finished: 2026-09-02 14:06:15 | Duration: ~10.1h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4840 | 18/50   |
  | Acc@50   | N/A    | N/A     |
  | spmIOU   | N/A    | N/A     |
  Secondary metrics are unavailable because the monitor did not pull a local log.

## 3. Convergence Summary
  - Best recorded by the terminal ledger: mIoU=0.4840 at 18/50.
  - Early-stopped after 11 consecutive validations without a new best.
  - Geometry injection caused the largest recent degradation and fell below the no-cluster baseline.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = -0.0054.
  - vs champion (M95-CTF-HCG-CSORT=0.5020): gamma = -0.0180.

## 5. Conclusion
  - Conclusion: [failed].
  - Interpretation: direct centroid/radius residual injection corrupts rather than enriches cluster tokens; token geometry is not the missing information bottleneck in this form.
  - Recommendation: close direct geometry injection. Keep M160-GEO-SH only as the pre-registered content-versus-capacity control.

## 6. Crash Info (if crashed)
  - No crash. Normal early stop.
================================================================================
