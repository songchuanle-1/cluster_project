================================================================================
  Experiment Result Analysis — cluster_project
  Experiment: A4-shuffle | State: done_earlystop
================================================================================

## 1. Basic Info
  - ID: A4-shuffle
  - Config: configs/Quard/trueroute_shuffle/model_base1_quard2_c2f_enc_lite_posA_l1_trueroute_shuffle.yaml
  - Server: server-4 | GPU: 1
  - Started: 2026-07-20 13:03 | Finished: 2026-07-21 13:32 | Duration: ~24h
  - State: done_earlystop

## 2. Best Metrics
  | Metric   | Value  | @ Epoch |
  |----------|--------|---------|
  | mIoU     | 0.4941 | ~19     |
  | Acc@50   | —      | —       |
  | spmIOU   | —      | —       |

## 3. Convergence Summary
  - Best first reached at: epoch ~19
  - Subsequent no_improve epochs: 10 (early-stopped)
  - Final epoch best: mIoU=0.4941
  - 收敛形态: 从 0.3900 early epoch 上升到 0.4941 后平台, 10 连不刷 Best 触及早停

## 4. Comparison
  - vs baseline (model_base1, 0.4894): γ = +0.0047 (略有效, 但 <0.005 context 声称阈值)
  - vs champion (model_base1_quard2_c2f_enc_lite_posA_l1, 0.5012): γ = -0.0071 (远低于 champion)
  - vs A3-true_route (0.4468): γ = +0.0473 (大幅优于 true_route, 证明内容路由有效)
  - vs A1-champion_lite (0.5012): γ = -0.0071 (random shuffle 破坏了 context 质量)

## 5. Conclusion
  - 结论: [对照验证] A3-true_route (0.4468) 的崩是因为内容路由 (content-based assignment) 有害, 而非结构注入 (structural injection) 有害.
    A4-shuffle 使用随机打乱的 routing index → 恢复了 0.4941 (vs A3 的 0.4468), 证明:
    (1) A3 的崩不是 cluster_attn 模块架构问题
    (2) 内容路由本身有信息破坏性
    (3) routing 控制组证据完整: true_route 有害, shuffle 中性, context-only (routing 丢弃) 最佳
  - 对后续实验设计的建议: routing 方向彻底关闭 (true_route/shuffle 均已证). 聚焦 context-only 机制 (ORT/CMX/REF/HYB) 继续提点.

## 6. Crash Info
  - N/A (正常早停)
================================================================================
