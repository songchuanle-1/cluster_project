================================================================================
  Motivation Review — cluster_project
  2026-08-10 09:26:47
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
  | 多尺度 context 回写提升定位 | confirmed | champion DRP 0.5012 vs base 0.4894 (γ=+0.0118) | 破 0.51 的增量来源 |
  | detail 残差 message 独立有效 | confirmed | D1=0.5003 (γ=+0.0109) | 与迭代/CCP 组合是否叠加 |
  | HCG 正确多尺度交付 | 闭合 | M65=0.5002 ≈ champion | 交付轴闭合, 不带来新上限 |
  | routing 有害 | 证伪 | A3 true_route 0.4468 (γ=-0.0544) | — |
  | message×HCG 组合负交互 | confirmed | M66-DET-HCG 0.4955 / M67-PSR-HCG 0.496 / M68-SSP-HCG 0.4965 / M72-CCP-HCG 0.4950 — 全部 < HCG 单轴 0.5002 | HCG 交付轴上 message 变换无叠加 |
  | detail×DRP 组合负交互 | confirmed | M58-DET-DRP 0.498 < DRP 0.5012 且 < detail 0.5003 | detail 与 champion 简洁回写不协同 |
  | REAGG 方向有潜力 (双缺陷仍 0.4983) | partial | M70-REAGG 0.4983 (级联+交付双缺陷) | M78/M79/M80 修复链在队 |
  | 迭代 readback 2轮 | partial | M69-ITER 0.4978 (缺陷交付) | M75/M77 迭代×message/HCG 在队 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion posA_l1 (DRP) | 0.5012 | 核心机制 (context 回写, 准单尺度交付) | 基准上限 |
  | M65-HCG | 0.5002 | 正确多尺度交付 | 交付轴闭合 (修复缺陷不破顶) |
  | D1-detail | 0.5003 | detail 残差 message | 确认 message 构造独立增益 |
  | M41-CTF | 0.4995 | per-scale FFN 精炼 cluster token (token 质量轴) | 接近 champion, 单独未破顶 |
  | M58-DET-DRP (本批终态) | 0.498 | detail × DRP | detail 与简洁回写负交互 |
  | M67-PSR-HCG (本批终态) | 0.496 | PSR × HCG | message×HCG 无叠加 |
  | M68-SSP-HCG (本批终态) | 0.4965 | SSP × HCG | message×HCG 无叠加 |
  | M70-REAGG | 0.4983 | 迭代+重新聚合 (双缺陷) | 方向未闭合, 修复链在队 |
  | M69-ITER | 0.4978 | 迭代 readback (缺陷交付) | 迭代轴受限缺陷交付 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; detail 有效; HCG 交付轴闭合; message×HCG 组合全部负交互;
    detail×DRP 负交互; routing 有害。
  - 未验证:
    ① **CTF (token FFN 精炼) 从未与任何正交轴组合** — CTF 单独 0.4995 接近 champion,
       其分析指出"瓶颈可能不在 token 质量而在 readback/融合机制"。若把 token 质量
       精炼 (CTF) 与正确交付 (HCG) 组合, 能否突破?
    ② **CTF × detail message** — token 质量精炼 × message 残差变换, 两轴从未正交。
    ③ REAGG 修复链 (M78/M79/M80) 在队, 等待终态。
  - 矛盾/疑问: 
    - message×HCG 全负交互 (M66/M67/M68/M72), 说明 HCG 交付轴上叠加 message 变换
      无价值。但 CTF 是 token 质量轴 (精炼 cluster token 源), 非 message 变换, 与
      HCG 组合不在已验证的负交互模式内 — 是唯一未测的正交组合格。
    - M58-DET-DRP 确认 detail 与 DRP 简洁回写不协同, 但 detail × 迭代 (M75/M76) 仍在
      队列中检验, 两者机制不同 (迭代是逐步精化, 非单次简洁回写)。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M81-CTF-HCG**: CTF (per-scale FFN 精炼 cluster token) × HCG (正确多尺度交付)。
    填补 {token 质量}×{交付} 正交格 — CTF 单轴 0.4995 未破顶, HCG 单轴 0.5002 未破顶,
    两者从未组合。若瓶颈确在 readback/融合 (CTF 分析结论), HCG 修复交付 + CTF 提升
    token 源质量 = 同时解决两处短板 → 可能破顶。
  - **M82-CTF-DET**: CTF × detail message。{token 质量}×{message 构造} 正交格。CTF
    精炼 token 源 + detail 把回写改为残差校正, 两轴独立有效但从未叠加。
  - **M83-REAG-CASC-DET**: REAGG 修复链 (级联正确重聚合) × detail message。
    {重聚合修复}×{message detail} 补格 — M76-DET-REAGG 是 reag×detail (双缺陷),
    M79-REAG-CASC 是级联修复×context message, M83 同时修重聚合缺陷 + detail 残差,
    单一变量对照 M79 (加 detail) 和 M76 (加重聚合修复)。
  - 与 goal.json constraints 冲突校验:
    - 非 gate/路由/residual 系; CTF 是既有已通过变体 (M41), HCG/级联/detail 均既有。
    - 新增参数仅 CTF 的 per-scale FFN (M41 已存在), HCG/级联/detail 零参数。
    - 不改 schedule; FLOPs: CTF+HCG ≈ M41+HCG gather (无 attention), 估算 < 10G。
    - cluster 模块只更新 inst_feats ✓ (仍走 _cluster_to_points 回写路径)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260810-092647.md
================================================================================
