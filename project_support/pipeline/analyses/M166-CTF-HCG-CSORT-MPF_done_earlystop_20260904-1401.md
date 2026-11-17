================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M166-CTF-HCG-CSORT-MPF | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M166-CTF-HCG-CSORT-MPF
  - Config: configs/Quard/ctf_hcg_csort_mpf/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mpf.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-09-03 20:11:41 | Finished remotely: 2026-09-04 11:18:09
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4899 | 13      |
  | Acc@50   | 0.540  | 13      |
  | spmIOU   | 0.4570 | 13      |

## 3. Convergence Summary
  - Best first reached at epoch 13.
  - Early stopping occurred at epoch 23 after 10 epochs without improvement.
  - Final mIoU was 0.4840; no traceback or CUDA error was present.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = +0.0005.
  - vs M161 foreground retrieval (0.4920): gamma = -0.0021.
  - vs champion (M95=0.5020): gamma = -0.0121.

## 5. Conclusion
  - Conclusion: [flat versus baseline, failed].
  - Interpretation: projecting query states back onto predicted point support
    adds reciprocal recurrence but no meaningful grounding gain.
  - Recommendation: close the MPF reciprocal-feedback branch.

## 6. Crash Info (if crashed)
  - No crash. Normal training early stop.
================================================================================
