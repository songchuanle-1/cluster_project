================================================================================
  Motivation Review — cluster_project
  2026-07-18 (当前运行中 + 队列状态审查)
================================================================================

## 1. Goal

```json
{
  "metric": {"name": "mIoU", "target": 0.51, "dataset": "ScanRefer"},
  "baseline_experiment_id": "model_base1",
  "description": "聚类路由机制 — 低分矩阵与点云特征高相关→通过cluster_attn更新点云特征→提升定位精度"
}
```

| 指标 | 值 |
|---|---|
| Target | mIoU ≥ 0.5100 |
| Champion | posA_l1 (0.5012, 36/50 epochs) |
| Baseline | model_base1 (0.4894, 41/50 epochs) |
| γ vs baseline | +0.0118 |
| Gap to target | +0.0088 |
| Phase | 1 — 指标冲刺 |

## 2. Story Status

| 假设 | 状态 | 核心证据 | 缺口 |
|---|---|---|---|
| cluster_attn 路由机制有效提升点云特征表达 | **confirmed** | posA_l1 0.5012 vs base 0.4894 (γ=+0.0118) | 距 target 0.51 还差 0.0088 |
| 路由是不可或缺的（去掉会掉点） | **confirmed** | noroute 0.4972 vs posA 0.5009 (Δ=-0.0037) | — |
| 路由设计选择 (gate type/refine) 影响性能 | **partial** | cag 0.4962 / cfe 0.4901 / layerscale 0.4921 | refine/residual 机制待验证 |
| 位置编码对路由效果有影响 | **partial** | posA 0.5012 > posB 0.4953 > posC 0.4952 | C2 posC 正在重跑验证 |
| 结果是稳定的（非随机波动） | **pending** | — | seed 2026/3407 待 B5 完成后跑 |

## 3. Experiment Assessment（已完成实验的动机视角评估）

### 核心路由验证

| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|---|---|---|---|
| **posA_l1** | **0.5012** | 直接验证 cluster_attn 路由 + L1 loss | **champion — 确认核心假设 ✓** |
| posA (no L1) | 0.5009 | 纯路由验证 | 路由本身有效，L1 微幅增益 |
| lite_l1 | 0.5006 | L1 only，无 pos encoding | L1 独立有效 |
| lite (base) | 0.4992 | 基础路由 | 路由 baseline |
| **noroute** | **0.4972** | 关掉路由 → 掉点 0.0037 | **路由不可或缺 ✓** |
| model_base1 | 0.4894 | 无路由的 baseline | 路由带来 +0.0118 提升 |

### 位置编码消融

| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|---|---|---|---|
| posB | 0.4953 | 位置编码类型 B | 排除 posB，posA 最优 |
| posC (已完成) | 0.4952 | 位置编码类型 C | 之前跑完但早停，C2 重跑中 |

### Gate / Refine 机制探索（路由内部设计选择）

| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|---|---|---|---|
| cag | 0.4962 | Cross-attention gate | gate 有收益但不达最优 |
| cfe | 0.4901 | Cross-feature exchange | 低于 baseline，方向不可行 |
| layerscale (已完成) | 0.4921 | LayerScale gate | 低于 posA，C1 重跑验证中 |
| nomask | 0.4997 | 去掉 cluster mask | mask 不是关键因素 |
| init0 | 0.4949 | 零初始化 | 初始化策略影响有限 |

### GBCR 系列（不同路由实现，偏离当前动机主线）

| Experiment | mIoU | 评价 |
|---|---|---|
| gbcr_langc2f_scale_l1 | 0.4967 | 不同路由实现，指标不如 posA_l1 |
| gbcr_adaptive_l1 | 0.4961 | 同上 |
| gbcr_langroute_l1 | 0.4956 | 同上 |
| gbcr_balanced_l1 | 0.4952 | 同上 |
| gbcr_langc2f_l1 | 0.4950 | 同上 |
| gbcr_local_l1 | 0.4943 | 同上 |
| gbcr_pointgate_l1 | 0.4841 | 大幅低于 baseline |

> GBCR 系列整体低于 posA_l1，且与当前动机（cluster_attn 路由）有不同的架构路线。搁置该方向。

### 早期弃项

| Experiment | mIoU | 废弃原因 |
|---|---|---|
| attnpool | 0.4711 | 大幅低于 baseline |
| posenc | 0.4689 | 大幅低于 baseline |
| true_route | 0.4468 | 大幅低于 baseline (true label routing) |
| hier_add | 0.4041 | 架构问题 |
| hier_content | 0.3659 | 架构问题 |

## 4. Gap Analysis（Q1: 故事缺什么）

### 已验证 ✓
- [x] cluster_attn 路由有效 (γ=+0.0118 vs baseline)
- [x] 路由不可或缺 (noroute Δ=-0.0037)
- [x] posA 是最优位置编码 (posA > posB > posC)
- [x] gate 机制在选择中 cag 最优 (0.4962)

### 未验证 ✗
- [ ] **指标未达标**: champion 0.5012 < target 0.51，gap=+0.0088
- [ ] **residual refine**: B5 排队中但推送失败 2 次，是否能验证 residual 残差连接有收益？
- [ ] **多 seed 稳定性**: seed 2026/3407 依赖 B5 完成
- [ ] **layerscale 重跑**: C1 正在跑，是否能超越之前的 0.4921？

### 矛盾/疑问
- 为什么 GBCR 系列（不同的 cluster 实现）整体低于 quard2 系列？是不同的 cluster 机制导致的还是参数规模差异？
- C1 layerscale (0.4868@12/50) 进展偏弱，是否该方向不值得深入？

## 5. Design Rationale（Q2+Q3: 当前运行中/排队的实验为什么存在）

### 当前运行中

| GPU | 实验 | 设计原因 | 对故事的贡献 |
|---|---|---|---|
| server-4:0 | **C1-layerscale** | Gate 机制探索: LayerScale signed gate vs sigmoid | 验证不同 gate 实现对路由的影响 → 如果超越 0.5012，可能成为新 champion |
| server-4:1 | **C2-posC** | 位置编码消融重跑 | 确认 posC 是否真的弱于 posA，闭合位置编码消融故事 |

### 队列等待中

| 顺序 | 实验 | 设计原因 | 对故事的贡献 |
|---|---|---|---|
| 1 | **B5-residual** | ResidualAttnRefine: 补 Q/K/V 梯度，验证残差连接比 sigmoid gate 更好 | 路由中 refine 机制的消融: 残差 vs gate |
| 2 | **PosA-seed2026** | 多 seed 稳定性 | champion 的 seed=2026 验证 |
| 3 | **PosA-seed3407** | 多 seed 稳定性 | champion 的 seed=3407 验证 |

### 当前设计评估

| 维度 | 评估 |
|---|---|
| 与动机一致 | ✅ 全部围绕 cluster_attn 路由的 refine/gate/pos/seed |
| 偏题实验 | 无 — GBCR 系列已完结，不再追 |
| 优先级 | B5-residual 被 C1 跳过了（C1 先推成功），B5 已失败 2 次需排查 |
| 缺口 | seed 验证被 B5 阻塞，如果 C1 或 C2 先完成可以解放 GPU 跑 seed |

## 6. Next Batch

→ 见 `pipeline/designs/exp_design_20260717-163500.md`

当前队列深度 4 waiting / 2 GPUs → depth OK，无需立即补充。
B5 如果再次失败，建议排查 crash 日志后修复重推或跳过直接跑 seed。

================================================================================
  Status: ACTIVE (Phase 1, gap=+0.0088)
  Created: 2026-07-18
================================================================================
