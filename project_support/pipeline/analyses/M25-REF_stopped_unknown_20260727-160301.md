================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M25-REF | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M25-REF
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_refine.yaml
  - Label: MultiScale_Gather_Refine — iterative context refinement instead of single-pass C2F_ClusterAttn_Lite
  - Server: server-4 | GPU: 1
  - Started: 2026-07-27 00:03 | Finished: ~2026-07-27 15:55 | Duration: ~15.9h
  - State: stopped_unknown (process disappeared mid-training, PID file DEAD, log stopped at epoch 26)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4892 | 25      |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (Best from pipeline_monitor prior tick; process died during epoch 26 training)

## 3. Convergence Summary
  - Best first reached at: epoch 25 (mIoU=0.4892)
  - No_improve at stop: 8/10 (approaching early-stop threshold)
  - spmIOU sequence (26 validation points): 0.306→0.348→0.382→0.410→0.407→0.424→0.421→0.442→0.441→0.445→0.450→0.448→0.447→0.452→0.445→0.455→0.450→0.449→0.451→0.447→0.448→0.452→0.449→0.444→0.444→0.446
  - Best spmIOU=0.455 at epoch ~16, declining to 0.444-0.446 at end
  - Convergence pattern: gradual rise to spmIOU ~0.45, then oscillation and decline. mIoU peaked at 0.4892 (epoch 25) before process died at epoch 26 training.

## 4. Comparison
  - vs baseline (model_base1=0.4894): gamma = -0.0002 (持平, 略低于 baseline)
  - vs champion (posA_l1=0.5012): gamma = -0.0120 (significant degradation)
  - vs M17-ORT (0.5005): gamma = -0.0113
  - vs D1-detail (0.5003): gamma = -0.0111
  - vs M16-CSR (cluster self-refine=0.4875): gamma = +0.0017 (marginally better than CSR)
  - The refine mechanism (MultiScale_Gather_Refine) is strictly worse than the single-pass context injection (champion)

## 5. Conclusion
  - 结论: [失败] — iterative refinement (MultiScale_Gather_Refine) degrades performance to baseline level
  - 解释: Replacing single-pass C2F_ClusterAttn_Lite with iterative gather+refine breaks the effective context injection pathway. The refine mechanism appears to over-smooth or dilute the cluster context signal when applied iteratively. This is consistent with other mechanism substitutions that degrade champion: max-pool (0.4910), cross-scale attention (0.4954), hybrid message (0.4898). Single-pass context injection via cluster_attn appears to be the uniquely effective pattern — every attempt to replace or augment it has fallen below 0.4960.
  - 对后续实验设计的建议:
    (a) 放弃 refine/gather 方向 — 两次 refine 尝试 (M16-CSR=0.4875, M25-REF=0.4892) 均不及 baseline
    (b) context injection 机制保持单次 cluster_attn，不做迭代/替换
    (c) 探索方向应聚焦于: 更好的 cluster token 质量 (ORT → all-scale), 更好的 loss (GIoU), 或更好的 attention (multi-head)

## 6. Crash Info (if crashed)
  - Error type: stopped_unknown (process disappeared without explicit crash log)
  - Error message excerpt: N/A — process died mid-epoch-26 without error signature. Log last modified 15:55.
  - Auto-fix attempt: N/A — process disappeared silently, no code fix needed. Queue auto-rotated to M27-ORT-W5.
================================================================================
