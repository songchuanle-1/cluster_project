================================================================================
  Motivation Review — cluster_project
  2026-08-09 00:11:00
================================================================================

## 1. Goal
  - goal.json description: cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51。
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1/DRP 0.5012 | Gap: +0.0088
  - Phase: 1 (NOT YET) — 继续 Phase 1 自主设计

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写提升定位 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | 破 0.51 的增量来源 |
  | detail 残差 message 独立有效 | confirmed | D1=0.5003 (γ=+0.0109) | 与迭代/CCP 组合是否叠加 |
  | HCG 正确多尺度交付修复缺陷 | confirmed | M65=0.5002 ≈ champion (γ=+0.0108) | 交付轴闭合, 不带来新上限 |
  | routing 有害 | 证伪 | A3 true_route 0.4468 (γ=-0.0544) | — |
  | detail×HCG 正交叠加 | 证伪 | M66-DET-HCG=0.4955 < 单轴 (负交互) | — |
  | 迭代 readback 2轮提升 | partial | M69-ITER=0.4978 (γ=+0.0084, <champion) | **迭代轮次用的是缺陷交付!** |
  | CCP 源质量提升 | 检验中 | M71-CCP 0.4934@ep27 下滑 | M72/M73/M74 组合待跑 |
  | reag (迭代+重新聚合 token) | 检验中 | M70-REAGG 本 tick 刚推送 | reag×detail (M76) 待跑 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion posA_l1/DRP | 0.5012 | 核心机制, 但交付缺陷"准单尺度" | 基准上限 |
  | M65-HCG | 0.5002 | 修复粗尺度交付缺陷 | 交付轴闭合 ✓ (不破顶) |
  | M69-ITER | 0.4978 | 迭代 readback 2轮 (缺陷交付) | **部分确认迭代方向, 但受限交付** |
  | M66-DET-HCG | 0.4955 | detail×HCG | 证伪交付×message 正交 (负交互) |
  | D1-detail | 0.5003 | detail message | message 轴确认有效 ✓ |
  | M63-PSR / M64-SSP | 0.4964/0.4928 | per-scale message | 均 < detail |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; detail 有效; HCG 修复交付但不破顶; routing 有害;
    detail×HCG 负交互。
  - **关键新观察**: M69-ITER=0.4978 用的是 Lite 基类的 `_cluster_to_points`
    (缺陷交付 — 粗尺度 token 只写到前 K 个点槽, 绝大多数点收零粗/中尺度 context)。
    即: 迭代的每一轮都只读到"准单尺度" context。HCG (M65) 单独证明了正确的
    多尺度交付价值, 但**从未与迭代组合过** — {迭代}×{交付 HCG} 格是空的。
  - 未验证: 迭代轮次若读到正确多尺度 context (而非准单尺度), 两轮精化是否有足够
    信息量去超越单轮 champion? — 这正是本次设计的核心假设。
  - 矛盾/疑问: M66 显示 detail×HCG 负交互 — 迭代×HCG 是否也会负交互? 
    风险存在, 但机制不同 (迭代是多次 gather 的逐步精化, detail 是单次残差 message;
    负交互源于"正确对齐的 context 被残差化", 迭代的加性累积不受此影响)。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M77-ITER-HCG: 迭代 readback (2轮) × HCG 正确多尺度交付。每轮 gather 读到真
    多尺度 context → 第二轮有足够新信息 → 迭代精化真正生效。
    预期: > max(M69=0.4978, M65=0.5002); 若叠加 > 0.5012 破顶。
    若 ≤ M65 → 迭代增量被 HCG 覆盖, 交付轴彻底闭合。
  - M78-REAGG-HCG: reag (迭代+重新聚合 token) × HCG。cluster token 随迭代进化 +
    正确交付, 两轴双更新。预期: > M70 (待跑) 且 > M65; 若 >0.5012 破顶。
  - 这两个变体直接填补故事线的 {迭代}×{交付} 空白格, 把 M69 的"受限交付"观察
    转化为可检验的因果假设。若失败 → 排除迭代×交付组合, 交付+迭代两轴各自闭合,
    剩余增量看 CCP (M71-M74 队列中) 与 server-6 message 组合 (M58/M67/M68)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_${TS}.md
================================================================================
