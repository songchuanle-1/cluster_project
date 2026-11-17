================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M146-CTF-HCG-CSORT-DET | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M146-CTF-HCG-CSORT-DET
  - Config: configs/Quard/ctf_hcg_csort_det/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_det.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-29 01:09 | Finished: 2026-08-29 14:07 | Duration: ~13h
  - State: done_earlystop (monitor kill, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4970 | 16 (10:13) |
  | Acc@50   | 0.513  | 16 |
  | spmIOU   | 0.461  | 16 |

## 3. Convergence Summary
  - Best first reached at: epoch ~16 (2026-08-29 10:13)
  - Subsequent no_improve epochs: 11/10 → early-stopped at ep18
  - Final epoch best: mIoU=0.4970 (10:13) — 之后 5 个验证点连续下滑
    (0.4955 → 0.4927 → 0.4867 → 0.4950 → 0.4946)
  - 收敛形态: 快速上升至 ep16 峰值后震荡下滑, 无平台维持

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0076 (有效)
  - vs champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0050 (失败)
  - vs 同族 detail 消息线: M146=0.4970 < D1-detail(relaunch)=0.5003 — CSORT×detail
    比 detail 单独还低, 去相关与 detail 消息存在负交互

## 5. Conclusion
  - 结论: [失败] (vs champion 掉 0.0050)
  - 解释: CSORT 与 cluster_message_type='detail' 无协同 — 在去相关机制下, 消息
    由聚合 context 改为细粒度 detail 反而引入噪声。message-type 轴关闭:
    'context' > 'detail' (champion 胜)。
  - 对后续实验设计的建议: message-type 轴关闭, 后续变体保持 'context' 默认;
    组合线 (CSORT×delivery) 再添一例不叠加, 强化"组合不叠加"证据。

## 6. Crash Info (if crashed)
  - N/A — 正常早停
================================================================================
