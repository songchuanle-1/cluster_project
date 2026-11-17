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
  - 收敛形态: 早期震荡低值(ep4 ~0.39), 中后期回升至 0.4941 平台, 未突破 champion

## 4. Comparison
  - vs baseline (model_base1): γ = +0.0047 (微弱有效, 但未达 ≥0.005 阈值)
  - vs current champion (model_base1_quard2_c2f_enc_lite_posA_l1): γ = -0.0071 (差于 champion)
  - vs A3-true_route (0.4468): γ = +0.0473 (远优于内容路由, 验证路由机制本身的伤害远小于内容路由)
  - 三阶对比: champion(0.5012, 路由计算但丢弃) > A4-shuffle(0.4941, 随机路由) > A3-true_route(0.4468, 内容路由)

## 5. Conclusion
  - 结论: [有效但不足] — 路由结构注入本身有损,但内容路由才是灾难性退化主因
  - 解释: A4-shuffle 作为 A3-true_route 的控制组,使用随机索引替代内容路由索引。
    A4(0.4941) 远优于 A3(0.4468,+0.0473),证明 A3 的崩不是"稀疏路由结构注入"本身,
    而是"内容相关的路由破坏了 cluster token 的语义"。但 A4 仍低于 champion(0.5012,-0.0071),
    说明即使是随机路由的结构注入也会引入噪声。最佳策略:计算路由但不使用(champion)。
  - 对后续实验设计的建议: 彻底放弃 routing 方向(banned 已覆盖),继续聚焦 context/detail/orthogonality 机制。
================================================================================
