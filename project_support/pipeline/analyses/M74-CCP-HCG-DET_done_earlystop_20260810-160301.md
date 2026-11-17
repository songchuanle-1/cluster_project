================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M74-CCP-HCG-DET | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M74-CCP-HCG-DET
  - Config: configs/Quard/det_ccp_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_det_ccp_hcg.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-09 20:03 | Finished: 2026-08-10 15:28 | Duration: ~19.4h
  - State: done_earlystop (log: "Early stopping at epoch 27: no improvement for 10 epochs (best=0.4948)")

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4948 | ~22-24  |
  | Acc@50   | 0.541  | ~26 (末段观测) |
  | spmIOU   | 0.450  | ~26 (末段观测) |
  (末段 ep26/27 val: 0.487/0.481; best 0.4948 在更早 epoch 达成, 其 Acc/spm 未直接落 grep)

## 3. Convergence Summary
  - Best first reached at: epoch ~22-24 (tick #456 13:03 观测 24/50 no_impr 6/10, best=0.4948)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 27, log mtime 15:28 确认)
  - 收敛形态: 起步爬升至 0.4948 后高位平台, 10 epoch 未刷新 → 早停

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0054 (有效)
  - vs current champion (posA_l1=0.5012): γ = -0.0064 (失败)
  - vs CCP×HCG (M72=0.4950): γ = -0.0002 (持平)
  - vs HCG alone (M65=0.5002): γ = -0.0054
  - vs detail alone (D1=0.5003): γ = -0.0055
  - vs CCP×detail (M73=0.4952): γ = -0.0004 (持平)

## 5. Conclusion
  - 结论: [失败] — CCP×HCG×detail 三维满格 0.4948 与 M72-CCP-HCG (0.4950) 持平, detail 残差 message 在 {CCP×HCG} 组合上无增益
  - 解释: detail (残差 message) 与已有效 context 机制组合负/无交互的规律再添一格。
    M58-DET-DRP=0.498 / M66-DET-HCG=0.4955 / M73-CCP-DET=0.4952 / M74=0.4948
    全部 ≤ HCG 单轴 0.5002。CCP 源质量轴 (M71=0.4934, M72=0.4950, M73=0.4952,
    M74=0.4948) 稳定 ~0.495 平台, 判定为弱轴。detail 仅在独立使用 (D1=0.5003)
    或与缺陷机制组合 (M75/M76) 时才有价值。
  - 对后续实验设计的建议:
    1. {CCP}×{detail} 格闭合 (负)。不再设计 detail×{CCP} 组合。
    2. 破顶候选转向 REAGG 进化轴 × HCG 交付: M78-REAGG-HCG (9/50 0.4767 上升中)
       与 M80-REAG-CASC-HCG, 以及 CTF token 精炼 × HCG: M81-CTF-HCG。
    3. 关注 server-6 M75/M76 (detail×缺陷机制) 结果以闭合 detail 轴故事线。

## 6. Crash Info
  - Error type: NOT crashed — clean early-stop exit
  - Auto-fix attempt: N
================================================================================
