================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M104-CTF-HCG-CSORT-S42 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M104-CTF-HCG-CSORT-S42
  - Config: configs/Quard/ctf_hcg_csort_s42/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_s42.yaml
  - Server: server-4 | GPU: 1
  - Started: ~2026-08-17 23:07 | Finished: 2026-08-18 16:38:32 | Duration: ~17.5h
  - State: done_earlystop (no_improve=11/10, monitor kill PID=1041778)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4940 | ~14/24  |
  | Acc@50   | ~0.548 | (est.)  |
  | spmIOU   | ~0.455 | (est.)  |

## 3. Convergence Summary
  - Best first reached at: ~epoch 14
  - Subsequent no_improve epochs: 10 (早停)
  - 收敛形态: 快速上升后平台, 典型 cluster 实验形态

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0046 (微弱有效)
  - vs champion M95-CTF-HCG-CSORT (seed1999=0.5020): γ = -0.0080 (显著低于)
  - vs 同 seed 对照 M89-CTF-HCG-R2 (seed42=0.4980, 无 CSORT): γ = -0.0040
  - CSORT 在 seed42 下反降 0.0040, 与 seed2026 一致 (均负增益)

## 5. Conclusion
  - 结论: [失败] — CSORT 在 seed42 下降 0.0040 vs 无 CSORT 对照, 跨 seed 一致性否定
  - 解释: CSORT 跨三个 seed 的表现: seed1999 +0.0040 (唯一正), seed2026 -0.0018, seed42 -0.0040。
    2/3 seed 负增益 → M95 的 0.5020 归因 seed1999 有利性, 非 CSORT 机制贡献。
  - 对后续实验设计的建议: CSORT 轴应降级, 不作为破顶方向。需要寻找 seed 稳定的结构改进。

## 6. Crash Info (if crashed)
  - N/A
================================================================================
