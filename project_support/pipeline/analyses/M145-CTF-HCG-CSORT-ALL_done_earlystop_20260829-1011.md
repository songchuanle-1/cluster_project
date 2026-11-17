================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M145-CTF-HCG-CSORT-ALL | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M145-CTF-HCG-CSORT-ALL
  - Config: configs/Quard/ctf_hcg_csort_all/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_all.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-28 18:11 | Finished: 2026-08-29 10:07 | Duration: ~16h
  - State: done_earlystop (monitor kill, PID=3323582, no_improve=11/10)
  - Hypothesis: 扩展 champion 获胜机制 CSORT 去相关从相邻尺度对扩展到全尺度对 (含非相邻 8↔256), 破 0.5020 平台

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4920 | 24      |
  | Acc@50   | 0.547  | 24      |
  | spmIOU   | 0.456  | 24      |

## 3. Convergence Summary
  - Best first reached at: epoch 24 (save best pth @ ep24)
  - Subsequent no_improve epochs: 11 (>= patience 10)
  - Final epoch best: mIoU=0.4920 vs historical best=0.4920
  - 收敛形态: 验证序列 0.4530/0.4890/0.4510/0.4840/0.4460 震荡, 中段 0.489-0.492 平台, 未持续上升

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0026 (勉强有效, 但幅度 <0.005 非显著)
  - vs champion (M95-CTF-HCG-CSORT=0.5020, 相邻对 CSORT): γ = -0.0100 (失败)
  - vs M143-OBJG=0.5000 (loss 监督轴近期最佳): γ = -0.0080
  - 同类: M146-CSORT-DET (running, 单变量 detail 组合) — 待终态

## 5. Conclusion
  - 结论: [失败]
  - 解释: CSORT 扩展到全尺度对 (含非相邻 8↔256) 后 0.4920, 较 champion 相邻对 0.5020 掉 0.0100。
    非相邻簇对缺少有意义的点对应, 其 orth loss 扰动有效信号, 破坏相邻对去相关的收益。
    假设 "全尺度对扩展可破 0.5020 平台" 被证伪。
  - 对后续实验设计的建议: 关闭 CSORT-ALL 方向。champion 的相邻尺度对 CSORT 范围确认正确, 不再扩展。
    去相关轴后续继续看 M149-SG / M150-OWC / M151-ODW / M147-MLAY-CSORT (均单变量/跨类组合)。

## 6. Crash Info (if crashed)
  - N/A (done_earlystop)
================================================================================
