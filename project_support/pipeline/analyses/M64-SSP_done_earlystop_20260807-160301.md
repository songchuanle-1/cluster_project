================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M64-SSP | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M64-SSP
  - Config: configs/Quard/ssp/model_base1_quard2_c2f_enc_lite_posA_l1_ssp.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-07T00:03:23 | Finished: 2026-08-07T15:34:00 | Duration: ~15.5h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4928 | 16      |
  | Acc@50   | 0.545  | 16      |
  | spmIOU   | 0.456  | 16      |
  (log 序列 ep1→26: 0.319→0.493(ep16 峰值)→0.479, 精确 best 0.4928 取自 monitor)

## 3. Convergence Summary
  - Best first reached at: epoch 16 (0.493 mIOU, Acc_50=0.545, spmIOU=0.456)
  - Subsequent no_improve epochs: 10 (ep17-26 均未刷新 best)
  - Early stopping at: epoch 26 (best=0.4928)
  - 收敛形态: 快速上升 (ep1-16 0.319→0.493) 后进入 0.479-0.486 平台, ep17 起 10 连不刷
    best, ep24-26 0.481/0.481/0.479 三连缓降 → 正常早停, 非 crash.

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = +0.0034 (有效)
  - vs current champion (posA_l1/DRP, 0.5012): γ = -0.0084 (低于 champion)
  - 同批 per-scale 机制对比: M64-SSP 0.4928 vs M63-PSR 0.4964 vs M62-ORTG 0.4979
    (M62-ORTG > M63-PSR > M64-SSP; SSP 为本批中最低)

## 5. Conclusion
  - 结论: [有效] (vs baseline) / 未超 champion
  - 解释: per-scale projection readback (投影放置轴补格) 机制单独使用有效 (+0.0034 vs
    baseline), 但低于同批 PSR/ORTG, 且距 champion 0.5012 差 0.0084, 未构成新的路线突破.
  - 对后续实验设计的建议: SSP 单独不优先; 队列中已有 M68-SSP-HCG (SSP 与 HCG 组合) 待跑,
    可验证 SSP 与 HCG 的协同; 若组合亦不升, 则放弃 SSP 路线.
================================================================================
