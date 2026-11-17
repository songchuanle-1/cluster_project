================================================================================
  Motivation Review — cluster_project
  2026-08-09 20:12:00
================================================================================

## 1. Goal
  - goal.json description: cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51。
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 0.5012 | Gap: +0.0088
  - Phase: 1 (NOT YET) — 继续 Phase 1 自主设计

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写提升定位 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | 破 0.51 的增量来源 |
  | detail 残差 message 独立有效 | confirmed | D1=0.5003 (γ=+0.0109) | 与迭代/CCP 组合是否叠加 |
  | HCG 正确多尺度交付 | confirmed | M65=0.5002 ≈ champion (γ=+0.0108) | 交付轴闭合, 不带来新上限 |
  | routing 有害 | 证伪 | A3 true_route 0.4468 (γ=-0.0544) | — |
  | detail×HCG 正交叠加 | 证伪 | M66-DET-HCG=0.4955 < 单轴 (负交互) | — |
  | CCP×HCG 正交叠加 | 证伪 | M72-CCP-HCG=0.4950 < HCG 单轴 0.5002 | CCP 轴弱 |
  | REAGG round-2 中/粗尺度重聚合 | **本 tick 终态** | M70-REAGG=0.4983@ep28 但 _reaggregate lvl>0 有缺陷 | 级联修复未测 (M79) |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion posA_l1 (DRP) | 0.5012 | 核心机制, 交付缺陷"准单尺度" | 基准上限 |
  | M70-REAGG (本 tick 终态) | 0.4983 | REAGG 迭代+重新聚合, **双缺陷** (重聚合 lvl>0 任意点槽 + Lite 准单尺度交付) | 即使双缺陷仍 0.4983 → 若修复, 方向可能破顶 |
  | M65-HCG | 0.5002 | 修复交付缺陷 | 交付轴闭合 ✓ |
  | M71-CCP | 0.4934 | 粗→细 context 传播 | CCP 轴弱 |
  | M72-CCP-HCG | 0.4950 | CCP×HCG | 负交互, CCP 轴弱 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; detail 有效; HCG 修复交付不破顶; routing 有害;
    detail×HCG / CCP×HCG 负交互; REAGG 双缺陷仍 0.4983 (本 tick 终态)。
  - **关键新观察 (M70 本 tick 终态 + 前 tick 代码审查)**: M70-REAGG 的 `_reaggregate`
    对 lvl>0 取 `feats[b,:n_valid]` = 前 K 个**点**槽而非真实上一级 token → round-2
    mid/coarse token 语义噪声。同时 `_cluster_to_points` 继承 Lite 缺陷版交付准单尺度。
    即 M70 同时有两个缺陷, 但即便如此已达 0.4983 (距 champion 仅 0.0029)。
  - 未验证: 
    ① 重聚合缺陷修复 (M79-REAG-CASC, 队列中): round-2 级联正确聚合是否有增益?
    ② 交付缺陷修复 (M78-REAGG-HCG, 队列中): 正确多尺度交付是否解锁 REAGG?
    ③ **两缺陷同时修复 (M80-REAG-CASC-HCG, 本 tick 设计)**: 完整修复链后 REAGG
       是否真正破顶?
  - 矛盾/疑问: 若 M80 ≈ M70 → 即使双修复 REAGG 也无增益, 轴彻底闭合, 与
    fine-dominant 观察一致; 若 M80 > M70 → REAGG 方向在完整修复下解锁。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M80-REAG-CASC-HCG: 级联重聚合 (M79 的 _reaggregate) + HCG 组合 gather (M78 的
    _cluster_to_points) 同时作用于 REAGG 循环。零新增参数。
  - 角色: 修复链 2×2 满格 — {重聚合: 缺陷/级联} × {交付: Lite/HCG} 的最后一格。
    对照 M70 (双缺陷) / M79 (只修重聚合) / M78 (只修交付), 单变量隔离两个修复。
  - 预期: 若 mid/coarse scale 的 round-2 重聚合在正确聚合+正确交付下确有信息,
    M80 > M78/M79 ≥ M70; 若中/粗尺度无贡献 (fine-dominant), M80 ≈ M70 轴闭合。
  - 与 goal.json constraints 冲突校验: 非 gate/路由/residual 系; 零新参数 (参数增量=0
    < 5K 但新计算图: 级联重聚合路径 + HCG 组合交付路径均未在 REAGG 循环中同时存在);
    不改 schedule; FLOPs ≈ REAGG (~2 round gather, HCG 组合 gather 无 attention)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260809-2012.md
================================================================================
