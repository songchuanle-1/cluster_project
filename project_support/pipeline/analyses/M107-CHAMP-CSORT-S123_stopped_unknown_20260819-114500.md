================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M107-CHAMP-CSORT-S123 | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M107-CHAMP-CSORT-S123
  - Config: configs/Quard/champ_csort_s123/model_base1_quard2_c2f_enc_lite_posA_l1_champ_csort_s123.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-18 20:38 | Finished: 2026-08-18 20:39 | Duration: <1h
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
  - vs M105-CTF-HCG-CSORT-S123 (seed123=0.4930, CTF-HCG 变体): CHAMP 变体未能运行
  - CHAMP-CSORT 系列全线崩溃 (4/4 seeds 均 crash), 无一个产出指标

## 5. Conclusion
  - 结论: [失败] — CSORT hier_postprocess.py bug 导致训练前即崩溃, 无数据产出
  - 解释: fvcore JIT tracing 触发 _cross_scale_orth_loss 中 IndexError
    (fine_tokens 索引 177 超出维度 64), 与 M98/M106 相同的 CSORT 模块 bug
  - 建议: CSORT 轴已关闭; CHAMP-CSORT 全系列因实现缺陷全线失败

## 6. Crash Info (if crashed)
  - Error type: IndexError — index 177 is out of bounds for dimension 1 with size 64
  - Crash location: hier_postprocess.py:655 _cross_scale_orth_loss()
    `agg[b, p] = fine_tokens[b, children].mean(dim=0)`
  - Crash phase: model_profile (fvcore FLOPs analysis, before training loop)
  - Auto-fix attempt: N
================================================================================
