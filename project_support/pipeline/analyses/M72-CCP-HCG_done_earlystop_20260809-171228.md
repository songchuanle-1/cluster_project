================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M72-CCP-HCG | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M72-CCP-HCG
  - Config: configs/Quard/ccp_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_ccp_hcg.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-09 01:03 | Finished: 2026-08-09 ~17:01 | Duration: ~16h
  - State: done_earlystop (log: "Early stopping at epoch 27: no improvement for 10 epochs (best=0.4950)")

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | ~18     |
  | Acc@50   | 0.551  | ~18     |
  | spmIOU   | 0.458  | ~18     |
  (best epoch ~18; 末 ep25-27 val mIOU 0.484-0.490 区间, early-stop best 定格 0.4950)

## 3. Convergence Summary
  - Best first reached at: epoch ~18 (0.4950)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 27)
  - Final epoch best: mIOU=0.4950 (存档) vs 末轮 val 0.484-0.490 回落
  - Convergence form: 快速上升后 0.490-0.495 高位平台, 峰值 0.4950 后 10 epoch
    未刷新 best, 末 ep27 val 回落

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0056 (有效, 但增益偏弱)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0062 (失败)
  - vs HCG alone (M65=0.5002): γ = -0.0052 (组合反低于单轴 — 负交互)
  - vs CCP alone (M71=0.4934): γ = +0.0016 (CCP+HCG 略优于 CCP 单轴)
  - vs detail×HCG (M66=0.4955): γ = -0.0005 (两组合负交互幅度接近)

## 5. Conclusion
  - 结论: [失败] — CCP×HCG 组合负交互, CCP 轴弱
  - 解释: CCP (粗簇全局上下文逐级注入细簇) × HCG (正确多尺度交付) 组合 0.4950
    低于 HCG 单轴 0.5002 (Δ=-0.0052), 与 detail×HCG 的负交互 (M66=0.4955) 形态
    一致: 当 HCG 已将正确对齐的多尺度 context 精确交付到每点时, CCP 再对 cluster
    token 做粗→细注入属于信息冗余, 双重变换造成抵消。CCP 源质量轴独立上限 ~0.4934
    (M71), 与任何强交付机制组合均不叠加。
  - 对后续实验设计的建议:
    1. CCP 轴判定为弱轴: M74-CCP-HCG-DET (3D 满格) 含 CCP×HCG 负交互, 预期下调
       ≈M73 或更低, 不作为破顶主候选 (仍可跑完作对照)。
    2. {token质量}×{message} 路径 (M73-CCP-DET, running) 与 {迭代}×{message}
       (M75-DET-ITER) 不含 HCG×X 负交互, 是剩余可关注的组合格。
    3. M79-REAG-CASC (本 tick 设计, 修复 REAGG lvl>0 重聚合缺陷) 是结构性修复路径,
       独立于 CCP/detail/HCG 组合轴, 单一变量对照 M70-REAGG。
================================================================================
