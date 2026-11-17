================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M49-NLR | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M49-NLR
  - Config: configs/Quard/nlr/model_base1_quard2_c2f_enc_lite_posA_l1_nlr.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-03 11:00 | Finished: 2026-08-04 03:49 | Duration: ~16.8h
  - State: done_earlystop (patience=10 hit at epoch 25)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4948 | ~15     |
  | Acc@50   | 0.549  | ~15     |
  | spmIOU   | 0.459  | ~15     |

## 3. Convergence Summary
  - Best first reached at: epoch ~15 (0.4948)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 25)
  - Final epoch best: mIoU=0.488 @ep25 vs historical best=0.4948 (缓慢下行)
  - Convergence shape: 快速上升至 0.4948@ep15, 之后 0.484-0.492 区间震荡, 平台后早停

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0054 (有效, context 收益保留)
  - vs champion (posA_l1 0.5012): γ = -0.0064 (失败, 未破 ceiling)
  - vs M48-BIL (0.4919): γ = +0.0029 (NLR > BIL)
  - vs M17-ORT (0.5005): γ = -0.0057 (NLR < token 正则)

## 5. Conclusion
  - 结论: [失败] — 非线性 MLP 读回未带来增益
  - 解释: NLR 用 MLP 非线性变换读回消息, 0.4948 仍低于 champion 0.5012。虽然略好于
    BIL(0.4919), 但非线性读回未突破简单加法 readback 的天花板。与 FILM/FLM/BIL 串联:
    readback expressiveness 轴全部 < champion。champion 的 `feat += gate*msg`(context) 与
    detail 消息(difference-based) 仍是最优 readback 形式。
  - 对后续实验设计的建议: 读回形式轴(M48-BIL/M49-NLR)基本闭合。剩余唯一读回变体
    M50-DGC(difference-gated adaptive) 在跑。若 DGC 仍不破 ceiling, 读回轴完全闭合,
    将注意力转移到 cluster token 聚合质量(M51-DCA/M52-CCR)与表示富化方向。
================================================================================
