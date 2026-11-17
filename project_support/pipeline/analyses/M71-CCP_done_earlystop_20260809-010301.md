================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M71-CCP | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M71-CCP
  - Config: configs/Quard/ccp/model_base1_quard2_c2f_enc_lite_posA_l1_ccp.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-08 08:26 | Finished: 2026-08-09 01:00 | Duration: ~16.5h
  - State: done_earlystop (log: "Early stopping at epoch 28: no improvement for 10 epochs (best=0.4934)")

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4934 | ~19     |
  | Acc@50   | 0.546  | ~19     |
  | spmIOU   | 0.459  | ~19     |

## 3. Convergence Summary
  - Best first reached at: epoch ~19 (0.4934, 上 tick ep27 时 no_impr=8/10)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 28)
  - Convergence form: 快速上升后 0.477-0.493 高位平台, 峰值 0.4934 后
    10 epoch 未刷新 best, 末 ep28 val mIOU 0.480 左右回落

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0040 (有效, 但增益偏弱)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0078 (失败, 距 champion 0.0078)
  - vs HCG (M65=0.5002): γ = -0.0068 (低于)
  - vs detail (D1=0.5003): γ = -0.0069 (低于)

## 5. Conclusion
  - 结论: [失败] (有正增益但未破顶, 且增益弱于 HCG/detail 两轴)
  - 解释: CCP (粗簇全局上下文逐级注入细簇, 零参数新信息路径) 单独只贡献
    γ=+0.0040, 说明"token 质量"轴 (CCP) 独立上限 ~0.4934, 远低于
    HCG/detail 单轴的 ~0.5003。粗→细逐级注入的上下文对细簇 token 的
    改善幅度有限 — 上下文信息细簇通过 cluster_attn 回写本已吸收大部分。
  - 对后续实验设计的建议:
    1. M72-CCP-HCG (CCP × HCG 正确交付, running) 是关键组合 — 若 >0.5012
       则 CCP 增益在"正确多尺度交付"下才被放大; 若 ≈HCG 单独则 CCP 与
       HCG 冗余, token 质量轴后续可降级。
    2. M73-CCP-DET (CCP × detail 残差 message, waiting) 与 M74-CCP-HCG-DET
       (三维满格) 继续排队跑, 补 {token质量}×{message} 因子格。
    3. 若组合格全部 ≤0.5012, CCP 轴判定为弱轴, 故事线退回 champion (posA_l1
       0.5012) + detail/HCG 组合轴 (D1/M65 系列), 不再投入 CCP 方向。
================================================================================
