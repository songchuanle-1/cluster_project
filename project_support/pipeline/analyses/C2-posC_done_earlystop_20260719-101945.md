================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: C2-posC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: C2-posC
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posC.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-07-18T09:22 | Finished: 2026-07-19T10:15 | Duration: ~25h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4968 | ~18     |
  | Acc@50   | 0.505  | —       |
  | spmIOU   | 0.450  | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ~18 (0.4968)
  - Subsequent no_improve epochs: 5 (0.4955→0.4954→0.4919→0.4953→ep23 0.4897)
  - Final epoch 23 best: 0.4897 vs historical best=0.4968
  - 收敛形态: 逐步上升至 ep18 见顶，之后震荡下行

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0074 (有效)
  - vs champion (PosA_l1=0.5012): γ = -0.0044 (未超越)
  - vs old posC (0.4952): γ = +0.0016 (略有改善)
  - vs posB (0.4953): γ = +0.0015

## 5. Conclusion
  - 结论: [有效] — 再次确认 posC > baseline 但 < posA
  - 解释: 两次独立 run (0.4952 / 0.4968) 均低于 posA (0.5012)，posA 编码优于 posC 一致成立
  - 对后续实验设计的建议: 已确认 posA > posC, posC 路线不看

## 6. Crash Info
  - 无 crash, 正常运行
================================================================================
