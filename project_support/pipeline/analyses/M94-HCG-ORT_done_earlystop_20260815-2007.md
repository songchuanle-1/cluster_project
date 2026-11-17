================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M94-HCG-ORT | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M94-HCG-ORT
  - Config: configs/Quard/hcg_ort/model_base1_quard2_c2f_enc_lite_posA_l1_hcg_ort.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-15 09:07 | Finished: 2026-08-15 20:07 | Duration: ~11h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | 19      |
  | Acc@50   | 0.543  | 19      |
  | spmIOU   | 0.458  | 19      |

## 3. Convergence Summary
  - Best first reached at: epoch 19 (mIoU 0.4930, Acc50 0.543, spmIOU 0.458)
  - Subsequent no_improve epochs: 11 (monitor kill PID=805731)
  - Final epoch best: mIoU=0.4930 vs historical best=0.4930
  - 收敛形态: 缓慢爬升至 ep19 见顶 (序列 0.487→0.485→0.491→0.488→0.489→0.487),
    之后 11 轮震荡未刷新, 被早停

## 4. Comparison
  - vs baseline (model_base1): γ = +0.0036 (有效, 略高于 baseline 0.4894)
  - vs current champion (A1 posA_l1): γ = -0.0082 (失败, 远低于 0.5012)
  - vs M65-HCG (HCG 单独, 0.5002): γ = -0.0072 — ORT 叠加在 HCG 基底上反降
  - vs M92-CTF-HCG-ORT (CTF×HCG×ORT, 0.4930): 完全相同 — 无论基底是 HCG 还是
    CTF×HCG, ORT 都把结果压在 0.4930, 无正交收益

## 5. Conclusion
  - 结论: [失败] (低于 champion 0.5012, 仅略高于 baseline)
  - 解释: M94 是 M92 的补格 — 把 ORT (尺度内正交) 直接叠加在 HCG 单一基底上
    (M92 是 CTF×HCG 双基底), 结果同为 0.4930。这进一步证实 ORT 多样性轴对
    任何强基底都**有害或中性**而非增益; 与 M92 (0.4930) 完全一致, 多样性轴
    (ORT) 在强基底上的破顶希望正式收窄。
  - 对后续实验设计的建议: M97-CHAMP-ORT / M98-CHAMP-CSORT 仍是最后两个干净证据点
    (champion 基底单变量)。若二者也持平或反降, 多样性轴正式闭环排除, 故事线聚焦
    "context 回写 + 正确交付 (CTF×HCG)", 破顶需另寻机制 (或接受 0.5012 为
    seed1999 架构上限, 转多 seed 均值论证)。队列当前以 seed 复现性验证为主
    (M99/M100/M101/M102), 与 08-15 16:27 next_batch 计划一致。

## 6. Crash Info (if crashed)
  - 无 crash。历史上 M94 曾在 08-15 08:08 启动时 NameError (orth_weight 未定义),
    经 Phase 3b 修复 (bugfix 20260815-0826) 后 09:07 重新入队成功, 本次为正常
    早停终止 (no_improve=11>=10)。
================================================================================
