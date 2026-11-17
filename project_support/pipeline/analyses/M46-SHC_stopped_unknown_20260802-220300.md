================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M46-SHC | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M46-SHC
  - Config: configs/Quard/shc/model_base1_quard2_c2f_enc_lite_posA_l1_shc.yaml
  - Server: server-4 | GPU: ? (process disappeared)
  - Started: 2026-08-02 (exact time unknown) | Finished: 2026-08-02 21:25 | Duration: ~15-20h (est.)
  - State: stopped_unknown (process vanished mid-training, no checkpoint dir on server-4)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4946 | ~23     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ~23 (estimated)
  - Process vanished before completion; no checkpoint dir found on server-4
  - Final epoch best: mIoU=0.4946

## 4. Comparison
  - vs baseline (model_base1): gamma = +0.0052 — marginal improvement
  - vs champion (posA_l1): gamma = -0.0066 — clearly worse
  - vs M32-DRP (0.5012): gamma = -0.0066

## 5. Conclusion
  - Conclusion: [FAILED] — split-head partial update underperforms full-dimension update
  - Explanation: Restricting cluster context to half feature channels hurts (-0.0066 vs champion). Points benefit from full-dimension context injection; "overwrite" hypothesis not supported.
  - Recommendation: Abandon split-head/channel-partitioning. Focus on readback expressiveness (M48-BIL, M49-NLR, M50-DGC).

## 6. Crash Info
  - Error type: process_disappeared (no OOM, no Python traceback)
  - Error message: N/A — process vanished silently
  - Auto-fix attempt: N — metrics sub-champion, restart not justified
================================================================================
