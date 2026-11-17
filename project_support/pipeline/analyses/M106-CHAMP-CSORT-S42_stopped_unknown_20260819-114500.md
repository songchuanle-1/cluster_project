================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M106-CHAMP-CSORT-S42 | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M106-CHAMP-CSORT-S42
  - Config: configs/Quard/champ_csort_s42/model_base1_quard2_c2f_enc_lite_posA_l1_champ_csort_s42.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-18 18:38 | Finished: 2026-08-18 18:39 | Duration: <1h
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
  - vs M104-CTF-HCG-CSORT-S42 (seed42=0.4940, CTF-HCG 变体): CHAMP 变体未能运行
  - CHAMP-CSORT 系列全线崩溃, 与 CTF-HCG-CSORT 系列(部分 seed 能运行)形成对比

## 5. Conclusion
  - 结论: [失败] — CSORT hier_postprocess.py bug 导致训练前即崩溃, 无数据产出
  - 解释: fvcore JIT tracing 触发 _cross_scale_orth_loss 中 IndexError
    (fine_tokens 索引 139 超出维度 64), 与 M98 相同的 CSORT 模块 bug
  - 建议: CSORT 轴已关闭; 此 bug 在 CHAMP 配置下 100% 复现,
    说明 CSORT 跨尺度正交损失在不同 batch 尺寸下均会触发

## 6. Crash Info (if crashed)
  - Error type: IndexError — index 139 is out of bounds for dimension 1 with size 64
  - Crash location: hier_postprocess.py:655 _cross_scale_orth_loss()
    `agg[b, p] = fine_tokens[b, children].mean(dim=0)`
  - Crash phase: model_profile (fvcore FLOPs analysis, before training loop)
  - Auto-fix attempt: N
================================================================================
