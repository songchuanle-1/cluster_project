================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M138-MLAY-DUAL | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M138-MLAY-DUAL
  - Config: configs/Quard/mlay_dual/model_base1_quard2_c2f_enc_lite_posA_l1_mlay_dual.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-26T13:09:39 | Finished: 2026-08-27T04:07:27 | Duration: ~15h
  - State: done_earlystop (monitor kill PID=3737535, no_improve=13/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4990 | 27/50   |
  | Acc@50   | 0.552  | ~27     |
  | spmIOU   | 0.457  | ~27     |

## 3. Convergence Summary
  - Best first reached at: epoch 27 (0.4990)
  - Subsequent no_improve epochs: 13 (early-stopped at 27/50)
  - Final epoch best: mIoU=0.4990 vs historical best=0.4990
  - 收敛形态: 0.45-0.50 区间震荡, 27 epoch 达 0.4990 后 13 epoch 未刷新

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0096 (有效)
  - vs current champion (M81-CTF-HCG=0.5012): γ = -0.0022 (持平/略低)
  - vs M134-DUAL (qla+qia 双通路, ctf_hcg base)=0.4970: γ = +0.0020
  - vs M86-MLAY (2层)=0.5010: γ = -0.0020
  - 前置: M139 note 标记 M138 为 "ctf_hcg base 缺陷" 变体 (base 非 legacy 2层),
        满强度正确天花板格以 M139-MLAY-DUAL-LEGACY 为准

## 5. Conclusion
  - 结论: [持平] — {MLay 2层}×{DUAL} 组合 0.4990, 未破 0.501 平台
  - 解释: MLay(2层) 与 {qla+qia 双通路} 的组合不叠加 (0.4990 < 各自单测 0.5010),
        与 M125/M126/M136 通路组合不叠加模式一致; 且该变体 base 有缺陷,
        结论需 M139 (legacy 2层 修正) 最终确认。
  - 对后续实验设计的建议: 继续等 M139-MLAY-DUAL-LEGACY 结果定论组合天花板格;
        若 M139 亦不叠加 → 组合轴正式关闭, 与 loss 监督轴 (M140-143) 交叉。
================================================================================
