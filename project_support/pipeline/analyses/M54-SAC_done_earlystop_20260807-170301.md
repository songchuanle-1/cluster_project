================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M54-SAC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M54-SAC
  - Config: configs/Quard/sac/model_base1_quard2_c2f_enc_lite_posA_l1_sac.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-04T17:25:00 | Finished: 2026-08-07T17:03:00 | Duration: ~3d
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4892 | ~18     |
  | Acc@50   | 0.541  | ~18     |
  | spmIOU   | 0.452  | ~18     |
  (best 0.4892 取自日志 Early stopping at epoch 27: no improvement for 10 epochs;
   Acc_50/spmIOU 取自该 epoch 验证行 mIOU: 0.489 Acc_50: 0.541 spmIOU: 0.452)

## 3. Convergence Summary
  - Best first reached at: epoch ~18 (mIOU 0.489, Acc_50 0.541, spmIOU 0.452)
  - Subsequent no_improve epochs: 10 (ep18-27 未刷新)
  - Early stopping at: epoch 27 (best=0.4892)
  - 收敛形态: 快速上升后 0.48-0.49 平台震荡, 后 10 epoch 持续不刷 best, 末尾 0.482-0.485
    缓降 → 正常早停, 非 crash. 进程消失由优雅早停退出引起, 非异常.

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = -0.0002 (≈0 持平)
  - vs current champion (posA_l1/DRP, 0.5012): γ = -0.0120 (低于 champion)
  - 同批 server-6 GPU7 slot 1-3 对比: M52-CCR 0.4948 / M53-VAC 0.4889 / M54-SAC 0.4892
    (SAC 与 VAC 持平, 均低于 CCR; 三变体均未超过 champion)

## 5. Conclusion
  - 结论: [持平] (vs baseline) / 未超 champion
  - 解释: Spatial-Aware Cluster Context (空间感知簇上下文) 机制与 baseline 持平, 无独立
    增益; 与 M53-VAC (0.4889) 同为 server-6 批中表现较弱者, 仅 M52-CCR (0.4948) 略高于
    baseline.
  - 对后续实验设计的建议: SAC 路线不优先, 不再扩展; server-6 三个 slot 变体 (CCR/VAC/SAC)
    中 CCR 相对最有效, 后续可关注 CCR 组合方向. SAC 终态后空出 slot, M58-DET-DRP 已补位.
================================================================================
