================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M108-CHAMP-CSORT-S2026 | State: stopped_unknown
================================================================================

## 1. Basic Info
  - ID: M108-CHAMP-CSORT-S2026
  - Config: configs/Quard/champ_csort_s2026/model_base1_quard2_c2f_enc_lite_posA_l1_champ_csort_s2026.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-18 22:38 | Finished: 2026-08-18 22:39 | Duration: <1h
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
  - vs M103-CTF-HCG-CSORT-S2026 (seed2026=0.4902, CTF-HCG 变体): CHAMP 变体未能运行
  - CHAMP-CSORT 系列 4/4 seeds 全部崩溃, 与 CTF-HCG-CSORT (3/4 seeds 能运行)形成对比
  - 说明 CHAMP 配置下的 CSORT 比 CTF-HCG 配置更易触发索引越界

## 5. Conclusion
  - 结论: [失败] — CSORT hier_postprocess.py bug 导致训练前即崩溃, 无数据产出
  - 解释: fvcore JIT tracing 触发 _cross_scale_orth_loss 中 IndexError
    (fine_tokens 索引 253 超出维度 64), 与 M98 相同的越界值, 同一 bug
  - 建议: CSORT 轴已关闭; CHAMP-CSORT 全系列因实现缺陷全线失败,
    进一步佐证 CSORT 跨尺度正交损失的实现存在根本性缺陷

## 6. Crash Info (if crashed)
  - Error type: IndexError — index 253 is out of bounds for dimension 1 with size 64
  - Crash location: hier_postprocess.py:655 _cross_scale_orth_loss()
    `agg[b, p] = fine_tokens[b, children].mean(dim=0)`
  - Crash phase: model_profile (fvcore FLOPs analysis, before training loop)
  - Auto-fix attempt: N
================================================================================
