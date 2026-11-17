================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M69-ITER | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M69-ITER
  - Config: configs/Quard/iter/model_base1_quard2_c2f_enc_lite_posA_l1_iter.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-08 04:03 | Finished: 2026-08-09 00:00 | Duration: ~20h
  - State: done_earlystop (log: "Early stopping at epoch 29: no improvement for 10 epochs (best=0.4978)")

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4978 | ~20     |
  | Acc@50   | 0.552  | ~20     |
  | spmIOU   | 0.461  | ~20     |

## 3. Convergence Summary
  - Best first reached at: epoch ~20 (mIOU 0.497-0.498 峰值序列)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 29)
  - Convergence form: 快速上升 (ep1-11 0.302→0.489) 后 0.483-0.498 高位平台
    震荡, 峰值 0.498 后 9 epoch 未再刷新 best (末 ep29 val mIOU 0.483 回落)

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0084 (有效)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0034 (失败, 距 champion 0.0034)
  - vs detail (D1=0.5003): γ = -0.0025 (低于)
  - vs HCG (M65=0.5002): γ = -0.0024 (低于)

## 5. Conclusion
  - 结论: [失败] (有正增益但未破顶)
  - 解释: 迭代 readback (2轮回写门控融合, cluster token 不变) 达 0.4978,
    确认"多轮回写"不带来新的上限 — 第二轮 gather 的信息量被第一轮已吸收,
    门控融合 (iter_gate) 接近线性叠加而非非线性精化。γ=+0.0084 说明迭代
    方向本身不差, 但 0.4978 < champion 0.5012, 迭代单轴不足以破顶。
  - 对后续实验设计的建议:
    1. {迭代}×{message} 组合 (M75-DET-ITER, M76-DET-REAGG 已在队列) 继续跑 —
       detail 残差 message 已被证明独立有效 (+0.0109), 迭代×残差 是两轴首次正交,
       若组合 >0.5012 则迭代轴的增量在 message 精化而非 round 数。
    2. M70-REAGG (迭代+重新聚合 cluster token) 是迭代轴的"cluster 进化"变体 —
       本轮结果 (M69 固定 token 2轮) 与 M70 (token 随迭代更新) 构成迭代轴
       内部的对比, M70 若 >0.4978 则 cluster token 进化是迭代增益来源。
    3. 迭代 round 数 (2→3) 不做 — 若 2 轮已饱和, 3 轮属数值扩展非结构变化,
       有调参气味。迭代轴后续只看组合格。
================================================================================
