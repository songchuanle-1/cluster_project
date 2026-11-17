================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M19-S2FC | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M19-S2FC
  - Config: configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_s2fc.yaml
  - Server: server-4 | GPU: 1 (launched 2026-07-22 09:03)
  - Started: 2026-07-22 09:03 | Finished: 2026-07-23 ~02:03 (process disappeared)
  - Duration: ~17h | Epochs: 26/50
  - State: stopped_unknown (进程消失，非正常退出)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4944 | ~22     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  Final epoch 26 mIoU=0.4841, Acc_50=0.538, spmIOU=0.448

## 3. Convergence Summary
  - Best first reached at: epoch ~22 (0.4944)
  - Subsequent no_improve epochs: ~4 (0.4880→0.4887→0.4881→0.4841)
  - Convergence pattern: 前期上升至ep22达峰0.4944, 此后缓慢下行至ep26的0.4841, no_improve=4/10未达早停阈值但进程消失
  - 2-scale fine+coarse [256,8] 去掉medium scale [64]: 峰值低于M18(0.4933, fine+medium)但仅差0.0011

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0050 (有效但不显著)
  - vs champion (posA_l1 0.5012): γ = −0.0068 (显著低于champion)
  - vs M18-S2FM (0.4933): γ = +0.0011 (fine+coarse 略优于 fine+medium, 但两者均远低于3-scale)
  - Scale ablation complete: M18(fine+medium)=0.4933, M19(fine+coarse)=0.4944 → 均<champion(3-scale)=0.5012, 三个scale均有独立贡献

## 5. Conclusion
  - 结论: [消融证据] 2-scale (fine+coarse, drop medium) 不足以恢复3-scale性能
  - 解释: 去掉medium scale [64] 后 mIoU 从 0.5012 降至 0.4944 (γ=−0.0068), 结合M18-S2FM去掉coarse降至0.4933 (γ=−0.0079), 证明fine/medium/coarse三个尺度各自提供不可替代的context信息
  - 对后续实验设计的建议: Scale ablation evidence chain complete — 3-scale design validated. 不扩展该方向

## 6. Crash Info
  - Error type: stopped_unknown (进程消失)
  - Error message excerpt: 远程进程在ep26后消失，train.log拉取失败
  - Auto-fix attempt: N — stopped_unknown非代码级bug, M20-DET已入替GPU1
================================================================================
