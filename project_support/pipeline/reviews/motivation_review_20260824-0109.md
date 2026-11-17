================================================================================
  Motivation Review — cluster_project
  2026-08-24 01:09:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    CSORT 轴已关闭, 0.5020 归因 seed-1999 红利)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-24 01:07:42: Phase 1 NOT YET, continue exploring

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder 直接访问 cluster tokens (方向①) | partial | DCM=0.5010 (qla 共享通路) > DCA=0.4970 (专用分支); 平台未破 | qia 视觉通路未测; 组合未定 |
  | 多层注入 (方向②) | partial | MLay 2层=0.5010; 3/4/6层重复注入已证退化 (banned) | 与其它机制叠加未定 |
  | MFP (masked feature prediction) | unconfirmed | M119=0.5020 tie champion (seed1999) — 唯一不伤的 encoder-side 机制 | seed 矩阵判定中 (M129/M130 running) |
  | encoder-side token 质量轴 (CCL/CGA/BCF/SRL/MEMBANK) | 证伪 | 0.489-0.493 全灭 | 关闭 |
  | CSORT 跨 scale 去相关 | 证伪 | 3/4 seed 负, 0.5020 归因 seed1999 | 关闭 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M119-MFP | 0.5020 | 特征级 mask 重建 aux loss 提升 cluster token 完整性 | encoder-side 唯一不伤, tie champion (seed1999, 机制性未定) |
  | M124-DCM | 0.5010 | decoder 经 qla 语言通路读 cluster context | decoder-access 轴最优 (0.5010), 持平平台 |
  | M123-DCA | 0.4970 | decoder query 专用分支 cross-attend cluster | 弱于 DCM, 轴内对比淘汰 |
  | M86-MLAY | 0.5010 | 2层注入 (方向②) | 多层注入有效但平台饱和 |
  | M128-DET-DCM | 0.4990 (running 22/50) | detail message × DCM | 运行中, 未决 |
  | M129-MFP-S42 / M130-MFP-S123 | running | MFP seed 对照 | 判定 MFP 机制性 (关键) |
  | M81-CTF-HCG | 0.5012 | 正确多尺度交付 | 稳定 ~0.501 平台 (跨 seed mean ~0.498) |
  | M95-CTF-HCG-CSORT | 0.5020 | 跨 scale 正交化 | seed1999 outlier, 轴已关闭 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); decoder-access 轴 DCM 最优 (0.5010);
    2层注入有效 (0.5010); MFP 不伤 (0.5020, 未定机制性)。
  - 未验证: ① MFP 是否真实机制 (M129/M130 running); ② decoder-access 与其它
    独立机制叠加能否破 ~0.501 平台 (M125/M126/M131 排队); ③ 是否有组合能突破
    seed-1999 结构上限 (~0.501-0.502)。
  - 矛盾/疑问: 多个独立机制 (MFP/DCM/MLay) 全部收敛于 0.501-0.502 平台,
    M95=0.5020 已被证伪为 seed 红利 → 平台 ~0.501 很可能是 seed-1999 的
    结构天花板, 单一机制无法破顶, 必须依赖**正交机制组合**。
  - 组合历史警示: CCP×HCG=0.4950, CCP×detail=0.4952, REAGG×HCG=0.5008 (无协同)
    —— 组合并非必然加性, 但 MFP×MLay 两轴从未同时激活过, 且各自是各自轴的
    最优实现, 仍是当前最高价值的未测格。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 组合选择: MFP (encoder-side 特征完整性 aux loss, 0.5020) × MLay (2层注入,
    0.5010)。两轴正交: MFP 让 cluster token 携带更完整的点云特征 (token 内容),
    MLay 让 context 在 2 个 encoder layer 回写 (写回深度)。二者从未组合:
    {MFP, MLay, DCM} 三角两两组合中, MFP×DCM (M131)、MLay×DCA (M125)、
    MLay×DCM (M126) 均已设计, 唯缺 MFP×MLay → 本次补全。
  - 条件: 依赖 MFP seed 验证结果 (depends_on M129/M130), 若 MFP 被判 seed 红利
    (同 CSORT), M132 一并撤回, 避免浪费槽位 — 与 M131 相同的条件设计。
  - 预期: 若 > champion 0.5020 → MFP×MLay 组合破顶, 故事线推进至
    "正交机制叠加 (encoder 内容 × 写回深度)"; 若 ≈0.501 (平台) → 确认
    seed-1999 结构上限, encoder-side 组合轴关闭, 聚焦 decoder-side。
  - 排除方向: 不设计纯 seed 变体 (M129/M130/M122 已覆盖)、不设计 3/4/6 层注入
    (banned)、不设计 gate 系 (banned)、不设计 N² attention (用户保留)、
    不设计 encoder-side 新 token 质量机制 (CCL/CGA/BCF/SRL/MEMBANK 全灭, 轴证伪)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260824-0109.md
================================================================================
