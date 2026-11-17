================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M67-PSR-HCG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M67-PSR-HCG
  - Config: configs/Quard/psr_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_psr_hcg.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-07 20:26 | Finished: 2026-08-10 00:31 | Duration: ~2.2d
  - State: done_earlystop (log 无 Early stopping 字样, 23 val 后中断 — server-6 外部资源干扰)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.496  | 14      |
  | Acc@50   | 0.552  | 14      |
  | spmIOU   | 0.459  | 14      |

## 3. Convergence Summary
  - Best first reached at: epoch 14 (0.496)
  - Subsequent no_improve epochs: 9 (ep15-23, 未触发早停阈值但 val 走完 23 后中断)
  - Final epoch best: mIOU=0.496 (存档) vs 末轮 val 0.492
  - 序列: 0.336→0.381→0.398→0.426→0.454→0.456→0.468→0.479→0.484→0.485→0.488→0.491→0.492→**0.496**→0.490→0.494→0.496→0.494→0.492→0.492→0.495→0.488→0.492
  - 收敛形态: 快速上升后 0.488-0.496 高位平台, 峰值 0.496 后波动, 未刷新

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0066 (有效)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0052 (失败)
  - vs PSR alone (M63=0.4964): γ = -0.0004 (PSR×HCG ≈ PSR 单轴 — 无叠加)
  - vs HCG alone (M65=0.5002): γ = -0.0042 (组合低于 HCG 单轴)

## 5. Conclusion
  - 结论: [失败] — PSR×HCG 组合无增益, 与 detail×HCG 负交互同模式
  - 解释: PSR (per-scale residual readback) × HCG (正确多尺度交付) 0.496 ≈ PSR 单轴
    0.4964, 低于 HCG 单轴 0.5002。HCG 已把正确对齐的多尺度 context 精确交付到点,
    PSR 的 per-scale 残差 message 叠加无增量 — 与 detail×HCG (M66=0.4955) 模式一致:
    message 语义变换 × HCG 正确交付普遍负交互或无叠加。
  - 对后续实验设计的建议:
    1. server-6 网格中 message×HCG 格 (detail×HCG M66, PSR×HCG M67, SSP×HCG M68)
       全部闭合且 ≤ HCG 单轴 — 确认 HCG 交付轴上 message 变换无叠加价值。
    2. PSR 单轴 (M63=0.4964) 是相对最强的 message 变换之一, 但已与 HCG 组合过无增益,
       不再投入。

## 6. Crash Info
  - Error type: NOT crashed — 中断 (log 无 Early stopping, 23 val 后停止, 疑似 server-6 外部资源干扰)
  - Auto-fix attempt: N
================================================================================
