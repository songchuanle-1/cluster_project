================================================================================
  Motivation Review — cluster_project
  2026-08-19 11:27:33
================================================================================

## 1. Goal
  - goal.json:
    metric: mIoU ≥ 0.51 on ScanRefer
    description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
    假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。"
  - Target: mIoU ≥ 0.5100
  - Champion: M95-CTF-HCG-CSORT = 0.5020 (seed1999, 22/50, done_earlystop)
  - Gap: +0.0080 (Phase 1 NOT YET)
  - **关键修正**: CSORT 跨 seed 验证 (M103/M104/M105) 证伪, M95=0.5020 归因 seed1999 有利性。
    真实机制 champion 应为 CTF-HCG 机制本身 (~0.498 mean across seeds)。
    实际 gap 至 0.51 ≈ +0.012。

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | A1(0.5012) - A0(0.4894) = +0.0118 | 已确认, 不需更多验证 |
  | Routing 有害 | confirmed | A3(0.4468) - A1(0.5012) = -0.0544 | 已证伪, 禁止 |
  | CTF (cross-scale token fusion) 有效 | confirmed | M41-CTF=0.4995, M81-CTF-HCG=0.5012 | 核心方向, 持续使用 |
  | HCG (hierarchical cluster gather) 有效 | confirmed | M65-HCG=0.5002, M78-REAGG-HCG=0.5008 | 核心方向, 与 CTF 互补 |
  | CSORT (cross-scale orthogonality) 有效 | **DISPROVED** | seed1999=0.5020(+0.004), seed2026=-0.0018, seed42=-0.004, seed123=-0.001 | 3/4 seed 负增益, 轴关闭 |
  | ORT (orth reg) 有效 | inconclusive | M17-ORT=0.5005, 但 M92/M94 ORT组合=0.4930 | 单独有效? 组合有害 |
  | detail message 有效 | confirmed | D1=0.5003, M82-DET-CTF=0.4989 | 稳定但增量有限 |
  | Multi-layer 注入 | disproved | M96=0.4940, banned 3/4/6层 | 退化确认 |
  | Gate 系 | disproved | cag/cfe/layerscale 三连败 | 已 banned |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M81-CTF-HCG (seed1999) | 0.5012 | CTF+HCG 核心组合 | 确立主力方向 ✓ |
  | M65-HCG (seed1999) | 0.5002 | HCG 单独效果 | 确认 HCG 独立有效 ✓ |
  | M41-CTF (seed1999) | 0.4995 | CTF 单独效果 | 确认 CTF 独立有效 ✓ |
  | M95-CTF-HCG-CSORT | 0.5020 | CSORT 叠加 (seed1999) | 首观 >champion, 但 seed 假阳性 |
  | M103-CSORT-S2026 | 0.4902 | CSORT seed2026 | 证伪 CSORT (Δ=-0.0018 vs no-CSORT) |
  | M104-CSORT-S42 | 0.4940 | CSORT seed42 | 证伪 CSORT (Δ=-0.0040 vs no-CSORT) |
  | M105-CSORT-S123 | 0.4930 | CSORT seed123 | 证伪 CSORT (Δ=-0.0010 vs no-CSORT) |
  | M109-CSORT-MSG | 0.5010 | message 级 CSORT | CSORT 位置无关, 均 seed 方差 |
  | M82-DET-CTF | 0.4989 | detail + CTF | detail 增量有限 |
  | M92-CTF-HCG-ORT | 0.4930 | CTF+HCG+ORT 三轴 | ORT 组合有害 |
  | M96-CTF-HCG-2LAY | 0.4940 | 2层注入 | 退化确认 |
  | seed 对照 (4 seeds) | 0.492-0.501 | 方差 ~±0.004-0.007 | 破顶需 >seed 方差 |

## 4. Gap Analysis（Q1: 故事缺什么）
  **已验证**:
  - 多尺度 context 有效 (core hypothesis)
  - CTF + HCG 是最有效的组合
  - Routing 有害, gate 系无效, multi-layer 退化

  **未验证**:
  - **如何进一步提升 context 质量?** — 所有尝试都在 0.49-0.50 区间徘徊
  - **是否存在未被发现的 context 注入机制?** — 70+ 实验均未突破 0.51
  - **CTF-HCG 的理论上界在哪?** — seed 方差使真值不确定

  **矛盾/疑问**:
  - M95=0.5020 是真实突破还是 seed 噪声? → 跨 seed 证伪, 归因 seed
  - 是否存在 >0.01 的结构改进空间? 还是 CTF-HCG 已接近上界?
  - 所有新机制都在 0.49-0.50 徘徊, 是否说明当前架构已到性能天花板?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  **故事线缺口**: 需要一个真正新的结构机制 (非调参, 非组合已知模块) 来突破 0.50 天花板。

  **候选方向分析**:
  1. Dual-path cluster context (几何聚类 + 语义聚类双路)
     → 填补 "所有聚类都是空间/特征空间, 未利用语义信息" 的缺口
     → 预期: 语义聚类提供互补 context → +0.005~0.010
     → 如果 > baseline: 证明多维度聚类是有效方向
     → 如果 < baseline: 排除语义聚类, 聚焦几何聚类优化

  2. Cluster memory bank (跨 batch EMA 存储 cluster 统计量)
     → 填补 "cluster context 只看当前 batch, 无训练分布级信息" 的缺口
     → 预期: EMA bank 提供稳定先验, 减少 seed 方差 → +0.003~0.008
     → 如果 > baseline: 证明跨 batch 信息有效, 且可能降低 seed 方差
     → 如果 < baseline: 排除跨 batch context 方向

  **约束校验**:
  - ✓ 非 N² attention (bank lookup O(N×K), K=cluster数≪N)
  - ✓ 非调参 (新计算图, 新模块)
  - ✓ 非 gate 系/路由系/attnpool
  - ✓ 非 multi-layer 重复注入
  - ✓ FLOPs 增加可控 (bank 是 O(K×d) lookup, dual-path 是 2× cluster 计算)

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260819-112733.md
================================================================================
