================================================================================
  Motivation Review — cluster_project
  2026-07-24 23:03:01
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100, Champion: posA_l1 0.5012, Gap: +0.0088
  - 动机: cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度
  - routing 已证伪 (-0.0544), 收益来自 context 而非 routing
  - Phase 1: NOT YET — 继续探索

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | 哪些 context 设计必要? |
  | routing 有效 | falsified | true_route 0.4468 (γ=-0.0544) | A4-shuffle 证伪结构性注入有害(0.4941) ✓ |
  | detail message_type 互补 | partial | 最佳 0.5003, 三轮波动 0.4955-0.5003 | M21-HYB 测试 context+detail 组合 |
  | ORT orthogonality 提升 | partial | 0.5005 vs champion 0.5012 (-0.0007) | 独立无增益, 组合待验证(M24-ORT-D) |
  | Cross-scale attention 提升 | unknown | M22-XCA 已启动 (ep 0) | 待收敛 |
  | Max-pool aggregation 提升 | unknown | M23-CMX waiting | 待运行 |
  | Cluster refine 机制必要 | unknown | 未测试 | **本次填补** |
  | Per-scale importance 异质 | unknown | 未测试 | 后续 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion posA_l1 | 0.5012 | context-only cluster 核心验证 | 确认核心假设 ✓ |
  | M17-ORT | 0.5005 | ORT on top of context | ORT 独立不增益 (-0.0007) |
  | D1-detail best | 0.5003 | detail message_type | detail 独立接近 champion |
  | M18-S2FM | 0.4933 | 2-scale FM (去 coarse) | 3-scale 必要 (-0.0079) |
  | M19-S2FC | 0.4944 | 2-scale FC (去 medium) | 3-scale 必要 (-0.0068) |
  | M1-QGC | 0.4939 | query-gated context | gate 系不增益 (-0.0073) |
  | A4-shuffle | 0.4941 | shuffle 控制实验 | routing 结构性注入有害, 非内容 |
  | M16-CSR | 0.4875 | cluster self-refine | 低于 baseline (-0.0019) |
  | M6-QSF | 0.4866 | query-scored fusion | 低于 baseline (-0.0028) |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 核心有效 (+0.0118), routing 有害, 3-scale 必要
  - 未验证: context refinement (迭代精炼), per-scale weighting, 组合机制上限
  - 矛盾/疑问: ORT(0.5005)和detail(0.5003)都接近 champion 但不超越 — 是 ceiling 还是机制不匹配?
  - **核心缺口**: champion 用单次 cluster_attn 写回 context, 是否迭代 refine 能有额外收益?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M25-REF (refine)**: 填补 refine 机制消融缺口
    - 假设: MultiScale_Gather_Refine 比单次 C2F_ClusterAttn_Lite 产生更高质量的 context
    - 预期: 如果 refine 有效, mIoU 应 > champion 0.5012
    - 对故事线: 验证 "context refinement 是 cluster 机制的关键设计选择"
  - 为什么是 refine 而不是 wider/finer/cosine:
    - cosine → LR schedule 变更, 违反 constraints (禁止单变体改 schedule)
    - wider → 2x top-k, 噪音风险, 已有类似方向(M22-XCA 跨尺度交互)
    - finer → 更多 cluster, FLOPs 增加, 先让 XCA/CMX 出结果再决定
    - refine → 唯一直接测试 context 迭代精炼的机制, 填补明确缺口

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260724-230301.md
================================================================================
