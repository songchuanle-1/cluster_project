================================================================================
  Motivation Review — cluster_project
  2026-08-27 21:14:52
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    跨 seed mean ~0.495, 归因 seed-1999 红利)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-27 21:07:36: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 近 24h 无 type=question;
    最近 route_change (08-26 01:10 M134-DUAL 轴关闭) 为已执行决策非保留 → 自主设计允许
  - 触发原因: M142 推送后 waiting=4 < 容量4+1=5 → 自主补设计 1 个
  - 本 tick 新证据: **M139-MLAY-DUAL-LEGACY 终态 0.4880** — {MLay 2层 legacy}×{DUAL
    双通路} 组合第 5 次确认不叠加, 且低于 baseline; 组合轴正式关闭。修正 base 后
    仍不叠加, 排除 base 缺陷导致误判的可能。

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012 | 关闭 |
  | cluster token 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C/CSF/FLM/pool/TrueRoute | 关闭 |
  | 通路组合叠加 (qla/qia/MLay/detail ×) | 关闭 | M125/M126/M134/M136/M138/**M139** 均不叠加 | 关闭 (5 次确认) |
  | 多层注入 (ctf_hcg@2) | 证伪 | M96-CTF-HCG-2LAY=0.4940 | 关闭 (legacy@2 有效=0.5010) |
  | 判别性 loss (CLICA) | 饱和 | M140=0.4970 < base 0.5012 | 判别轴无增益 |
  | CSORT 应用位置 (token vs message) | 非关键 | M109-CSORT-MSG=0.5010 ≈ M95=0.5020 | 位置轴关闭 |
  | champion CSORT 全尺度对去相关 | 检验中 | M145 queued | 非相邻对 8↔256 未测 |
  | loss 监督其余维度 (CSIC/OBJG/LQA) | 检验中 | M141 running / M143,M144 queued | 一致/目标/语义 |
  | **CSORT × detail message 组合** | 未测 | **本次设计 M146** | 去相关×残差回写互补? |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 跨尺度 orth 破平台 | 唯一破 0.5012 机制 (seed 脆弱) |
  | M109-CSORT-MSG | 0.5010 | message 级 CSORT | CSORT 位置非关键, 轴关闭 |
  | M139-MLAY-DUAL-LEGACY (本 tick 终态) | 0.4880 | 组合轴天花板格修正版 | 组合轴第 5 次确认不叠加, 正式关闭 |
  | M138-MLAY-DUAL (缺陷版) | 0.4990 | 组合轴 | 与 M139 共同关闭组合轴 |
  | M140-CLICA | 0.4970 | 判别性 loss | 判别轴饱和 |
  | D1-detail (message_type=detail) | 0.5003 | 残差回写 message | detail 机制单独有效 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; 结构变换全灭; 通路组合不叠加 (5 次); CSORT 位置非关键;
    CLICA 判别饱和; champion 跨 seed 脆弱 (mean~0.495)。
  - 未验证: **champion 的 cross-scale orth (CSORT) 与 detail 残差 message 是否叠加**。
    CSORT (0.5020) 与 detail (0.5003) 是仅有的两个独立有效且作用位点不同的机制:
    CSORT 在 cluster token 层 (输入侧去相关), detail 在回写 message 层 (输出侧残差)。
    两者从未在 champion base 上组合。若互补 → 每尺度携带去相关且带点级残差的 context
    → 回写信息容量最大 → 破 0.5020 平台。
  - 矛盾/疑问: 组合轴已 5 次不叠加, 但那些是 {delivery 机制 × delivery 机制} 的
    结构组合; CSORT×detail 是 {正则化 × delivery} 的跨类组合, 作用位点正交,
    与失败组合不属同类, 值得一格。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M146-CTF-HCG-CSORT-DET: 在 champion (ctf_hcg_csort, seed 1999) 上
    cluster_message_type: context → **detail** (残差回写 inst_feats - cluster_message
    + LayerNorm), 其余完全一致。零新增参数, 零新代码 (detail 路径已在 Encoder_layer
    实现), 物理包复制满足 Phase 3a 独立性。
  - 因果假设: CSORT 使粗 token 与细子簇聚合去相关 → 各尺度 context 互补; detail
    使回写 message = 残差 (inst_feats - context) → 保留点级细节。两个机制作用
    位点正交 (token 去相关 × message 残差), 组合后每尺度写入的是"互补且带细节"
    的 context → 定位更准 → 破 0.5020。一句话: "去相关的残差回写 → 信息更富 → 定位更准"。
  - 与 banned[]/constraints 校验:
    - 非 gate系/非语言路由系/非 residual 系 (detail 是 message 构造机制, 与 banned
      的 residual 系 (B5/E4 cluster_mode=residual) 不同: banned 的是 residual
      cluster aggregation mode, 这里 detail 是 cluster_message_type 残差回写,
      D1-detail 0.5003 已证有效非残差系)。
    - 非调参: detail 是信息流变更 (回写路径变化), 非数值配置改动; csort_weight=0.01
      沿用 champion; 结构首筛 seed 1999 ✓; 禁改 schedule ✓。
    - FLOPs/显存: detail 路径仅加一次 LayerNorm 减法, 可忽略 → ≤10G 约束满足。
    - 与"分支停止: 提升<0.002"约束: 若 M146 增益 <0.002 → CSORT×detail 组合格关闭。
  - 为何仍值得赌: 组合轴关闭的是同类的 delivery×delivery; CSORT×detail 是
    {已证有效的去相关} × {已证有效的残差回写} 的跨类组合, 位点正交, 且实现成本
    最低 (纯 config), 是当前最高性价比的补格。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260827-211452.md
================================================================================
