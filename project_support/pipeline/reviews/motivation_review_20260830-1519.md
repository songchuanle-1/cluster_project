================================================================================
  Motivation Review — cluster_project
  2026-08-30 15:19
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非
    routing。目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-30 15:07: Phase 1 NOT YET (champion 0.5020, gap +0.0080)
  - 活跃保留 (Phase 0.5 双闸门): goal.json constraints 无"活跃保留"条款;
    近 24h decisions 无保留型 route_change/question (均为 skip_design/
    early_stop/queue_push/terminal/next_batch) → 自主设计允许
  - 触发原因: M151 推送后 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7
    max_tasks_per_gpu=2 = 4 槽位, 阈值 5) → 自主补设计; server-6 队内无 waiting
    (M122/M156 均在跑, 终态后防空转)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1=0.5012 vs A0=0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 | 关闭 |
  | 多尺度 context 深度是核心收益 | 确认 (M86) | 2层 legacy=0.5010 | 深度已 2 层 |
  | 组合不叠加 (architecture×loss / loss×decoder) | 多例确认 | M146=0.4970/M147=0.4970/M148=0.4990/M153 在队 | 破平台需新信息路径 |
  | CSORT 跨 seed 脆弱 | 脆弱 | s1999=0.5020 / mean~0.495 | 对称项是收益负载 (本tick M149-SG=0.4940) |
  | **CSORT 操作数 (loss 约束对象)** | **未检** | 源侧 token (原始质心/M155 精炼) | **receiver 侧逐点消息未测 → 本设计 M157** |
  | **PMD 收益是内容驱动还是结构压力** | **未检** | — | **shuffled 对照 → 本设计 M158** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 源侧跨尺度 token 去相关 | 唯一破平台机制之一 |
  | M119-CTF-HCG-MFP | 0.5020 | masked 重建 (token 完整性) | 3-seed 证伪, 轴关闭 |
  | M148-CSORT-DCM | 0.4990 | CSORT×decoder-access | 组合负交互, decoder 组合关闭 |
  | **M149-CSORT-SG (本tick 终态)** | 0.4940 | 非对称 stop-gradient 去相关 | **对称追逐项是收益负载; 非对称方向关闭** |
  | M145-CSORT-ALL | 0.4920 | 全尺度对去相关 | 证伪"多对更好" (loss 范围扩展有害) |
  | M152/M156 (在队/在跑) | — | 尺度范围消融 | 补全 CSORT 作用域网格 |
  | M155-RF (在队) | — | CSORT 移到精炼 token | 源侧对象错位检查 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; 深度是核心收益; 组合线多例不叠加; M149-SG 证伪
    "对称追逐环是 CSORT 脆弱来源" (非对称去掉反而丢 0.008); 源侧 CSORT 操作数
    只有 token 层 (原始质心 → 精炼 token, M155) 被检查。
  - 未验证: **receiver 侧操作数** — CSORT 家族 (M95/M150/M151/M152/M153/M154/
    M155/M156) 全部约束在**源侧 cluster token / 消息构造** (token 去相关、写回
    正交、尺度范围、全局 token、精炼 token)。从没人把 abs-cosine 去相关作用到
    **decoder 实际消费的逐点 scale message** (gather 后的 msg_256/msg_64/msg_8)。
    由于每个点只 gather 少数 token, 源侧 token 去相关不保证点级收到的消息跨尺度
    互补 — 去相关收益可能在 gather 后被稀释。这是"去相关轴唯一有效方向"上最后
    一个未检的操作数 (receiver 侧)。
  - 未验证 (控制组): 若 PMD 上分, 需区分是"内容感知去相关" (消除同点跨尺度真实
    冗余) 还是"结构正交压力" (把任意向量推正交, 与 M145-ALL 的"多对有害"同构)。
    需要 shuffled 对照隔离内容对应。
  - 矛盾/疑问: M145-ALL 证伪"loss 范围扩展" (更多 token 对有害), 但 PMD 是**换操作数**
    而非扩范围 — 若 PMD 掉, 说明去相关压力本身已饱和; 若 PMD 上, 说明操作对象
    才是关键。与 M145 不矛盾, 是操作数维度 (非范围维度) 的消融。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M157-CTF-HCG-CSORT-PMD** (server-4): 把 abs-cosine 去相关的操作数从源侧
    cluster token 换成 **receiver 侧逐点 scale message** (champion 单变量, CSORT→PMD)。
    填补"操作数维度"缺口: 若点级消息跨尺度仍冗余 (gather 稀释源侧去相关) →
    破 0.5020; 若掉 → 源侧去相关已足够, receiver 侧操作数排除。零新增参数。
  - **M158-CTF-HCG-CSORT-PMD-SH** (server-6): PMD 的 shuffled 对照 — 相邻尺度对
    中 lvl+1 侧按固定偏移重排, 破坏同点跨尺度内容对应, 只保留结构正交压力。
    若 PMD-SH ≈ PMD → PMD 收益非内容驱动 (结构压力, 与 M145-ALL 同构); 若
    PMD-SH < PMD → 内容对应是关键 (去相关收益来自消除同点跨尺度真实冗余)。
    与 A4-shuffle 控制组 (routing 内容 vs 结构) 同构, 保证 PMD 结论可解释。
  - 预期推进: M157 无论成败关闭"receiver 侧操作数"假设; M158 保证该结论的
    可解释性 (内容 vs 结构)。两变体组合构成去相关轴操作数维度的完整消融。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260830-1519.md
================================================================================
