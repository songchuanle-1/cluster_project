================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M111-CTF-HCG-SRL | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M111-CTF-HCG-SRL
  - Config: configs/Quard/ctf_hcg_srl/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_srl.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-08-19 11:45:58 | Finished: 2026-08-20 14:07:36 | Duration: ~26.4h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4912 | 18      |
  | Acc@50   | 0.504  | 18      |
  | spmIOU   | 0.454  | 18      |

## 3. Convergence Summary
  - Best first reached at: epoch 18
  - Subsequent no_improve epochs: ~2 (monitor killed at ep20 with no_improve=11/10 per internal count — note: eval interval ~80min, slower than usual)
  - mIoU series: 0.321, 0.390, 0.414, 0.434, 0.449, 0.448, 0.463, 0.463, 0.475, 0.484, 0.486, 0.482, 0.487, 0.486, 0.491, 0.481, 0.490, 0.491, 0.490
  - 收敛形态: 上升趋势缓慢，ep18 达峰后平台震荡。SRL loss 增加了每 epoch 训练时间 (~80min vs ~36min for M110)

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0018 (持平/微弱)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0108 (显著低于 champion)
  - vs CTF-HCG base (M81/M89≈0.5012): γ = -0.0100 (大幅低于基础 CTF-HCG)

## 5. Conclusion
  - 结论: [失败]
  - 解释: SRL (Self-supervised Representation Learning) 辅助 loss 不仅未提升 CTF-HCG，反而降低了 0.01 mIoU。SRL loss 的梯度干扰了主任务的优化方向，且显著增加了训练时间 (每 epoch 翻倍)。
  - 对后续实验设计的建议: 放弃 SRL 方向。seed=42 对照 (M113) 在队列中等待，但鉴于主实验失败，可考虑降低优先级或跳过。
================================================================================
