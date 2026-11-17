================================================================================
  Motivation Review — cluster_project
  2026-08-29 10:14
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-29 10:07:43: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 近 24h 无 type=question;
    最近 decisions 为 skip_design/early_stop/queue_push/next_batch/code_sync/other,
    无保留型 route_change/question → 自主设计允许 (Phase 0.5 双闸门通过)
  - 触发原因: M147 推送后 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7
    max_tasks_per_gpu=2 = 4 槽位, 阈值 5) → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1=0.5012 vs A0=0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 | 关闭 |
  | 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C/CCP/CSF/FLM/pool | 关闭 |
  | loss 监督轴 | 5连败(关闭) | M140-144 (OBJG=0.5000 最佳) | 关闭 |
  | CSORT 跨 seed 稳定性 | 脆弱 | s1999=0.5020 / mean~0.495 | M149-SG 待验 |
  | **CSORT 尺度范围** | **本tick M145-ALL 证伪扩展** | ALL(含非相邻)=0.4920, 较 champion 掉 0.0100 | **最细对是否单独足够 (M152-F1)** |
  | write-back 冗余假设 (soft/hard) | 未测 | — | M150-OWC / M151-ODW 在队 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 相邻尺度对去相关破平台 | 唯一破 0.5012 机制, 但跨 seed 脆弱 |
  | **M145-CSORT-ALL (本tick 终态)** | 0.4920 | 全尺度对含非相邻扩展 | 证伪"多对更好": 多余/非相邻 loss 项有害, γ=-0.0100 vs champion |
  | M147-MLAY-CSORT (running) | — | CSORT×MLay 跨类组合 | 组合格最高性价比补格 |
  | M143-OBJG | 0.5000 | 目标感知 aux loss | loss 轴最佳但仍未破平台 |
  | M81-CTF-HCG (base) | 0.5012 | context 回写核心 | 跨 seed 亦敏感 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; 交互/注意力全灭; loss 监督轴关闭; CSORT 是唯一
    破平台机制 (0.5020) 但 seed 脆弱。
  - **新证据 (本tick)**: M145-CSORT-ALL = 0.4920 — 把去相关扩展到全尺度对 (含
    非相邻 8↔256) 反而掉 0.0100。这给出去相关轴的**关键边界信息**: loss 项的
    覆盖范围本身就是敏感旋钮, 多余对应关系 (coarse 对、非相邻对) 引入噪声。
  - 未验证: champion 用 2 个相邻对 (256↔64 和 64↔8)。M145 往"多"方向 (全对)
    扩展失败。那么**往"少"方向 (仅最细对 256↔64) 呢**? 去相关收益是否集中于
    最细尺度对应 (点级冗余最高处), 粗对 (64↔8) 是否只是噪声/扰动?
  - 矛盾/疑问: 若最细对单独足够 (F1 ≈ champion) → 粗对无贡献, 故事可简化为
    "最细簇去相关即可", 且 M145 的"多余项有害"得到双向印证; 若 F1 > champion
    → 粗对是主动噪声, 移除即破平台 (潜在路径到 0.51); 若 F1 < champion → 相邻
    多对共同必要, 排除"最细对单独足够"。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M152-CTF-HCG-CSORT-F1: champion (ctf_hcg_csort) 基础上, CSORT loss
    只作用于最细尺度对 lvl=0 (256↔64), 去掉粗尺度对 lvl=1 (64↔8)。零新增参数,
    零新增超参, **结构消融** (goal.json Phase1 明确允许"结构消融")。
  - 因果假设: "champion 的 CSORT 收益主要来自最细尺度对应 (点级冗余最高处);
    粗对 (64↔8) 的 token 关联松散, 其 loss 项是噪声"。这是去相关轴**尺度范围**
    维度 (champion 相邻对 / M145 全对 / M152 最细对) 的第三个点, 补完消融网格。
  - 消融干净性: F1 forward 绕过 CSORT 的 2 对累积 (调 C2F_ClusterAttn_CTF_HCG.
    forward), 仅累积 lvl=0, 保持 /num_pairs=2 归一化 — 最细对的梯度贡献与
    champion 完全一致, 只是粗对项缺失。避免 weight 放大混淆。
  - 与 banned[]/constraints 校验:
    - 非 gate系/语言路由系/attnpool/qcond/agg/multi/true_route/prune/nomask;
    - 非 3/4/6 层重复注入 (cluster_att_num_layers=1 不变);
    - 非大型 QKV 投影; 非调参 (零新增参数, 零新增超参, 非数值分布扫参);
    - 非 residual 系 (不改 message 构造/写回结构);
    - 非 loss 监督轴 (CSORT 是 diversity loss, 不是任务监督 aux loss — 该轴
      关闭的是 CLICA/CSIC/OBJG/LQA 类任务监督, CSORT 仍是去相关轴主力)。
    - FLOPs/显存: 纯张量运算, 零新增参数, ≤10G 满足。
    - 分支停止: 1999 首筛; 若 1999 峰值 <0.5020 或提升 <0.002 → F1 证伪
      "粗对无贡献", 记录为"相邻多对共同必要"证据。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260829-1014.md
================================================================================
