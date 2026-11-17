================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M41-CTF | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M41-CTF
  - Config: configs/Quard/ctf/model_base1_quard2_c2f_enc_lite_posA_l1_ctf.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-07-30 14:03:58 | Finished: 2026-07-31 20:05:44 | Duration: ~30h
  - State: done_earlystop (no improvement for 10 epochs, best=0.4995)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4995 | 16      |
  | Acc@50   | 0.552  | 16      |
  | spmIOU   | 0.462  | 16      |

## 3. Convergence Summary
  - Best first reached at: epoch 16 (2026-07-31 07:39)
  - Subsequent no_improve epochs: 10 (epochs 17-26)
  - Final epoch best: mIoU=0.4995 vs historical best=0.4995
  - 序列: 0.308→0.379→0.407→0.421→0.445→0.459→0.477→0.476→0.485→0.490→0.485→0.485→0.493→0.488→0.491→**0.500**→0.497→0.485→0.495→0.497→0.495→0.490→0.492→0.492→0.492→0.491
  - 收敛形态: 快速上升至 epoch 16 触顶(0.4995)，此后持续震荡下降无法恢复，epoch 26 触发 no_improve=10 早停。峰值后在 0.485-0.497 区间波动，典型过拟合型收敛。

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0101 (有效, 显著超越 baseline)
  - vs champion (model_base1_quard2_c2f_enc_lite_posA_l1 0.5012): γ = -0.0017 (接近但未超越)
  - vs M40-SWI (running, current best 0.4970): γ = +0.0025 (CTF > SWI so far)
  - vs M26-ORT-HYB (stopped_unknown 0.4998): γ = -0.0003 (几乎持平)
  - vs M17-ORT (done_earlystop 0.5005): γ = -0.0010

## 5. Conclusion
  - 结论: [有效但未突破] — 显著优于 baseline (+0.0101)，距 champion 仅 0.0017
  - 解释: Cluster Token FFN (per-scale 2-layer FFN+residual+LayerNorm refines cluster tokens before readback) 能提升 token 质量至接近 champion 水平，但无法突破 0.5012 天花板。token quality hypothesis 部分证实：FFN 精炼 token 有效(+0.0101 vs baseline)，但单靠 token 质量提升不足以推动 champion 再提升——瓶颈可能不在 token 质量而在 readback/融合机制。
  - 对后续实验设计的建议: CTF 机制本身有价值(token 精炼)但不单独突破。建议考虑与有效机制组合(M40-SWI完成后再评估)。当前 waiting 队列 M42-WCA/M43-CLN/M44-CSF 均在探索不同维度的瓶颈(channel aggregation/cluster token normalization/cross-scale fusion)，方向合理。

## 6. Crash Info
  - NOT crashed — clean early-stop exit
  - Note: Process disappeared between epoch 26 completion and next tick check. GPU 1 subsequently occupied by another user (lyb, gdn2_eval).
================================================================================
