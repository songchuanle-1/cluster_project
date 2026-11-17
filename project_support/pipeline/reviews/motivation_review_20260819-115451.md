================================================================================
  Motivation Review — cluster_project
  2026-08-19 11:54:51
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
  - Active retentions: None (no 保留/缺口保留 found)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1-A0=+0.0118 | 无需更多验证 |
  | Routing 有害 | confirmed | A3-A1=-0.0544 | 禁止 |
  | CTF 有效 | confirmed | M81=0.5012 | 核心基础 |
  | HCG 有效 | confirmed | M65=0.5002, M78=0.5008 | 核心基础 |
  | CSORT 有效 | DISPROVED | 3/4 seed 负增益 (08-19 正式关闭) | 轴关闭 |
  | ORT 单独有效 | inconclusive | M17=0.5005 vs M92/M94=0.4930 | 待 M97 结果 |
  | Multi-layer 注入 | disproved | M96=0.4940 | banned |
  | Gate 系 | disproved | 三连败 | banned |
  | Residual 系 | disproved | B5/E4=0.4944 | banned |
  | 跨 batch 记忆 (membank) | RUNNING | M110 刚启动 (ep1/50) | 等结果 |
  | 空间重建 loss (srl) | RUNNING | M111 刚启动 (ep1/50) | 等结果 |
  | Cluster 对比 loss (ccl) | DESIGNED | M115 实现完毕, 待入队 | 等实现 |
  | Cluster 图注意力 (cga) | DESIGNED | M116 实现完毕, 待入队 | 等实现 |
  | 双向 context flow (bcf) | DESIGNING | M117 实现中 | 等实现 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M81-CTF-HCG | 0.5012 | 核心: CTF+HCG context 机制 | 确认 context-only 有效 ✓ |
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 归因种子效应, 非机制增益 |
  | M109-CSORT-MSG | 0.5010 | message-level decorrelation | 接近 M81, 无独立增益 |
  | M78-REAGG-HCG | 0.5008 | HCG + reaggregate | HCG 核心有效 |
  | M65-HCG | 0.5002 | 单独 HCG | HCG 核心有效 |
  | M110-MEMBANK | running | 跨 batch 记忆原型 | 测试中 |
  | M111-SRL | running | 空间重建 loss | 测试中 |
  | M86-MLAY | 0.4960 | multi-layer, running ep15 | 预期失败 (banned) |
  | M97-CHAMP-ORT | 0.4920 | champion-base ORT, running ep14 | 测 ORT 在 champion 上的效果 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效, CTF+HCG 是核心架构
  - 未验证:
    * cluster token 表示质量 (CCL 测试中)
    * cluster 间空间结构建模 (CGA 测试中)
    * 双向信息流 (BCF 测试中)
    * 自监督训练信号 (MFP 留到下一轮)
  - 矛盾/疑问:
    * CTF-HCG 真实 mean ~0.498, seed1999 能到 0.5020 → 高方差说明架构有潜力
    * 0.50→0.51 需要 ~0.012 提升, 等于整个 CTF+HCG 收益量级 → 需要多个正交方向叠加
    * 已探索的大量方向 (CSORT/ORT/CCP/REAGG/DET等) 均在 0.50 附近打转, 未能突破

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 本批延续上一 tick (11:46) 的设计, 补充第三变体 BCF:
  - M115-CCL: Cluster Contrastive Loss — InfoNCE 跨 scale 对齐 → 减少 cluster 表示冗余
  - M116-CGA: Cluster Graph Attention — KNN+GAT → cluster 间空间结构感知
  - M117-BCF: Bidirectional Context Flow — point→cluster 反向 attention → 双向信息交换
  - 三个变体分别测试: 训练信号(ccl) / 信息聚合(cga) / 信息流向(bcf)
  - 预期: 这批跑完后确定哪个正交轴有潜力, 可叠加有效方向追求 0.51

## 6. Next Batch
  → M115-CCL + M116-CGA + M117-BCF 入队 server-4 queue
  → 见 pipeline/designs/exp_design_20260819-115451.md
================================================================================
