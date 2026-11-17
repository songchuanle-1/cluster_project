================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M38-FLM | State: stopped_unknown (early_stop effective)
================================================================================

## 1. Basic Info
  - ID: M38-FLM
  - Config: configs/Quard/flm/model_base1_quard2_c2f_enc_lite_posA_l1_flm.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-07-29 16:03:20 | Finished: 2026-07-30 13:45:36 | Duration: ~21.7h
  - State: stopped_unknown (early-stopping triggered at epoch 32: no improvement for 10 epochs)

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4865 | ~13     |
  | Acc@50   | TBD    | —       |
  | spmIOU   | TBD    | —       |
  (log only records mIoU; Acc@50/spmIOU not parsed from training log)

## 3. Convergence Summary
  - Best first reached at: epoch ~13 (2026-07-30 06:55)
  - Subsequent no_improve epochs: 10 (epochs 23-32)
  - Final epoch best: mIoU=0.4865 → last validation: mIoU=0.4725
  - 收敛形态: 快速上升至 epoch~13 达到 0.4865 后缓慢震荡下行，epoch 23 后持续低于 0.485，触发早停

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = -0.0029 (失败: 低于 baseline)
  - vs current champion (Lite, 0.5012): γ = -0.0147 (显著低于 champion)
  - vs gate系 (cag 0.4962, cfe 0.4901): γ ≈ -0.01~0 (与 gate 系同类水平)
  - FiLM (gamma*feature + beta): 本质是乘法调制，与 LayerScale (additive 0.4921) 类似但更弱

## 5. Conclusion
  - 结论: [失败] — FiLM multiplicative modulation 不能提升 cluster context 回写
  - 解释: FiLM modulation (gamma*feature + beta conditioned on cluster context) 实质是 conditioned linear transform，不改变信息流结构，属于"在 X 处加了一个单层变换"的调参式变更。0.4865 低于 baseline 0.4894，说明 conditioning 在信息量不足时引入噪声
  - 对后续实验设计的建议: 不再尝试 conditioning-based modulation 方向 (gate系、FiLM、LayerScale 三连败)，聚焦结构性机制变更 (新 attention pattern / 新 loss / 新信息聚合路径)

## 6. Crash Info
  - No crash — training completed normally via early-stop
  - Stop reason: no improvement for 10 consecutive epochs (best=0.4865@ep~13)
  - Process terminated cleanly after epoch 32 validation
================================================================================
