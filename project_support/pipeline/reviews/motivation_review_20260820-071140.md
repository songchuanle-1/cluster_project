================================================================================
  Motivation Review — cluster_project
  2026-08-20 07:11:40
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
  - Active retentions: None (no 保留/缺口保留 found in constraints[] or recent decisions)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1-A0=+0.0118 | 无需更多验证 |
  | Routing 有害 | confirmed | A3-A1=-0.0544 | 禁止 |
  | CTF+HCG 核心架构 | confirmed | M81=0.5012, M65=0.5002, M78=0.5008 | 基底确定, 需突破 |
  | CSORT 跨尺度正交 | DISPROVED | 3/4 seed 负增益 (08-19 关闭) | 轴关闭 |
  | ORT champion 基底 | disproved | M97=0.4920 no_improve=9/10 | 轴关闭 |
  | Multi-layer 注入 | disproved | M96=0.4940, M86=0.4960 | banned |
  | Gate 系 | disproved | 三连败 | banned |
  | Residual 系 | disproved | B5/E4=0.4944 | banned |
  | 跨 batch 记忆 (membank) | negative | M110=0.4950 高振荡, seed 对照进行中 | 大概率关闭 |
  | 空间重建 loss (srl) | RUNNING | M111=0.4950@ep15 | 早期, 等收敛 |
  | Cluster 对比 loss (ccl) | WAITING | M115 排队 | 等运行 |
  | Cluster 图注意力 (cga) | WAITING | M116 排队 | 等运行 |
  | 双向 context flow (bcf) | WAITING | M117 排队 | 等运行 |
  | 跨模态 cluster 交互 | UNTESTED | 全新方向 | 首次探索 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M81-CTF-HCG | 0.5012 | 核心 CTF+HCG context 机制 | 确认 context-only 有效 ✓ |
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 归因种子效应, 非机制增益 |
  | M109-CSORT-MSG | 0.5010 | message 级 decorrelation | 与 M81 持平, CSORT 轴关闭 |
  | M110-MEMBANK | 0.4950 | 跨 batch 记忆 | 高振荡 +0.006 vs baseline, 不稳定 |
  | M97-CHAMP-ORT | 0.4920 | champion 基底 ORT | ORT 在 champion 上无效, 即将早停 |
  | M86-MLAY | 0.4960 | multi-layer 注入 | 已 banned, 即将早停 |
  | M78-REAGG-HCG | 0.5008 | reaggregate + HCG | HCG 核心有效, reagg 无正协同 |
  | M65-HCG | 0.5002 | 单独 HCG | HCG 核心有效 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效 (+0.0118), CTF+HCG 是核心架构 (0.500-0.502)
  - 未验证:
    * cluster token 表示质量 (CCL 排队测试中)
    * cluster 间空间结构建模 (CGA 排队测试中)
    * 双向信息流 (BCF 排队测试中)
    * 空间重建辅助信号 (SRL 运行中)
    * **跨模态 cluster 级交互 (完全未探索 — 本次设计目标)**
  - 矛盾/疑问:
    * CTF-HCG 真实 mean ~0.498, seed1999 能到 0.5020 → 高方差说明架构有潜力但优化不稳定
    * 0.50→0.51 需要 ~0.012 提升, 等于整个 CTF+HCG 收益量级 → 可能需要多个正交方向叠加
    * 已探索 ~50 个方向均在 0.50 附近打转 → 需要全新信息流路径

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 已排队变体 (CCL/CGA/BCF/SRL) 均聚焦于视觉侧 cluster 改进
  - 未探索方向: 跨模态 (language↔cluster) 直接交互
  - 当前架构中 language 只在 decoder 层与 point features 交互
  - 如果 language 能直接在 cluster 层级提供指导, cluster context 可能更具 task-relevance
  - M118-LCC: Language-Conditioned Cluster Context
    * 验证假设: 跨模态 cluster 级交互是否比 point-level 交互更高效
    * 如果有效: 开辟全新方向, 可与 CCL/CGA/BCF 叠加
    * 如果无效: 排除 cluster 级跨模态路径, 聚焦视觉侧改进
  - 预期: 这批实验 (CCL+CGA+BCF+SRL+LCC) 跑完后, 覆盖视觉+跨模态两大方向

## 6. Next Batch
  → M118-LCC (Language-Conditioned Cluster Context)
  → 见 pipeline/designs/exp_design_20260820-071140.md
================================================================================
