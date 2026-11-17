================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M43-CLN | State: stopped_unknown (early_stop)
================================================================================

## 1. Basic Info
  - ID: M43-CLN
  - Config: configs/Quard/cln/model_base1_quard2_c2f_enc_lite_posA_l1_cln.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-01 00:38 | Finished: 2026-08-02 05:47 | Duration: ~29h
  - State: stopped_unknown (early stopping triggered at epoch 25)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | 15      |
  | Acc@50   | 0.536  | 25      |
  | spmIOU   | 0.446  | 25      |

## 3. Convergence Summary
  - Best first reached at: epoch 15 (0.4930)
  - Subsequent no_improve epochs: 10 (early-stop at epoch 25)
  - Final epoch best: mIoU=0.4930 vs historical best=0.4930
  - 收敛形态: 快速上升到 epoch 15 后进入平台期，epoch 15-25 在 0.485-0.493 间震荡

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = +0.0036 (微弱有效)
  - vs champion (posA_l1, 0.5012): γ = -0.0082 (远低于 champion)
  - vs DRP baselines: M17-ORT(0.5005), M32-DRP(0.5012) — CLN 远低于
  - 机制: DRP + Cluster LayerNorm (cluster_mode=drp_cln)

## 5. Conclusion
  - 结论: [失败] — LayerNorm on cluster tokens is insufficient
  - 解释: 在 DRP pipeline 中对 cluster tokens 加 LayerNorm 只带来 +0.0036 vs baseline，
    但远低于 champion DRP variants (0.5012)。Cluster LayerNorm 是纯数值分布调整，
    不改变信息流路径，属于 Phase 1.6 调参气味信号 #2/#3。
  - 对后续实验设计的建议: 放弃 CLN 方向。验证了"仅加 normalization 不改变信息流"
    的假设，确认需要结构性机制变更而非数值调整。

## 6. Crash Info
  - Error type: process_silent_death
  - Error message excerpt: 进程消失(3次确认)，推测 OOM 或进程被系统 kill
  - Auto-fix attempt: N/A (early-stop 已触发，无需重跑)
================================================================================
