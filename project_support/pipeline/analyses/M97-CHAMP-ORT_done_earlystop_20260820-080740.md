================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M97-CHAMP-ORT | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M97-CHAMP-ORT
  - Config: configs/Quard/champ_ort/model_base1_quard2_c2f_enc_lite_posA_l1_champ_ort.yaml
  - Server: server-6 | GPU: 7 (H100 80GB, 多任务模式 slot 2/2, 与 M86-MLAY 共享)
  - Started: 2026-08-15 18:10 | Finished: 2026-08-20 08:07 | Duration: ~4.6 days
  - State: done_earlystop (monitor kill PID=1934356, no_improve=11/10)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4920 | ~7      |
  | Acc@50   | 0.507  | ~17     |
  | spmIOU   | 0.457  | ~15     |
  (Best mIoU reached early ~ep7, then 11 epochs failed to improve)

## 3. Convergence Summary
  - Best first reached at: epoch ~7
  - Subsequent no_improve epochs: 11 (monitor killed at epoch 18)
  - Validation sequence (last 5): 0.4510, 0.4890, 0.4530, 0.4920, 0.4550
  - 收敛形态: 快速上升至 ~0.492 后大幅震荡，多次接近但未突破 best。多任务共享 GPU 可能导致训练不稳定。

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = +0.0026 (微弱有效，低于 +0.005 阈值)
  - vs current champion (M95-CTF-HCG-CSORT, 0.5020): γ = -0.0100 (显著低于)
  - vs M62-ORTG (0.4979): γ = -0.0059 (champ_ort < ortg，champ 正交投影弱于 DRP+ORT 方案)
  - vs M94-HCG-ORT (0.4940, from analyses): 持平偏弱

## 5. Conclusion
  - 结论: [失败]
  - 解释: Champion 正交投影 (champ_ort) 将 cluster context 通过正交投影回写 inst_feats，Best mIoU=0.4920 仅微超 baseline +0.0026，远低于 champion 0.5020。正交投影约束过强，限制了 context 回写的表达力。
  - 对后续实验设计的建议: 放弃 champ_ort 路线。HCG 的多尺度交付机制 (M65=0.5002) 和 CSORT 排序机制 (M95=0.5020) 仍是当前最优方向。正交约束不如直接 context 注入有效。

## 6. Crash Info (if crashed)
  - N/A — 正常早停，非 crash
================================================================================
