================================================================================
  Motivation Review — cluster_project
  2026-08-09 17:15:00
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
  | CCP×HCG 正交叠加 | 证伪 | **M72-CCP-HCG=0.4950 本 tick 终态 < HCG 单轴 0.5002** | CCP 轴弱 |
  | 迭代 readback 2轮提升 | partial | M69-ITER=0.4978 (γ=+0.0084, <champion) | 迭代轮次用缺陷交付 |
  | REAGG (迭代+重新聚合) | 检验中 | M70-REAGG 0.4983@25/50 running | **reaggregate lvl>0 缺陷** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion posA_l1 | 0.5012 | 核心机制, 交付缺陷"准单尺度" | 基准上限 |
  | M65-HCG | 0.5002 | 修复粗尺度交付缺陷 | 交付轴闭合 ✓ |
  | M69-ITER | 0.4978 | 迭代 readback 2轮 (缺陷交付) | 迭代方向受限交付 |
  | M70-REAGG | 0.4983 (running) | 迭代+重新聚合 cluster token | **reaggregate 有结构缺陷** |
  | M72-CCP-HCG | 0.4950 | CCP(源质量)×HCG(交付) | 本 tick 终态: 负交互, CCP 轴弱 |
  | M66-DET-HCG | 0.4955 | detail×HCG | 负交互 |
  | D1-detail | 0.5003 | detail message | message 轴确认有效 ✓ |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; detail 有效; HCG 修复交付但不破顶; routing 有害;
    detail×HCG 负交互 (M66); **CCP×HCG 负交互 (M72-CCP-HCG 本 tick)**。
  - **关键新观察 (本 tick 代码审查发现)**: M70-REAGG 的 `_reaggregate` 对 lvl>0
    直接取 `feats[b, :n_valid]` —— 即更新后 inst_feats 的**前 K_{lvl-1} 个点槽**,
    而非上一级刚聚合出的 cluster token。cluster_ids_list[1][b] 长度=256 (fine token→
    mid), 但 seg=feats[b,:256] 取的是前 256 个**点**; lvl=2 同理取前 64 个点。
    即 round-2 的 mid(64)/coarse(8) cluster token 由"任意前几个点"聚合而来, 语义噪声;
    只有 lvl0(256) 从全部点正确重聚合。这与 HCG 修复的交付缺陷同源 (数据布局错配)。
  - 未验证: REAGG 若用**级联正确重聚合** (lvl1 从新 fine token 聚合, lvl2 从新
    mid token 聚合), round-2 是否读到真实的更新后多尺度 context → 迭代+重聚合
    是否真正生效?
  - 矛盾/疑问: 若 mid/coarse 贡献小 (M65 闭合 + 各组合负交互), 级联修复可能收益有限
    → 若 M79 ≈ M70, 则证明 round-2 中/粗尺度重聚合无增益, 该轴也闭合。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M79-REAG-CASC: REAGG 基座 + 级联正确重聚合 (修复 _reaggregate lvl>0 缺陷),
    保持交付仍用 Lite 缺陷版 (与 M70 单一变量对照)。零新增参数, 只改 round-2
    重聚合的信息流: lvl1 聚合新 fine token, lvl2 聚合新 mid token。
    预期: 若 > M70 (0.4983 平台) → round-2 中/粗尺度 context 在正确聚合下有增益,
    REAGG 方向强化; 若 ≈ M70 → 中/粗尺度无贡献, 与 fine-dominant 观察一致, 闭合
    {重聚合}×{尺度} 格。
  - 与队列中 M78-REAGG-HCG 正交: M78 改交付 (HCG), M79 改重聚合 (级联), 两者
    分别独立检验 REAGG 的两个缺陷修复路径。
  - 若 M79 有效, 后续可与 HCG 交付正交组合 (reag_casc × HCG), 形成完整修复链。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_${TS}.md
================================================================================
