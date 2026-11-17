================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M58-DET-DRP | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M58-DET-DRP
  - Config: configs/Quard/det_drp/model_base1_quard2_c2f_enc_lite_posA_l1_det_drp.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-07 17:03 | Finished: 2026-08-10 00:31 | Duration: ~2.3d
  - State: done_earlystop (log 无 Early stopping 字样, 25 val 后中断 — server-6 外部资源干扰)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.498  | 17      |
  | Acc@50   | 0.552  | 17      |
  | spmIOU   | 0.460  | 17      |

## 3. Convergence Summary
  - Best first reached at: epoch 17 (0.498)
  - Subsequent no_improve epochs: 8 (ep18-25, 未触发早停阈值但 val 走完 25 后中断)
  - Final epoch best: mIOU=0.498 (存档) vs 末轮 val 0.484 回落
  - 序列: 0.262→0.385→0.389→0.427→0.447→0.450→0.459→0.462→0.479→0.479→0.490→0.488→0.493→0.483→0.494→0.497→**0.498**→0.496→0.497→0.492→0.496→0.493→0.489→0.493→0.484
  - 收敛形态: 快速上升后 0.490-0.498 高位平台, 峰值 0.498 后波动未刷新, 末段回落

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0086 (有效)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0032 (失败)
  - vs D1-detail (0.5003): γ = -0.0023 (detail message 独立上, det_drp 反而低)
  - 注: M58 是 detail message_type 叠加在 DRP(champion) 基础上 — 结果 0.498 < DRP 0.5012 且 < detail 0.5003

## 5. Conclusion
  - 结论: [失败] — detail message 在 DRP champion 基础上不叠加, 反降
  - 解释: DRP 本身是"context-only 回写"(路由死代码已删), detail message 把回写改成
    inst_feats 与 cluster_message 的残差。DRP+detail 0.498 低于 DRP 0.5012 和 detail
    0.5003, 说明 detail 残差变换与 DRP 的简洁回写路径不协同 — 与 M66-DET-HCG
    (detail×HCG 负交互) 同模式: detail 是 message 语义变换, 与已有效的回写/交付
    机制叠加普遍负交互。
  - 对后续实验设计的建议:
    1. 确认 detail 独立有效 (D1=0.5003), 但与任何"正确化"机制 (DRP/HCG) 组合均为负 —
       detail 应保持独立使用或只与缺陷机制组合 (M75/M76 的 iter×detail / reag×detail)。
    2. M58 为 server-6 上 2×2 网格中的 detail×DRP 格, 已闭合 (负)。
    3. 后续不再设计 detail×{DRP/HCG} 组合。

## 6. Crash Info
  - Error type: NOT crashed — 中断 (log 无 Early stopping, 25 val 后停止, 疑似 server-6 外部资源干扰)
  - Auto-fix attempt: N
================================================================================
