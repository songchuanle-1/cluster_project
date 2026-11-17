================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M16-CSR | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M16-CSR
  - Config: configs/Quard/csr/model_base1_quard2_c2f_enc_lite_posA_l1_csr.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-07-21 13:38 | Finished: 2026-07-22 09:01 | Duration: ~19.4h
  - State: done_earlystop (no improvement for 10 epochs)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4875 | ~18     |
  | Acc@50   | 0.529  | ~18     |
  | spmIOU   | 0.444  | ~18     |

## 3. Convergence Summary
  - Best first reached at: epoch ~18 (2026-07-22 03:04)
  - Subsequent no_improve epochs: 10 (epochs 21-30)
  - Final epoch best: mIoU=0.4787 vs historical best=0.4875
  - Convergence pattern: rapid rise from 0.325→0.487 in first 18 epochs, then oscillation 0.47-0.487 with no further improvement. Early stopped at epoch 30.

## 4. Comparison
  - vs baseline (model_base1): γ = -0.0019 (0.4875 vs 0.4894) → [失败]
  - vs champion (posA_l1): γ = -0.0137 (0.4875 vs 0.5012) → [失败]
  - vs refine (C3-refine): γ = -0.0056 (0.4875 vs 0.4931) → [失败]
  - Cluster Self-Refine mechanism adds complexity but degrades performance below baseline.

## 5. Conclusion
  - 结论: [失败] — Cluster Self-Refine (CSR) does not improve over baseline
  - 解释: Adding self-refinement on cluster tokens (extra attention on top of cluster_attn) introduces noise without improving context quality. Best 0.4875 < baseline 0.4894, confirming the refine family (C3=0.4931, M16=0.4875) offers no gain.
  - 对后续实验设计的建议: 放弃 refine/self-refine 方向。证据充分: C3-refine (MultiScale_Gather_Refine)=0.4931, M16-CSR (Cluster Self-Refine)=0.4875 — 均未超越 baseline。继续聚焦 context/detail 信号质量和尺度消融。

## 6. Crash Info
  - N/A (clean early stop)
================================================================================
