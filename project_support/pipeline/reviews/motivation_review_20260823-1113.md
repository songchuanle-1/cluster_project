================================================================================
  Motivation Review — cluster_project
  2026-08-23 11:13:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder 直接访问 cluster tokens (方向①) | partial | DCM=0.5010 > DCA=0.4970, 均收敛于 ~0.501 平台 | 与其它机制叠加是否破顶未定 |
  | 多层注入 (方向②) | partial | MLay 2层=0.5010; 3/4/6层重复注入已证退化 | seed 矩阵未完成 |
  | MFP (masked feature prediction) | unconfirmed | M119=0.5020 tie champion (seed1999) | 需 S42/S123 判定机制性 (M129/M130 排队) |
  | encoder-side token 质量轴 (CCL/CGA/BCF/SRL) | 证伪 | 0.489-0.493 全灭 | 关闭 |
  | CSORT 跨 scale 去相关 | 证伪 | 3/4 seed 负, 0.5020 归因 seed1999 | 关闭 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M119-MFP | 0.5020 | 特征级 mask 重建 aux loss 提升 cluster token 完整性 | encoder-side 唯一不伤的机制, tie champion (seed1999) |
  | M124-DCM | 0.5010 | decoder 通过 qla 共享通路读 cluster context | decoder-access 轴最优实现, 持平 champion |
  | M123-DCA | 0.4970 | decoder query 独立 cross-attend cluster | 弱于 DCM, decoder-access 轴内对比 |
  | M86-MLAY | 0.5010 | 2层注入 (方向②) | 多层注入有效但平台饱和 |
  | M109-CSORT-MSG | 0.5010 | message 级跨 scale 去相关 | 与 CSORT 轴一起关闭 (seed 方差内) |
  | M114-MEMBANK-S123 | 0.5010 | 跨 batch 记忆 | 3-seed 中仅 S123 达顶, 机制不稳 |
  | M81-CTF-HCG | 0.5012 | 正确多尺度交付 | 稳定 ~0.501 平台 (跨 seed mean ~0.498) |
  | M117-BCF / M116-CGA / M115-CCL | 0.489-0.493 | encoder-side 辅助路径 | 掉点, encoder-side 质量轴基本证伪 |
  | M95-CTF-HCG-CSORT | 0.5020 | 跨 scale 正交化 | seed1999 outlier, 轴已关闭 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); decoder-access 轴 DCM 最优 (0.5010);
    2层注入有效 (0.5010); MFP 不伤 (0.5020, 未定机制性)。
  - 未验证: ① MFP 是否真实机制 (seed 矩阵进行中, M129/M130); ② decoder-access
    与其它独立机制叠加能否破 ~0.501 平台 (M125-M128 排队); ③ 是否有组合能突破
    seed-1999 结构上限 (~0.501-0.502)。
  - 矛盾/疑问: 多个独立机制 (MFP/DCM/MLay/MEMBANK-S123/CSORT-MSG) 全部收敛于
    0.501-0.502 平台, 且 M95=0.5020 已被证伪为 seed 红利 → 平台 ~0.501 很可能是
    seed-1999 的结构天花板, 单一机制无法破顶, 必须依赖**正交机制组合**。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 组合选择: MFP (encoder-side 特征完整性, aux loss, 0.5020) × DCM (decoder-side
    共享通路访问, 0.5010)。两条轴正交: MFP 让 cluster token 携带更完整的点云特征,
    DCM 让 decoder 绕过 writeback 单通道瓶颈直接读多尺度 cluster context。
    若 MFP 为真实机制 (seed 对照确认), 两条正交有效轴叠加是当前最可能破 0.501
    平台的路径 — 直接回应 goal 的"多尺度 context → 提升定位精度"。
  - 条件: 该变体依赖 MFP seed 验证结果 (depends_on M129/M130), 若 MFP 被判 seed
    红利 (同 CSORT), 则 M131 一并撤回, 避免浪费槽位。
  - 预期: 若 > champion 0.5020 → 组合机制破顶, 故事线推进至"正交机制叠加";
    若 ≈0.501 (平台) → 确认 seed-1999 结构上限, decoder-access 轴关闭,
    转向全新信息路径 (方向① 的未探索变体)。
  - 排除方向: 本轮不设计纯 seed 变体 (M129/M130/M122 已覆盖)、不设计 3/4/6 层注入
    (banned)、不设计 gate 系 (banned)、不设计 N² attention (用户保留)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260823-1113.md
================================================================================
