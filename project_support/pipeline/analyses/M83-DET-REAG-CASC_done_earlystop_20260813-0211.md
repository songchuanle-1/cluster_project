================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M83-DET-REAG-CASC | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M83-DET-REAG-CASC
  - Config: configs/Quard/det_reag_casc/model_base1_quard2_c2f_enc_lite_posA_l1_det_reag_casc.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-12 17:47 (resume) | Finished: 2026-08-13 02:07 | Duration: ~8.5h
  - State: done_earlystop (resumed from stopped_unknown 0.3018@ep2, killed at ep26)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4910 | ≤26     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |
  (日志拉取失败，Acc@50/spmIOU 缺失；checkpoint 留远端)

## 3. Convergence Summary
  - Best first reached at: epoch ≤26 (前段验证序列 0.4470/0.4820/0.4440/0.4830/0.4430)
  - Subsequent no_improve epochs: 13/10 (超出 patience 10 → 早停触发)
  - 收敛形态: 中段达到 ~0.48 平台后震荡，26 轮内 13 次未刷新 best，判定收敛停滞

## 4. Comparison
  - vs baseline (model_base1 0.4894): γ = +0.0016 (持平偏弱)
  - vs champion (model_...posA_l1 0.5012): γ = -0.0102 (未达标)
  - vs M79-REAG-CASC (reag_casc 单独, 0.4919): γ = -0.0009 (加 detail 无增益)
  - vs M70-REAGG (reag 单独, 0.4983): γ = -0.0073 (reag_casc 修复链整体弱于 reag)

## 5. Conclusion
  - 结论: [失败]（低于 champion 且低于同系 M70-REAGG）
  - 解释: detail × reag_casc 组合 = 0.4910。detail message_type 与 REAGG 修复链叠加无正协同，
    与 M79-REAG-CASC(0.4919) 基本持平，说明 detail 在 REAGG 轴上无额外增益；
    REAGG 轴本身（M70=0.4983 为轴内最高）也未能突破 champion 0.5012。
  - 对后续实验设计的建议: REAGG 轴证据已充分（M70/M78/M79/M83 共 4 个），
    轴内无突破，不再追加 REAGG 系变体；后续资源投向 CTF×HCG 种子验证（M89/M90/M91）与 QMOD 轴（M85/M88 在跑）
================================================================================
