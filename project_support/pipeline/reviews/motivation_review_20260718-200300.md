================================================================================
  Motivation Review — cluster_project
  2026-07-18 20:03:00
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 0.5012 | Gap: +0.0088 | Phase 1
  - 动机: 聚类矩阵与点云特征高相关→cluster_attn更新点云特征→提升定位精度
  - constraints[]: 7条硬约束 | banned[]: 8条禁区

## 2. Story Status（故事线状态）
| 假设 | 状态 | 证据 | 缺口 |
|------|------|------|------|
| cluster_attn 路由有效 | confirmed | posA_l1 0.5012 vs base 0.4894 (γ=+0.0118) | 距 target 0.51 差 0.0088 |
| 路由不可或缺 | confirmed | noroute 0.4800 (Δ=-0.0212) | — |
| posA 最优位置编码 | confirmed | posA 0.5012 > posB 0.4953 > posC 0.4952 | C2 posC 重跑验证中 |
| gate 类型影响路由 | partial (banned) | cag/cfe/layerscale 三连败 | gate 系已禁止 |
| refine/residual/detail 机制 | testing | B5-residual@ep7(0.4516), C3-refine queued, D1-detail queued | 机制消融进行中 |
| cluster_att_num_layers 影响 | untested | posA(noL1) 2layer=0.5009, champion 1layer=0.5012 | 2layer+L1 未测 |
| cluster_att_init 敏感性 | untested | champion init=0.1, default=0.0 | init=0.0 未测 |

## 3. Experiment Assessment（动机视角）
| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|------------|------|-------------|-------------|
| posA_l1 (champion) | 0.5012 | cluster_attn 路由 + L1 | 核心假设确认 ✓ |
| posA (no L1) | 0.5009 | 纯路由 (2layer) | 路由有效, L1 微增益 |
| B5-residual | 0.4516@ep7 | residual refine 机制 | 待收敛 |
| C2-posC | 0.4866@ep10 | 位置编码消融 | 待收敛 |
| C1-layerscale | 0.4998@ep27 | gate 类型 (stopped) | gate 系已禁 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: cluster_attn 路由有效, 路由不可或缺, posA 最优
  - 未验证:
    - cluster_att_num_layers: 2层+L1 vs 1层+L1 — 2层曾在 posA(noL1) 中接近 champion
    - cluster_att_init: 0.1 vs 0.0 — 非零初始化是否贡献增益?
  - 在验证中: residual/refine/detail 机制, posC 编码

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - F1-2layer: 验证 cluster_att_num_layers 对 L1 版本的敏感性。posA(noL1) 用 2 层达 0.5009, 与 champion(1层+L1=0.5012) 接近。合并 2层+L1 可能超越 champion。
  - F2-init00: 验证 cluster_att_init=0.1 是否必要。如果 init=0.0 结果相似 → init 不重要; 如果掉点 → non-zero init 是关键设计选择。
  - 两个变体均 YAML-only, 零代码风险, 直接验证路由机制的两个未消融超参数。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260718-200300.md
================================================================================
  Status: ACTIVE (Phase 1, gap=+0.0088)
  Created: 2026-07-18 20:03
================================================================================
