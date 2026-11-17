================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M68-SSP-HCG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M68-SSP-HCG
  - Config: configs/Quard/ssp_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_ssp_hcg.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-07 22:09 | Finished: 2026-08-10 00:31 | Duration: ~2.1d
  - State: done_earlystop (log: "Early stopping at epoch 23: no improvement for 10 epochs (best=0.4965)")

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4965 | 13      |
  | Acc@50   | 0.550  | 13      |
  | spmIOU   | 0.461  | 13      |

## 3. Convergence Summary
  - Best first reached at: epoch 13 (0.4965)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 23)
  - Final epoch best: mIOU=0.4965 (存档) vs 末轮 val 0.487-0.489 回落
  - 序列: 0.324→0.378→0.412→0.448→0.478→0.483→0.486→0.489→0.490→0.492→0.493→0.489→**0.496**→0.490→0.488→0.489→0.493→0.489→0.485→0.488→0.486→0.487
  - 收敛形态: 快速上升后 0.485-0.493 平台, 峰值 0.4965 后 10 epoch 未刷新

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0071 (有效)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0047 (失败)
  - vs SSP alone (M64=0.4928): γ = +0.0037 (SSP×HCG 略优于 SSP 单轴)
  - vs HCG alone (M65=0.5002): γ = -0.0037 (组合仍低于 HCG 单轴)

## 5. Conclusion
  - 结论: [失败] — SSP×HCG 组合低于 HCG 单轴, 与前两格 (M66/M67) 同模式
  - 解释: SSP (per-scale projection readback) × HCG 0.4965, 虽比 SSP 单轴 0.4928
    高 +0.0037, 但仍低于 HCG 单轴 0.5002。server-6 上 message×HCG 三格 (M66-DET-HCG
    =0.4955, M67-PSR-HCG=0.496, M68-SSP-HCG=0.4965) 全部确认: HCG 正确交付轴上叠加
    message 变换无增量, HCG 单轴即为该方向上限。
  - 对后续实验设计的建议:
    1. message×HCG 轴完全闭合 — 不再设计 {detail/PSR/SSP/CSF}×HCG 组合。
    2. HCG 正确交付 (M65=0.5002) 作为"交付轴"的独立价值已确认, 但组合无叠加,
       后续组合只考虑 {迭代/REAGG}×HCG (M77/M78 队列中)。

## 6. Crash Info
  - Error type: NOT crashed — clean early-stop exit
  - Auto-fix attempt: N
================================================================================
