================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M66-DET-HCG | State: stopped_unknown (log 确认 early-stop 判定)
================================================================================

## 1. Basic Info
  - ID: M66-DET-HCG
  - Config: configs/Quard/det_hcg/model_base1_quard2_c2f_enc_lite_posA_l1_det_hcg.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-07 16:06 | Finished: 2026-08-08 ~09:03 | Duration: ~17h
  - State: stopped_unknown (进程消失 ×3 确认; 远端日志尾部确认 "Early stopping at
    epoch 28: no improvement for 10 epochs (best=0.4955)" — 实际已触达 early-stop 判定)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4955 | ~21     |
  | Acc@50   | 0.538  | ~21     |
  | spmIOU   | 0.446  | ~21     |
  (log 峰值序列: ep~21 mIOU 0.496/Acc50 0.551/spm 0.459 为观测峰值, early-stop
   best 定格 0.4955; 末 ep28 val mIOU 0.480/Acc50 0.536/spm 0.442 持续下行)

## 3. Convergence Summary
  - Best first reached at: epoch ~21 (mIOU 0.496 观测峰值 / 0.4955 存档 best)
  - Subsequent no_improve epochs: 10 (early-stop 判定 at epoch 28)
  - Final epoch best: mIOU=0.4955 (存档) vs 末轮 val 0.480
  - Convergence form: 快速爬升 (前期) → 平台期 ~0.48-0.49 震荡 → 后 10 epoch
    持续下行 (0.492→0.490→0.489→0.488→0.485→0.481→0.482→0.480), 未再刷新 best

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0061 (有效)
  - vs current champion (posA_l1/DRP=0.5012): γ = -0.0057 (失败)
  - vs detail alone (D1=0.5003): γ = -0.0048 (组合反低于单轴)
  - vs HCG alone (M65=0.5002): γ = -0.0047 (组合反低于单轴)
  - 关键: detail×HCG 两轴组合 < 各自单独 — 负交互, 非正交叠加

## 5. Conclusion
  - 结论: [失败]
  - 解释: detail 残差 message (D1=0.5003) 与 HCG 正确多尺度交付 (M65=0.5002) 各自
    单轴均 ≈ champion 水平, 但二者叠加 (M66=0.4955) 反而低于任一单轴 0.005 —
    **两机制负交互**: detail 的残差语义 (inst_feats - cluster_msg) 在 HCG 的
    "每点精确交付" 下可能将正确对齐的 context 也转为残差偏差, 双重变换造成信息抵消。
    这与 M65 结论 (交付轴闭合, 修复只补短板不增上限) 一致并进一步: 交付已闭合的
    前提下叠加 message 精化反而有害。
  - 对后续实验设计的建议:
    1. **M74-CCP-HCG-DET (3D 满格) 需谨慎**: 含 detail×HCG 组合, 依据 M66 负交互
       预测其可能也低于 CCP×detail (M73)。仍可跑完作对照, 但预期下调至 ≈M73 或更低,
       不作为破顶主候选。
    2. {message}×{交付} 轴证据闭合: M66 证明 detail×HCG 不叠加 → 该 2×2 格判定
       负交互, 后续组合优先选 {token质量}×{message} (CCP×detail, M73) 与
       {迭代}×{message} (iter×detail, M75) 两条不含 HCG×detail 负交互的路径。
    3. M67-PSR-HCG / M68-SSP-HCG (server-6) 含 HCG×per-scale message, 关注是否
       同样出现负交互 (结果低于纯 PSR/SSP 单轴则佐证负交互普遍性)。

## 6. Crash Info (if stopped_unknown)
  - Error type: 非代码错误 — 进程消失 (deathwatch 3/3 确认), 远端日志尾部完整打印
    "Early stopping at epoch 28", 判定为正常 early-stop 判定后进程退出未干净回收
    (checkpoint 留远端未拉取, 状态标 stopped_unknown)
  - Error message excerpt: "Early stopping at epoch 28: no improvement for 10 epochs (best=0.4955)"
  - Auto-fix attempt: N — 无需修复, 结果已完整
================================================================================
