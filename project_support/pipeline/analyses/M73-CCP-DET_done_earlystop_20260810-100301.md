================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M73-CCP-DET | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M73-CCP-DET
  - Config: configs/Quard/det_ccp/model_base1_quard2_c2f_enc_lite_posA_l1_det_ccp.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-09 17:03 | Finished: 2026-08-10 09:16 | Duration: ~16.2h
  - State: done_earlystop (log: "Early stopping at epoch 27: no improvement for 10 epochs (best=0.4952)")

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4952 | ~26     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ~26 (0.4952, 08:03 tick 观测 26/50 no_impr 8/10)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 27, 09:16 日志确认)
  - 收敛形态: 起步爬升后 0.488-0.495 高位平台, 峰值 0.4952 后 10 epoch 未刷新

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0058 (有效)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0060 (失败)
  - vs CCP alone (M71=0.4934): γ = +0.0018 (CCP×detail 略优于 CCP 单轴)
  - vs detail alone (D1=0.5003): γ = -0.0051 (低于 detail 单轴)

## 5. Conclusion
  - 结论: [失败] — CCP×detail 组合未破顶, 与 M58-DET-DRP 同模式
  - 解释: CCP (粗→细 cluster token 传播) × detail (残差 message) 0.4952, 虽比 CCP
    单轴 0.4934 高 +0.0018, 但低于 detail 单轴 0.5003 和 champion 0.5012。
    "detail 残差 message 与已有效的 context 机制 (CCP/DRP) 组合负交互"再添一格
    (M58-DET-DRP=0.498 同模式)。detail 只在独立使用 (D1=0.5003) 或与缺陷机制
    (迭代/REAGG, M75/M76) 组合时才可能有价值。
  - 对后续实验设计的建议:
    1. {CCP}×{message detail} 格闭合 (负)。不再设计 detail×{CCP/DRP/HCG} 组合。
    2. 关注 M75/M76 (detail×缺陷机制) 结果, 以及 M81-CTF-HCG 破顶候选。

## 6. Crash Info
  - Error type: NOT crashed — clean early-stop exit
  - Auto-fix attempt: N
================================================================================
