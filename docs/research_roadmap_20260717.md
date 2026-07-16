# Cluster Attention 研究迭代路线图

> 目标：持续优化 3D Referring Expression Segmentation 模型性能，形成从 baseline → contribution → evidence 的完整论文创新链条
> 基线 `model_base1` mIoU = **0.4894**，当前最佳 B1 `posA_l1` = **0.5012**（+0.0118）

## 当前证据链（已收敛）

| 实验 | mIoU | Δ vs baseline | 回答的问题 |
|---|---:|---:|---|
| `model_base1` | 0.4894 | — | 无 cluster 基线 |
| B1 `posA_l1` | **0.5012** | **+0.0118** | PosA+L1+legacy routing：当前最佳 |
| A1 `noroute` | 0.4951 | +0.0057 | 纯多尺度 mean-pool context：占大半收益 |
| B1 - A1 | +0.0061 | — | legacy Q/K/V aggregation 的独立贡献 |
| A3 `true_route` | 0.4922 | +0.0028 | 真实 routing 写回：有害（比 A1 低 0.003） |

### 已可支持的论文结论

1. **Late-stage single-layer multi-scale cluster context refinement** 带来 **+0.0118 mIoU**（9.7G FLOPs，+2.1%）
2. 收益分解：~48% 来自多尺度均值 context（A1 0.0057），~52% 来自 Q/K/V 聚合（A1→B1 0.0061）
3. **Coarse-to-fine routing 不是收益来源**：真实 routing（A3 0.4922）< 无 routing（A1 0.4951）< Q/K/V 聚合（B1 0.5012）
4. 注入位置（PosA: LLA→LIA→Cluster→ILA）和单层注入（L1）是必要但非充分条件

## 迭代流水线

### Phase 1：当前在跑（~1-2 天）

| # | 实验 | GPU | 状态 | 预计完成 |
|---|---:|---|---|---|
| P1.1 | B3 `posA_l1_detail` | s4-gpu1 | 🔄 ep1 | ~1天 |
| P1.2 | A3 `true_route` | s4-gpu0 | 🔄 ep24, 5/10 | ~5h→kill |
| P1.3 | B1 seed=2026 | s4-gpu0 | ⏳ 队列（A3 kill 后自动） | ~1天 |

### Phase 2：下一批实验设计（P1 完成后立即启动）

| # | 实验 | 目的 | 优先级 |
|---|---:|---|---|
| P2.1 | B1 seed=3407 | 第三种籽稳定性 | 高（论文必需） |
| P2.2 | **若 B3 detail > 0.5012**：detail seed=2026 / noroute_detail | 验证 detail 可复现 + 是否需 routing 配合 | 高 |
| P2.3 | **若 B3 detail ≤ 0.5012**：新方向设计 | 找下一个增长点 | 高 |
| P2.4 | 效率测量（FLOPs/内存/延迟） | 论文效率数据 | 中（不占 GPU） |
| P2.5 | Cluster 尺度消融 [256] vs [64] vs [8] | 哪层贡献最大 | 低（机制深化） |

### Phase 3：收敛包（P2 完成后）

| # | 任务 | 产出 |
|---|---:|---|
| P3.1 | 最终候选模型 3-seed 完整统计 | mean±std Best mIoU，末5均值 |
| P3.2 | 全指标报告（Acc@25/50, spmIoU, FLOPs, 延迟） | 论文 Table 1 |
| P3.3 | 路由诊断分析（Q/K/V 做了什么） | 论文机制分析 |
| P3.4 | 论文初稿 | Methods + Results + Analysis |

---

## 关键决策点

1. **B3 detail > B1 (0.5012)？** → 新最佳，detail 进入主模型证据链
2. **B3 detail ≤ B1？** → detail 单独无效，需新方向：gate 机制 / 自适应尺度 / 或接受 B1 为最终模型
3. **B1 多 seed 稳定性** → std < 0.003 则可信，否则需排查训练不稳定性
4. **效率是否 < 10G FLOPs？** → 若 >10G 需精简，B1 约 9.7G 合格

## 新方向储备（若 B3 detail 无效，下一步探索）

| 方向 | 思路 | 风险 |
|---|---|---|
| Adaptive per-point scale | 每点学习融合不同尺度的权重 | 低（类似 LayerScale 已负） |
| Cluster bank size tuning | 尝试 [128,32,4] / [512,128,16] | 低（纯超参） |
| Multi-layer lightweight injection | 最后 2 层各用独立 gate，避免过平滑 | 中（L3/L4 历史负） |
| Point-wise gating | 当前 per-point gate 是否过于粗糙？ | 中 |
| Contrastive cluster loss | 在 cluster token 上加对比 loss | 中（不确定性高） |
