================================================================================
  Motivation Review — cluster_project
  2026-08-29 01:16
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-29 01:07:37: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 近 24h 无 type=question;
    最近 10 条 decisions 为 queue_push/early_stop/skip_design/next_batch/other(bugfix),
    无保留型 route_change/question → 自主设计允许 (Phase 0.5 双闸门通过)
  - 触发原因: M146 推送后 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7
    max_tasks_per_gpu=2 = 4 槽位, 阈值 5) → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1=0.5012 vs A0=0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 | 关闭 |
  | 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C=0.4865 / CCP=0.4934 / CSF/FLM/pool | 关闭 |
  | delivery×delivery 组合 | 关闭 | 6 次不叠加 (M125/126/134/136/138/139) | 关闭 |
  | loss 监督轴 | **5连败(关闭)** | M140=0.4970/141=0.4960/142=0.4890/143-OBJG=0.5000/144-LQA=0.4930(本tick) | 关闭 |
  | CSORT 跨 seed 稳定性 | 脆弱 | s1999=0.5020 / s42=0.494 / s123=0.493 / s2026=0.490 (mean~0.495) | M149-SG(修复后) 待验 |
  | write-back 冗余假设 (soft loss) | 未测 | — | M150-OWC 在队 |
  | **write-back 冗余假设 (hard structure)** | **未测** | champion 的回写 `feats+msg` 未从结构上保证互补性 | **本设计 M151** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | cross-scale orth 破平台 | 唯一破 0.5012 机制, 但跨 seed 脆弱 |
  | M144-LQA (本tick 终态) | 0.4930 | cluster-token 语言对齐 aux loss | loss 轴第 5 败 → 该轴整体关闭 |
  | M143-OBJG | 0.5000 | 目标感知 aux loss | loss 轴最佳但仍 < base 0.5012 |
  | M39-C2C / M71-CCP | 0.4865/0.4934 | token 交互/传播 | 交互轴证伪 |
  | M81-CTF-HCG (base) | 0.5012 | context 回写核心 | 跨 seed 亦敏感 (s123=0.494) |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; 交互/注意力全灭; loss 监督轴 5 连败关闭;
    CSORT 是唯一破平台机制但 seed 脆弱。
  - 未验证: **write-back 的互补性是否必须从结构上保证**。champion 的 residual
    回写 `feats + msg` — msg 聚合自 point_feats, 天然与 inst_feats 相关。相关分量
    只做"再确认"(reinforce), 只有正交分量提供新 context。M150-OWC 用 loss 惩罚
    相关性 (软约束, 模型可权衡); **没有任何变体从结构上保证回写正交** (硬约束)。
  - 关键证据: 去相关轴是唯一有效方向 (CSORT 破平台)。该轴的逻辑补全:
    token 之间 (CSORT/ALL/SG) → write-back vs inst_feats (OWC soft) →
    **write-back 结构正交 (ODW hard)**。软/硬两种强制方式对照, 若 OWC 有效而
    ODW 失效 → 说明软约束即可, 硬约束过强伤 reinforce; 若 ODW 有效 → 结构保证
    优于 loss 权衡。无论哪种, 澄清回写机制是 "complement" 还是 "reinforce"。
  - 矛盾/疑问: 若 ODW 掉点明显 → 说明 reinforce 是必要的 (相关回写有独立价值),
    排除 "回写只需互补" 假设 — 排除一个方向也是故事推进。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M151-CTF-HCG-CSORT-ODW: champion (csort) 基础上, 在 cluster_attn forward
    末尾对 write-back message fm 做 **Gram-Schmidt 正交投影**: 移除 fm 平行于
    inst_feats 的分量, 只回写正交分量。零新增参数, 零新增超参, 确定性变换。
  - 因果假设: "residual 回写若与 inst_feats 相关则更新冗余 → 结构上保证
    msg ⊥ feats → 每次回写必然补充新 context → 实例特征更丰富 → 破 0.5020"。
    是去相关轴 (唯一有效方向) 的**硬约束操作数**, 与 OWC (软 loss) 构成对照。
  - 与 banned[]/constraints 校验:
    - 非 gate系/语言路由系/attnpool/qcond/agg/multi/true_route/prune/nomask;
    - 非 3/4/6 层重复注入 (cluster_att_num_layers=1 不变);
    - 非大型 QKV 投影; 非调参 (零新增参数, 零新增超参, 非数值分布扫参);
    - **residual 系辩**: banned 的 residual 系 (B5/E4) 是 message_type=residual 构造;
      ODW 不改 message 构造, 是在 write-back 上的确定性正交投影 — 不同机制。
    - FLOPs/显存: 纯张量运算, 零新增参数, ≤10G 满足。
    - 分支停止: 1999 首筛; 若 1999 峰值 <0.5020 或提升 <0.002 → ODW 证伪, 记录为
      "reinforce 必要" 证据。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260829-0116.md
================================================================================
