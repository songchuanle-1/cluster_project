================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M44-CSF | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M44-CSF
  - Config: configs/Quard/csf/model_base1_quard2_c2f_enc_lite_posA_l1_csf.yaml
  - Server: server-4 | GPU: ? (finalized by monitor)
  - Started: 2026-08-02 06:03 | Finished: 2026-08-03 ~10:54 | Duration: ~28.8h
  - State: done_earlystop (patience=10 hit at epoch ~29)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4958 | 20      |
  | Acc@50   | 0.553  | 20      |
  | spmIOU   | 0.459  | 20      |

## 3. Convergence Summary
  - Best first reached at: epoch 20 (0.4958)
  - Subsequent no_improve epochs: 9 (early-stopped at epoch 29)
  - Final epoch best: mIoU=0.4958 vs historical best=0.4958 (no improvement after ep20)
  - Convergence shape: steady climb to 0.434@ep9 → 0.4958@ep20, then oscillates 0.484-0.489, plateau

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0064 (有效, context 仍带来增益)
  - vs champion (posA_l1 0.5012): γ = -0.0054 (失败, 未破 ceiling)
  - vs M46-SHC 0.4946: γ = +0.0012 (略好于 split-head)

## 5. Conclusion
  - 结论: [失败] — 跨尺度 cluster token 的 pairwise cross-attention 融合未带来增益
  - 解释: CSF 试图通过相邻尺度 cluster token 间的 cross-attention 增强跨尺度交互, 但 0.4958
    低于 champion 0.5012。与 C2C(0.4865, inter-cluster attn) 结论一致: 额外的
    cluster token 间交互对 readback 无益, 甚至有害。跨尺度信息已由多尺度 gather 充分捕获。
  - 对后续实验设计的建议: 停止 cluster-token 交互类变体 (CSF/C2C 双证伪)。转向
    readback expressiveness (BIL/NLR/DGC 已在队列) 或 cluster token 聚合质量方向。
================================================================================
