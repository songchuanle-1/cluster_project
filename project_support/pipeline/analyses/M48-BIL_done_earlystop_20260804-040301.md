================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M48-BIL | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M48-BIL
  - Config: configs/Quard/bil/model_base1_quard2_c2f_enc_lite_posA_l1_bil.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-03 10:56 | Finished: 2026-08-04 03:38 | Duration: ~16.7h
  - State: done_earlystop (patience=10 hit at epoch 29)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4919 | ~19     |
  | Acc@50   | 0.544  | ~19     |
  | spmIOU   | 0.456  | ~19     |

## 3. Convergence Summary
  - Best first reached at: epoch ~19 (0.4919)
  - Subsequent no_improve epochs: 10 (early-stopped at epoch 29)
  - Final epoch best: mIoU=0.482 @ep29 vs historical best=0.4919 (缓慢下降)
  - Convergence shape: 平稳上升至 0.4919@ep19, 之后 0.482-0.489 区间震荡下行, 平台后早停

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0025 (微弱, context 收益被双线性读回侵蚀)
  - vs champion (posA_l1 0.5012): γ = -0.0093 (失败, 未破 ceiling)
  - vs M49-NLR (0.4948): γ = -0.0029 (BIL < NLR)

## 5. Conclusion
  - 结论: [失败] — 逐点条件双线性读回 (point-conditional multiplicative interaction) 无益
  - 解释: BIL 用 `feat += gate*(W_p(feat)*W_c(msg))` 的逐点乘法交互替代简单加法 readback, 但
    0.4919 显著低于 champion 0.5012。与 M47-FILM(0.4936)/M38-FLM(0.4865) 结论一致:
    对 readback 消息增加逐点/逐通道的非线性变换均不优于简单 `feat += gate*msg`。
    乘法交互引入的特征缩放不稳定, 反而损害了 context 回读的稳定性。
  - 对后续实验设计的建议: readback expressiveness 维度 M48-BIL(0.4919)/M49-NLR(0.4948)
    均 < champion, 仅剩 M50-DGC(difference-gated adaptive) 待验证。读回形式轴基本闭合:
    简单加法(context/detail) 仍是最优。转向 cluster token 聚合质量与表示富化方向。
================================================================================
