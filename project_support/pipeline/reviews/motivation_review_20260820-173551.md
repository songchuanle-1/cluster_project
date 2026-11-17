================================================================================
  Motivation Review — cluster_project
  2026-08-20 17:35:51
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
  | ORT champion 基底 | disproved | M97=0.4920 | 轴关闭 |
  | MEMBANK 跨 batch 记忆 | disproved | M110=0.4954, M112=0.4890 (2 seeds) | 轴关闭 |
  | SRL 空间重建 loss | disproved | M111=0.4912, M113 seed 对照运行中 | 轴关闭 |
  | Cluster 对比 loss (CCL) | WAITING | M115 排队 | 等运行 |
  | Cluster 图注意力 (CGA) | WAITING | M116 排队 | 等运行 |
  | 双向 context flow (BCF) | WAITING | M117 排队 | 等运行 |
  | 跨模态 cluster 交互 (LCC) | WAITING | M118 排队 | 等运行 |
  | 自监督 mask 重建 (MFP) | UNTESTED | 从未尝试 (设计文档多次留到下一轮) | 本次设计目标 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 变体, seed1999 outlier | 名义 champion, 归因种子效应 |
  | M81-CTF-HCG | 0.5012 | 核心 CTF+HCG context 机制 | 确认核心架构 ✓ |
  | M109-CSORT-MSG | 0.5010 | message 级 decorrelation | 与 M81 持平, CSORT 轴关闭 |
  | M110-MEMBANK | 0.4954 | 跨 batch 记忆 | 失败, 轴关闭 |
  | M111-SRL | 0.4912 | 空间重建辅助 loss | 失败, 轴关闭 |
  | M112-MEMBANK-S42 | 0.4890 | MEMBANK seed 对照 | 2 seeds 确认失败 |
  | M97-CHAMP-ORT | 0.4920 | champion 基底 ORT | 失败, 轴关闭 |
  | M86-MLAY | 0.501* | multi-layer 注入 (2层) | *运行中 25/50, 逼近 champion |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context-only 有效 (+0.0118), CTF+HCG 是核心架构 (0.500-0.502)
  - 已排队 (M115-M118): CCL (token 判别性), CGA (空间结构), BCF (双向流), LCC (跨模态)
  - 未验证: **自监督 mask 重建** — 设计文档 (exp_design_08-19 11:46 §3.3 / §7)
    明确"从未尝试 (新 auxiliary loss)"且"留到下一轮", 是当前唯一
    已规划但未实现的结构方向
  - 矛盾/疑问:
    * CTF-HCG 真实 mean ~0.498, seed1999 能到 0.5020 → 高方差, 优化不稳定
    * 0.50→0.51 需要 ~0.012, 等于整个 CTF+HCG 收益量级 → 需新信息流路径
    * 已探索 ~50 个方向均在 0.50 附近打转 → 已排队变体覆盖视觉侧+跨模态
    * MFP 与已失败 SRL 不同: SRL 是空间布局重建 (spatial reconstruction),
      MFP 是 cluster token 特征 mask 重建 (feature masking), 机制不同

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - MFP (Masked Feature Prediction): 对 FFN 精炼后的 cluster token 施加随机 mask,
    用 lightweight prediction head 从上下文重建被 mask 的 token 特征 → 自监督
    auxiliary loss
    * 验证假设: "cluster token 必须编码完整、可重建的场景结构 → 更强的 context 表示"
    * 与 CCL 正交: CCL 对齐跨尺度 token (InfoNCE); MFP 约束单尺度 token 内部
      的信息完整性 (mask→reconstruct)
    * 与 SRL 不同: SRL 重建空间布局 (监督几何); MFP 重建特征本身 (自监督表示)
  - 预期: MFP 若有效 → cluster token 表示更完整 → readback context 更丰富;
    若无效 → 排除特征级 mask 自监督路径, 聚焦已排队的视觉/跨模态方向
  - 队列深度: 当前 waiting=4 (M115-M118), 可用卡数=5, 达标需 6; 补 MFP → 5,
    与上一 tick (15:13) 接受的 5 waiting 持平

## 6. Next Batch
  → M119-CTF-HCG-MFP (Masked Feature Prediction)
  → 见 pipeline/designs/exp_design_20260820-173551.md
================================================================================
