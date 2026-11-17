================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M147-MLAY-CSORT | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M147-MLAY-CSORT
  - Config: configs/Quard/mlay_csort/model_base1_quard2_c2f_enc_lite_posA_l1_mlay_csort.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-29 10:10 | Finished: 2026-08-30 11:32:45 | Duration: ~25h
  - State: done_earlystop (11/10 no-improve, monitor kill PID=1228742)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4970 | 23/50   |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch 23
  - Subsequent no_improve epochs: 11 (early-stopped)
  - Final epoch best: 0.4970 (best at ep23, 11 ep 无刷新)
  - 形态: 上升后平台, 未达到任一父类 (MLay 0.5010 / CSORT 0.5020)

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0076 (有效但弱于父类)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0050 (失败)
  - vs M86-MLAY (0.5010): γ = -0.0040 — MLay 单轴更高
  - vs M95-CSORT (0.5020): γ = -0.0050 — CSORT 单轴更高
  - 与同类组合失败: M146-CSORT-DET=0.4970, M148-CSORT-DCM=0.4990

## 5. Conclusion
  - 结论: [失败] — 组合负交互
  - 解释: MLay (2层 legacy 深度) × CSORT (跨尺度去相关) 组合 = 0.4970,
    低于两父类 (0.5010/0.5020) 各 ~0.004-0.005 — "architecture(深度)×loss(去相关)"
    组合不叠加, 与 M146 (message-type×CSORT) / M148 (decoder-access×CSORT) 同型。
  - 对后续实验设计的建议: 深度轴 (MLay) 与去相关轴 (CSORT) 的跨轴组合关闭;
    继续 CSORT 单轴变体 (M149-SG/M150-OWC/M151-ODW/M152-F1/M154-GSC/M155-RF/
    M156-CP) 与 M153-CSORT×MFP (loss×loss 双机制, 未检象限)。MLay 线收敛为
    seed 稳定性验证 (M120-s42/M122-s123) 的角色。
================================================================================
