================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M47-FILM | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M47-FILM
  - Config: configs/Quard/film/model_base1_quard2_c2f_enc_lite_posA_l1_film.yaml
  - Server: server-4 | GPU: ? (finalized by monitor)
  - Started: 2026-08-02 21:03 | Finished: 2026-08-03 ~10:35 | Duration: ~13.5h
  - State: done_earlystop (patience=10 hit at epoch 26)
  - Note: queue.json 记录 final_best=0.497, 但 ckpt 日志最大 mIoU=0.4936 (tfevents val/mIOU max=0.4936)。
    以日志为准: best=0.4936。

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4936 | 16      |
  | Acc@50   | 0.548  | 16      |
  | spmIOU   | 0.458  | 16      |

## 3. Convergence Summary
  - Best first reached at: epoch 16 (0.4936)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 26)
  - Final epoch best: mIoU=0.4936 vs historical best=0.4936
  - Convergence shape: 快速上升到 0.4929@ep11, 0.4936@ep16, 之后 0.482-0.490 区间震荡, 平台期

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0042 (微弱, context 收益被 FiLM 调制侵蚀)
  - vs champion (posA_l1 0.5012): γ = -0.0076 (失败)
  - vs M44-CSF 0.4958: γ = -0.0022 (FiLM < CSF)

## 5. Conclusion
  - 结论: [失败] — FiLM 逐通道调制 readback 无益
  - 解释: FiLM 对 cluster message 做 per-channel γ/β 调制, 增加 2 个 d→d 投影 (~131K params),
    但 0.4936 低于 champion 的简单加法 readback。与 M38-FLM(0.4865) 一致: 逐通道调制
    系列持续失败。champion 的 `feat += gate*msg` 简单加法仍是最优 readback 形式。
  - 对后续实验设计的建议: readback expressiveness 方向继续观察 BIL/NLR/DGC;
    逐通道调制类 (FiLM/FLM) 判定为死胡同。cluster token 质量 (aggregation) 仍是未探明方向。
================================================================================
