================================================================================
  Motivation Review — cluster_project
  2026-08-24 17:13:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    CSORT 轴已关闭, 0.5020 归因 seed-1999 红利, 结构真实 mean ~0.498)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-24 17:07:38: Phase 1 NOT YET, continue exploring
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 24h 内无未决 question;
    最近 route_change (16:13 MFP 轴关闭) 为已执行决策非保留 → 自主设计允许
  - 触发原因: M126 推送后 waiting=5 < 容量5+1=6 (cluster_project 容量=5)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder 直接访问 cluster tokens (方向①) | partial | DCM(qla)=0.5010 > DCA=0.4970; DCMV(qia)=0.4950 弱 | DUAL 双通路 queued (M134) |
  | 多层注入 (方向②) | partial | MLay 2层=0.5010; 3/4/6层重复注入已证退化 (banned) | {②}×{qla}=M126 running; {②}×{qia}=M136 queued |
  | **{②}×{DUAL 双通路} 满强度组合** | **未测** | — | **本次设计 M138** |
  | MFP (masked feature prediction) | 证伪 (今日) | 3-seed 0.5020/0.4869/0.4960, 均值 0.4950 | 轴关闭 |
  | encoder-side token 质量轴 | 证伪 | CCL/CGA/BCF/SRL/MEMBANK 0.489-0.495 | 关闭 |
  | CSORT 跨 scale 去相关 | 证伪 | 3/4 seed 负, 0.5020 归因 seed1999 | 关闭 |
  | {qla,qia}×{cluster KV} 2×2 | 补格中 | qla=0.5010 ✓ / qia=0.4950 ✗ / DUAL queued | M134 补第4格 |
  | seed 稳健性 | 排队中 | DCM-S42/M122/M137 queued | — |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M133-DCMV (本 tick 终态) | 0.4950 | qia 视觉通路 cluster KV 直读 (DCM 对称版) | **qia 单轴弱** (-0.0060 vs DCM), decoder-access 收益在语言通路 |
  | M124-DCM | 0.5010 | decoder query 经 qla 共享 KV 读 cluster | decoder-access 轴最优, 平台饱和 |
  | M86-MLAY | 0.5010 | 2层注入 (方向②) | 多层注入有效但平台饱和 |
  | M128-DET-DCM | 0.4990 | detail × DCM | 无正协同 |
  | M130-MFP-S123 | 0.4960 | MFP seed123 | 完成 3-seed 判定 → MFP 关闭 |
  | M125-MLAY-DCA | running | {②}×{DCA 专用分支} | 2×2 {2层}×{DCA} 补格 |
  | M126-MLAY-DCM | running (本 tick 推送) | {②}×{qla 共享} | {②}×{qla} 补格 |
  | M134-DUAL | queued | qla+qia 双通路 (1层) | {qla,qia} 双通路叠加 |
  | M136-MLAY-DCMV | queued | {②}×{qia} | 2层×qia 补格 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); DCM qla=0.5010 (decoder-access 轴最优);
    MLay 2层=0.5010 (多层注入有效); MFP/CSORT/encoder-token 全灭。
  - M133 新证据: qia 视觉通路 cluster KV 访问单轴弱 (0.4950), decoder-access 收益
    集中在 qla 语言通路。双通路叠加 (M134) 是判定 qia 在组合中是否起作用的实验。
  - **未验证核心缺口**: 两个用户批准突破方向 (① decoder-access, ② 多层注入) 的
    **满强度正交组合** 从未测试。现有矩阵只覆盖 {②}×{单通路} (M126/M136) 和
    {双通路}×{1层} (M134)。{②}×{DUAL} 即 2层注入 × 双通路 是组合空间的天花板格。
  - 平台 ~0.501-0.502 是 seed-1999 结构上限。若满强度组合仍 ≤0.502, 则确认
    当前机制空间已探尽, 需范式级新方向。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M138-MLAY-DUAL: 2层注入 (cluster_att_num_layers=2) × 双通路
    (use_cluster_mem=True qla + use_cluster_mem_visual=True qia)。
    因果假设: 方向① 的最优实现 DCM(qla)=0.5010 与方向② 的最优 MLay=0.5010
    各自独立有效; 若两者收益正交可叠加, 满强度组合应破 0.502 平台;
    若仍 ≈0.501, 则确认平台是 seed-1999 结构天花板, 两方向组合不叠加。
    结果无论正负都推进故事: 破顶 → 故事闭环; 不破 → 平台饱和证据闭环。
  - 与 banned[]/constraints 校验:
    - 非 gate 系/非 langroute/非 attnpool/非 residual/非 true_route/非 3-6层注入
      (2层 = MLay 已验证档位, 非重复注入); 非调参 (零新超参, 复用已验证结构标志)。
    - FLOPs 与 DCM/DUAL 同量级 (仅 KV concat, 无新模块), ≤10G 约束满足。
    - 不设计 seed 以外数值扫描; 纯结构组合补格。
  - 条件独立性: 不依赖 M126/M134/M136 结果 — 直接回答满强度组合问题,
    即使单通路组合都失败, 本实验仍判定"组合不叠加"这一独立结论。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260824-1713.md
================================================================================
