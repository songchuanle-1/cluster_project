================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M103-CTF-HCG-CSORT-S2026 | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M103-CTF-HCG-CSORT-S2026
  - Config: configs/Quard/ctf_hcg_csort_s2026/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_s2026.yaml
  - Server: server-4 | GPU: 0
  - Started: ~2026-08-17 13:10 | Finished: 2026-08-18 12:38:22 | Duration: ~23h
  - State: stopped_unknown (process disappeared at epoch 25/50)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4902 | ~20/25  |
  | Acc@50   | ~0.547 | (est.)  |
  | spmIOU   | ~0.452 | (est.)  |

## 3. Convergence Summary
  - Best first reached at: ~epoch 20
  - Process disappeared at epoch 25 (no early-stop message, no crash log)
  - 收敛形态: 正常上升后平台, 未收敛即中断

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0008 (持平)
  - vs champion M95-CTF-HCG-CSORT (seed1999=0.5020): γ = -0.0118 (显著低于)
  - vs 同 seed 对照 M102-CTF-HCG-S2026 (seed2026=0.4920, 无 CSORT): γ = -0.0018
  - CSORT 在 seed2026 下不仅无效, 反而降低 0.0018

## 5. Conclusion
  - 结论: [失败] — CSORT 在 seed2026 下无正增益, 反降 0.0018 vs 无 CSORT 对照
  - 解释: M95-CTF-HCG-CSORT 的 0.5020 极可能是 seed1999 有利性所致, 而非 CSORT 机制贡献。
    CSORT 跨 seed 表现: seed1999=0.5020, seed2026=0.4902 (Δ=-0.0118), 方差远超机制增益。
  - 对后续实验设计的建议: CSORT 不宜作为破顶方向, 需寻找更稳定的结构改进

## 6. Crash Info (if crashed)
  - Error type: stopped_unknown (process disappeared, no crash log)
  - Auto-fix attempt: N
================================================================================
