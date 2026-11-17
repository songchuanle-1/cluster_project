================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M105-CTF-HCG-CSORT-S123 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M105-CTF-HCG-CSORT-S123
  - Config: configs/Quard/ctf_hcg_csort_s123/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_s123.yaml
  - Server: server-4 | GPU: 0
  - Started: ~2026-08-18 08:37 | Finished: 2026-08-18 20:38:24 | Duration: ~12h
  - State: done_earlystop (no_improve=11/10, monitor kill PID=2466308)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4930 | ~10/20  |
  | Acc@50   | ~0.546 | (est.)  |
  | spmIOU   | ~0.453 | (est.)  |

## 3. Convergence Summary
  - Best first reached at: ~epoch 10
  - Subsequent no_improve epochs: 10 (早停)
  - 收敛形态: 快速上升后快速平台, 早停偏早

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0036 (微弱有效)
  - vs champion M95-CTF-HCG-CSORT (seed1999=0.5020): γ = -0.0090 (显著低于)
  - vs 同 seed 对照 M90-CTF-HCG-S3 (seed123=0.4940, 无 CSORT): γ = -0.0010
  - CSORT 在 seed123 下微降 0.0010, 与 seed2026/seed42 一致

## 5. Conclusion
  - 结论: [失败] — CSORT 在 seed123 下降 0.0010 vs 无 CSORT 对照
  - 解释: 四个 seed 的 CSORT 跨 seed 结果汇总:
    seed1999: +0.0040 (唯一正, M95 0.5020 vs M81 0.5012)
    seed2026: -0.0018 (M103 0.4902 vs M102 0.4920)
    seed42:   -0.0040 (M104 0.4940 vs M89 0.4980)
    seed123:  -0.0010 (M105 0.4930 vs M90 0.4940)
    → 3/4 seed 负增益, CSORT 机制效果被证伪。M95=0.5020 为 seed1999 有利性。
  - 对后续实验设计的建议: CSORT 轴正式关闭。破顶需从其他结构方向寻找。

## 6. Crash Info (if crashed)
  - N/A
================================================================================
