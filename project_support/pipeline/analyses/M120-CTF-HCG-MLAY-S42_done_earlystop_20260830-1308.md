================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M120-CTF-HCG-MLAY-S42 | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M120-CTF-HCG-MLAY-S42
  - Config: configs/Quard/mlay_s42/model_base1_quard2_c2f_enc_lite_posA_l1_mlay_s42.yaml
  - Server: server-6 | GPU: 7
  - Started: 2026-08-20 10:39 (log/ckpt dir origin; 08-22 kill/reset 后 ~08-28 08:07 重推)
  - Finished: 2026-08-30 13:07:30 (monitor kill PID=4038426)
  - Duration: ~24 epochs (H100, GPU7 双任务)
  - State: done_earlystop (no_improve=11 >= patience=10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4950 | 24/50   |
  | Acc@50   | 0.552  | 24      |
  | spmIOU   | 0.457  | 24      |

## 3. Convergence Summary
  - Best first reached at: epoch 24 (0.4950, Acc50=0.552 spmIOU=0.457)
  - Subsequent no_improve epochs: 11 (early-stopped)
  - 序列: 0.4470, 0.4850, 0.4490, 0.4860, 0.4500 (平台震荡, 未再刷 Best)
  - 形态: 前段上升后平台, Best 出现在 ep24 附近, 之后 11 epoch 无刷新

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0056 (有效)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0070 (失败)
  - vs M86-MLAY (0.5010 @ seed 1999): γ = -0.0060 — seed 42 显著低于 seed 1999
  - 与同类 seed 稳定性先例一致: MFP s42=0.4869, M90 s123=0.4940, M91 s42=0.4963

## 5. Conclusion
  - 结论: [失败] — MLay 机制 seed 复现性差
  - 解释: MLay (2层 legacy 深度) seed=42 = 0.4950, 比 seed 1999 (0.5010) 低 0.0060,
    复现已有 seed 脆弱模式 (MFP 0.5020→s42 0.4869 / M90 0.4940 / M91 0.4963)。
    机制本身在 seed 1999 上有增益, 但跨 seed 不稳定, 不构成稳健贡献。
  - 对后续实验设计的建议: MLay 线收敛为 seed 稳定性验证角色 (M122-s123 仍在跑, 仅补矩阵第3点);
    机制主线继续 CSORT 单轴变体 (M149-SG/M150-OWC/M151-ODW/M152-F1/M154-GSC/M155-RF/M156-CP)
    与 M153-CSORT×MFP (loss×loss 双机制, 未检象限)。
================================================================================
