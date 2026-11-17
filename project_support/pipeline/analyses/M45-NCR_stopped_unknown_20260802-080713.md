================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M45-NCR | State: stopped_unknown (early_stop)
================================================================================

## 1. Basic Info
  - ID: M45-NCR
  - Config: configs/Quard/ncr/model_base1_quard2_c2f_enc_lite_posA_l1_ncr.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-01 11:03 | Finished: 2026-08-02 07:27 | Duration: ~20h
  - State: stopped_unknown (early stopping triggered at epoch 30)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4980 | 20      |
  | Acc@50   | 0.539  | 30      |
  | spmIOU   | 0.446  | 30      |

## 3. Convergence Summary
  - Best first reached at: epoch 20 (0.4980)
  - Subsequent no_improve epochs: 10 (early-stop at epoch 30)
  - Final epoch best: mIoU=0.4980 vs historical best=0.4980
  - 收敛形态: 缓慢上升至 epoch 20 达峰，之后平台+轻微震荡 (0.485-0.498)

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = +0.0086 (有效)
  - vs champion (posA_l1, 0.5012): γ = -0.0032 (接近但未超过)
  - vs DRP baselines: M32-DRP(0.5012), M17-ORT(0.5005) — NCR 略低
  - 机制: 用 attention-based soft cluster assignment (ncr_topk=4) 替换 hard gather
  - 同类 readback 变体比较: M42-WCA(0.4890), M41-CTF(0.4995), M45-NCR(0.4980)

## 5. Conclusion
  - 结论: [有效但未超越] — soft cluster readback 有收益但不如 hard-gather DRP
  - 解释: NCR 用 attention 做 soft assignment 替代 hard top-K gather，证明
    soft readback 可行 (+0.0086 vs baseline)，但不如 DRP 的 hard gather。
    可能 soft assignment 引入的 attention noise 稀释了 cluster context 的信息密度。
  - 对后续实验设计的建议: NCR 方向有价值但需要更强的 readback 机制。
    M48-BIL (bilinear) 和 M49-NLR (nonlinear) 已在队列中，预计可超越 NCR。

## 6. Crash Info
  - Error type: process_silent_death
  - Error message excerpt: 进程消失(3次确认)，推测 OOM 或进程被系统 kill
  - Auto-fix attempt: N/A (early-stop 已触发，无需重跑)
================================================================================
