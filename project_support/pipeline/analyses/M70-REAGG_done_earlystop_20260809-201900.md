================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M70-REAGG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M70-REAGG
  - Config: configs/Quard/reag/model_base1_quard2_c2f_enc_lite_posA_l1_reag.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-09 00:03 | Finished: 2026-08-09 ~20:00 | Duration: ~20h
  - State: done_earlystop (log: "Early stopping at epoch 28: no improvement for 10 epochs (best=0.4983)")

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4983 | ~18     |
  | Acc@50   | 0.551  | ~18     |
  | spmIOU   | 0.458  | ~18     |
  (best epoch ~18; 末 ep28 val mIOU 0.480 回落, spmIOU 0.442)

## 3. Convergence Summary
  - Best first reached at: epoch ~18 (0.4983)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 28)
  - Final epoch best: mIOU=0.4983 (存档) vs 末轮 val 0.480 回落
  - Convergence form: 快速上升后 0.490-0.498 高位平台, 峰值 0.4983 后 10 epoch 未刷新 best

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0089 (有效)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0029 (接近但未破顶)
  - vs M69-ITER (0.4978): γ = +0.0005 (REAGG 略优于纯迭代, 但差距微小)
  - vs M65-HCG (0.5002): γ = -0.0019 (REAGG 缺陷版低于 HCG 正确交付)
  - 注: M70 存在**双缺陷** — _reaggregate lvl>0 取前 K 个点槽 (非真实上一级 token)
    + _cluster_to_points 继承 Lite 准单尺度交付

## 5. Conclusion
  - 结论: [有效但未破顶] — REAGG 方向有潜力, 但从未被正确检验
  - 解释: M70-REAGG 在「重聚合 lvl>0 任意点槽 + 准单尺度交付」双缺陷下仍达 0.4983
    (距 champion 仅 0.0029), 说明 round-2 迭代+重新聚合机制本身有正向信号; 但两个
    缺陷使 round-2 的 mid/coarse cluster token 语义噪声、交付错配, 无法确定其真实上限。
  - 对后续实验设计的建议:
    1. M79-REAG-CASC (队列中) 修复重聚合缺陷: round-2 级联正确聚合, 单一变量对照 M70。
    2. M78-REAGG-HCG (队列中) 修复交付缺陷: HCG 组合 gather 正确多尺度交付。
    3. M80-REAG-CASC-HCG (本 tick 设计) 双修复满格: 检验 REAGG 完整修复后是否破顶。
    4. 若 M80 ≈ M70 → 中/粗尺度 round-2 重聚合无增益, 与 fine-dominant 观察一致,
       该轴闭合; 若 M80 > 0.5012 → REAGG 方向成为新破顶主候选。
================================================================================
