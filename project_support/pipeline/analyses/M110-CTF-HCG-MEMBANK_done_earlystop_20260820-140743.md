================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: M110-CTF-HCG-MEMBANK | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: M110-CTF-HCG-MEMBANK
  - Config: configs/Quard/ctf_hcg_membank/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_membank.yaml
  - Server: server-4 | GPU: 0
  - Started: 2026-08-19 11:45:39 | Finished: 2026-08-20 02:07:32 | Duration: ~14.4h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4954 | 16      |
  | Acc@50   | 0.512  | 16      |
  | spmIOU   | 0.460  | 16      |

## 3. Convergence Summary
  - Best first reached at: epoch 16
  - Subsequent no_improve epochs: 7 (monitor killed at ep23 with no_improve=13/10 per internal count)
  - mIoU series: 0.320, 0.361, 0.399, 0.428, 0.447, 0.457, 0.466, 0.463, 0.473, 0.472, 0.477, 0.480, 0.487, 0.485, 0.485, **0.495**, 0.488, 0.487, 0.478, 0.485
  - 收敛形态: 快速上升至 ep16 峰值后震荡平台，7 epoch 未刷新 Best

## 4. Comparison
  - vs baseline (model_base1=0.4894): γ = +0.0060 (微弱有效)
  - vs current champion (M95-CTF-HCG-CSORT=0.5020): γ = -0.0066 (未破顶)
  - vs CTF-HCG base (M81/M89≈0.5012): γ = -0.0058 (低于基础 CTF-HCG)

## 5. Conclusion
  - 结论: [失败]
  - 解释: Cluster memory bank 机制 (跨 epoch 持久化 cluster token 记忆) 未能超越基础 CTF-HCG，mIoU 0.4954 仅微弱高于 baseline +0.006，远低于 champion 0.5020。Memory bank 引入的跨 epoch 状态依赖可能增加了优化难度。
  - 对后续实验设计的建议: 放弃 memory bank 方向。seed=42 对照 (M112) 正在运行中，等待结果确认一致性。
================================================================================
