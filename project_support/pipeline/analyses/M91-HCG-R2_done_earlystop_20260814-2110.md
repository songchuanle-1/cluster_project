================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M91-HCG-R2 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M91-HCG-R2
  - Config: configs/Quard/hcg_r2/model_base1_quard2_c2f_enc_lite_posA_l1_hcg_s42.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-14 06:09 (log train_..._hcg_s42_20260814_060925.log) | Finished: 2026-08-14 21:07 | Duration: ~15h
  - State: done_earlystop (no_improve=11/10, 连续 11 epoch 未刷新 best, monitor kill PID=1225821)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4963 | 24      |
  | Acc@50   | 0.550  | 24      |
  | spmIOU   | 0.459  | 24      |

## 3. Convergence Summary
  - Best first reached at: epoch 24 (mIoU 0.4963, log 17:53)
  - Subsequent no_improve epochs: 11 (killed at patience=10, ep26)
  - Trajectory: 前 23 epoch 爬升触顶 0.496 (末 5 验证: 0.485/0.490/0.484/0.491), 触顶后验证在
    0.483-0.491 区间回落震荡, 未再刷新 best, 判定早停。
  - 与 M65-HCG (seed 1999) 对比: 收敛形态相近但峰值低 0.0039。

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0069 (有效)
  - vs current champion (posA_l1 0.5012): γ = -0.0049 (未破顶)
  - vs M65-HCG (0.5002, seed 1999): γ = -0.0039 — **同一 HCG 配置换 seed=42 掉点 0.0039**,
    复现性同样存疑
  - vs M90-CTF-HCG-S3 (0.4940, seed 123): γ = +0.0023 (HCG alone seed42 > CTF×HCG seed123)
  - vs M89-CTF-HCG-R2 (seed 42, running 0.4830@ep12): 同 seed=42 系, 待终态

## 5. Conclusion
  - 结论: [有效] (优于 baseline +0.0069) 但 [未破顶] 且 seed 敏感性确认
  - 解释: M91 是 M65-HCG (0.5002, seed 1999) 的 seed=42 复现检查, 结果 0.4963 低于 M65 达
    0.0039。与 M90 (CTF×HCG seed123 掉 0.0072) 合并看, **seed=1999 的高分含明显 seed 有利性**:
    HCG 轴真实水平 ~0.496-0.500, champion 架构在 seed1999 下普遍 ~0.5005-0.5012 的观点
    进一步强化。seed 方差 ~±0.004-0.007, 任何"破顶"声称需 ≥0.005 且最好跨 seed 验证。
  - 对后续实验设计的建议: (1) 已入队的 M97-CHAMP-ORT / M95-CSORT / M96-2LAY 均用 seed=1999
    结构首筛 — 结果需按 seed 方差基准解释, 破 0.5012 才视为真破顶; (2) 若某变体破顶,
    需 seed 42 复现验证; (3) 多样性轴 (ORT/CSORT) 若在 seed1999 上与 champion 持平而非破顶,
    与 M90/M91 一起构成"0.5012 为 seed 有利值"的完整证据。
================================================================================
