================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M143-CTF-HCG-OBJG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M143-CTF-HCG-OBJG
  - Config: configs/Quard/ctf_hcg_objg/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_objg.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-28 06:09 | Finished: 2026-08-28 18:07 | Duration: ~12h
  - State: done_earlystop (no_improve=13/10, monitor kill PID=1705485)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.5000 | 21/50   |
  | Acc@50   | 0.553  | 21      |
  | spmIOU   | 0.463  | 21      |

## 3. Convergence Summary
  - Best first reached at: epoch ~21 (mIoU=0.5000)
  - Subsequent no_improve epochs: 13 (monitor kill, patience=10)
  - Final epoch best: mIoU=0.5000; last 5 validations 0.459/0.495/0.459/0.491/0.456
  - 收敛形态: 快速上升至 0.497@ep~13 后震荡爬升到 0.500@ep~21 即进入平台衰减,
    被早停 kill (最后 5 次验证退化明显, 0.456~0.495)

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0106 (有效)
  - vs 父模型 ctf_hcg base (M81=0.5012): γ = -0.0012 (持平/微降)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0020
  - vs loss 轴同族: M140-CLICA=0.4970 / M141-CSIC=0.4960 / M142-dual=0.4890
    → OBJG=0.5000 为 loss 轴最佳, 但仍 < ctf_hcg base

## 5. Conclusion
  - 结论: [失败] (相对父模型 ctf_hcg 0.5012 微降; 相对 baseline 有效但无突破)
  - 解释: OBJG (cluster-token 目标对象感知 aux loss, cluster_objg_weight=0.1)
    加在 ctf_hcg base 上 (cluster_mode=ctf_hcg, 非 champion csort), 0.5000
    距 base 0.5012 差 0.0012, 距 champion 0.5020 差 0.0020。loss 监督轴第 4 个
    变体 (判别 CLICA / 一致 CSIC / 双监督 / 目标感知 OBJG) 全部 < ctf_hcg base,
    直接监督 cluster token 语义不能带来 >0.001 增益。OBJG 是 loss 轴最接近
    base 的变体, 但未破平台。
  - 对后续实验设计的建议: loss 监督轴在 base 上第 4 连败 (CLICA/CSIC/dual/OBJG
    均 ≤0.5000 < base 0.5012) → 该轴在 base 上关闭。仅剩 M144-LQA (语言语义对齐,
    running) 一维待终态; 若 LQA 也 ≤0.5012 → loss 轴整体关闭, 平台突破只能靠
    结构机制 (CSORT 系 M145-149 / MLay 系 M120-122 seed 矩阵)。OBJG 本身可考虑
    ×CSORT 组合 (与 M146-148 同类跨类组合), 但 loss 轴前科 (M142 双监督组合
    比单独更差) 表明组合优先级低于在队 M145-148。

## 6. Crash Info (if crashed)
  - N/A (早停正常, 无 crash)
================================================================================
