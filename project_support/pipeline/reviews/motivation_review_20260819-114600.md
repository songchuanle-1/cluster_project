================================================================================
  Motivation Review — cluster_project
  2026-08-19 11:46:00
================================================================================

## 1. Goal
  - goal.json:
    metric: mIoU ≥ 0.51 on ScanRefer
    description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
    假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。"
  - Target: mIoU ≥ 0.5100
  - Champion: M95-CTF-HCG-CSORT = 0.5020 (seed1999 only; true mean ~0.498)
  - Gap: +0.0080 (nominal) / +0.012 (vs true mechanism mean)
  - Phase: 1 NOT YET
  - Active constraints: Phase 1 禁止调参, 只允许结构性机制变更
  - Active retentions: None (no 保留/缺口保留 found in recent decisions or goal.json constraints)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1-A0=+0.0118 | 无需更多验证 |
  | Routing 有害 | confirmed | A3-A1=-0.0544 | 禁止 |
  | CTF 有效 | confirmed | M81=0.5012 | 核心基础 |
  | HCG 有效 | confirmed | M65=0.5002, M78=0.5008 | 核心基础 |
  | CSORT 有效 | DISPROVED | 3/4 seed 负增益 | 轴关闭 |
  | ORT 单独有效 | inconclusive | M17=0.5005 vs M92/M94=0.4930 | 待 M97 结果 |
  | Multi-layer 注入 | disproved | M96=0.4940 | banned |
  | Gate 系 | disproved | 三连败 | banned |
  | Residual 系 | disproved | B5/E4=0.4944 | banned |
  | 跨 batch 记忆 (membank) | RUNNING | M110 刚启动 | 等结果 |
  | 空间重建 loss (srl) | RUNNING | M111 刚启动 | 等结果 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M81-CTF-HCG | 0.5012 | 核心: CTF+HCG context 机制 | 确认 context-only 有效 ✓ |
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 归因种子效应, 非机制增益 |
  | M109-CSORT-MSG | 0.5010 | message-level decorrelation | 接近 M81, 无独立增益 |
  | M100-CHAMP-S123 | 0.4980 | seed=123 对照 | 确认 CTF-HCG mean ~0.498 |
  | M78-REAGG-HCG | 0.5008 | HCG + reaggregate | HCG 核心有效 |
  | M65-HCG | 0.5002 | 单独 HCG | HCG 核心有效 |
  | M86-MLAY | 0.4960 | multi-layer, RUNNING | 预期失败 (banned) |
  | M97-CHAMP-ORT | 0.4920 | champion-base ORT, RUNNING | 测 ORT 在 champion 上的效果 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效, CTF+HCG 是核心架构
  - 未验证:
    * cluster token 表示质量 (是否充分 discriminative?)
    * 双向信息流 (目前只有 cluster→point, point→cluster 未探索)
    * cluster 间空间结构建模 (各 cluster 独立处理, 忽略空间关系)
    * 自监督训练信号 (只依赖下游 task loss, 缺少 auxiliary signal)
  - 矛盾/疑问:
    * 为什么 CTF-HCG 真实 mean ~0.498 但 seed1999 能到 0.5020?
      → 高方差说明架构潜力存在, 但训练不稳定。需要降低方差的机制。
    * 0.50 → 0.51 需要 ~0.012 提升, 等于整个 CTF+HCG 的收益量级
      → 单一改进不太可能达到, 需要多个正交方向叠加

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M112 Cluster Contrastive Loss (CCL)**:
    填补 "cluster token discriminability" 缺口。InfoNCE loss 迫使同场景同位置的
    cluster tokens 在跨 scale 间对齐, 不同 cluster 的 tokens 互斥。预期: 减少 cluster
    表示冗余 → context 信息更丰富 → mIoU 提升。
    如果 > baseline: 证明 cluster 表示质量是瓶颈, 可与 M110(membank) 叠加
    如果 < baseline: 排除 "cluster discriminability" 假设

  - **M113 Bidirectional Context Flow (BCF)**:
    填补 "双向信息流" 缺口。当前架构只有一条通路: cluster_attn 把 cluster context
    写入 point features。BCF 添加反向通路: point features 作为 query 检索最相关的
    cluster features。预期: 双向信息交换 > 单向。
    如果 > baseline: 证明信息流方向性是关键因素
    如果 < baseline: 排除 "反向 context" 假设

  - **M114 Cluster Graph Attention (CGA)**:
    填补 "cluster 空间结构" 缺口。当前每个 cluster token 独立处理, 忽略 cluster
    之间的空间关系。CGA 在 cluster centroids 上构建 KNN graph, 用 GAT 传播空间结构
    信息。预期: 空间结构感知 → 更好的 context 聚合。
    如果 > baseline: 证明 cluster 间空间关系有价值
    如果 < baseline: 排除 "cluster 空间图" 假设

  - **M115 Masked Feature Prediction (MFP)**:
    填补 "自监督训练信号" 缺口。训练时随机 mask 15% cluster tokens, 从剩余 context
    重建。预期: self-supervised 正则 → 更好的泛化 → 降低 seed 方差。
    如果 > baseline: 证明训练信号不足是瓶颈
    如果 < baseline: 排除 "auxiliary reconstruction" 假设

  预期结果: 这批实验跑完后, 我们将知道哪个正交方向有潜力, 可以叠加多个有效方向
  追求 0.51 目标。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260819-114600.md
================================================================================
