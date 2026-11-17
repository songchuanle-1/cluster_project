================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M98-CHAMP-CSORT | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M98-CHAMP-CSORT
  - Config: configs/Quard/champ_csort/model_base1_quard2_c2f_enc_lite_posA_l1_champ_csort.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-18 00:40 | Finished: 2026-08-18 00:41 | Duration: <1h
  - State: stopped_unknown (crashed during model_profile before epoch 1)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | N/A    | —       |
  | Acc@50   | N/A    | —       |
  | spmIOU   | N/A    | —       |

  (No metrics collected — crash occurred during fvcore JIT tracing at startup)

## 3. Convergence Summary
  - Best first reached at: N/A (never reached epoch 1)
  - Subsequent no_improve epochs: N/A
  - Final epoch best: N/A
  - 收敛形态: 无 — 训练未启动, 在 model_profile FLOPs 分析阶段即崩溃

## 4. Comparison
  - vs baseline (model_base1=0.4894): N/A (无指标产出)
  - vs champion M95-CTF-HCG-CSORT (seed1999=0.5020): N/A
  - CHAMP-CSORT 与 CTF-HCG-CSORT 的区别: CHAMP 变体仅在 champ 配置上叠加 CSORT
  - 本次实验因 CSORT 模块 bug 未能产出任何数据

## 5. Conclusion
  - 结论: [失败] — CSORT hier_postprocess.py bug 导致训练前即崩溃, 无数据产出
  - 解释: fvcore JIT tracing 触发 _cross_scale_orth_loss 中 IndexError
    (fine_tokens 索引 253 超出维度 64), CSORT 跨尺度正交损失存在未修复的索引越界 bug
  - 建议: CSORT 轴已关闭; 此崩溃进一步确认 CSORT 模块存在实现缺陷,
    即使在 CTF-HCG-CSORT 中能运行的 seed 也仅是侥幸避开了该路径

## 6. Crash Info (if crashed)
  - Error type: IndexError — index 253 is out of bounds for dimension 1 with size 64
  - Crash location: hier_postprocess.py:655 _cross_scale_orth_loss()
    `agg[b, p] = fine_tokens[b, children].mean(dim=0)`
  - Crash phase: model_profile (fvcore FLOPs analysis, before training loop)
  - Auto-fix attempt: N
================================================================================
