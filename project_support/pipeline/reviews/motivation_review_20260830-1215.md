================================================================================
  Motivation Review — cluster_project
  2026-08-30 12:15
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-30 12:07: Phase 1 NOT YET (champion 0.5020, gap +0.0080)
  - 活跃保留 (Phase 0.5 双闸门): goal.json constraints 无"活跃保留"条款;
    近 24h decisions 无保留型 route_change/question (本 tick 之前为 skip_design/
    early_stop/queue_push/next_batch) → 自主设计允许
  - 触发原因: M150 推送后 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7
    max_tasks_per_gpu=2 = 4 槽位, 阈值 5) → 自主补设计
  - 资源窗口: server-6 M120-MLAY-S42 no_impr=9/10 即将早停 → 空出 1 槽且
    server-6 队内无 waiting → 需补 server-6 变体防空转

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1=0.5012 vs A0=0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 | 关闭 |
  | 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C/CCP/CSF/FLM/pool | 关闭 |
  | loss 监督轴 | 5连败(关闭) | M140-144 | 关闭 |
  | 多尺度 context 深度是核心收益 | 确认 (M86) | 2层 legacy=0.5010 vs 1层=0.5012 (持平) | 深度已 2 层 |
  | CSORT 跨 seed 稳定性 | 脆弱 | s1999=0.5020 / mean~0.495 | M149-SG 在跑 |
  | CSORT 尺度范围 | M145-ALL 证伪扩展 | ALL=0.4920 | M152-F1(最细对)+M156-CP(粗对) 在队/本设计 |
  | write-back 正交 (soft/hard) | 未测 | — | M150-OWC(跑)/M151-ODW(队) |
  | 全局场景尺度 (K=1) | 未测 | 3 尺度 [256,64,8] 无场景级 token | M154-GSC 在队 |
  | **CSORT 作用目标 vs 交付消息对齐** | **未测** | CSORT 作用于原始质心, 消息用 CTF 精炼 token | **M155-RF (本设计)** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 跨尺度 token 去相关 | 唯一破 0.5012 平台机制之一 |
  | M86-MLAY (2层 legacy) | 0.5010 | 多尺度 context 深度 | 隔离出深度是核心收益来源 |
  | M119-CTF-HCG-MFP | 0.5020 | masked 重建 (token 完整性) | 与 CSORT 平级独立 0.5020 |
  | M147-MLAY-CSORT (本tick 终态) | 0.4970 | MLay×CSORT 组合 | 再证 architecture×loss 不叠加 |
  | M148-CSORT-DCM | 0.4990 | CSORT×decoder-access | 证伪 decoder-access×CSORT 组合 |
  | M145-CSORT-ALL | 0.4920 | 全尺度对去相关 | 证伪"多对更好" |
  | M146-CSORT-DET | 0.4970 | CSORT×detail 消息 | message-type 轴关闭 (context 胜) |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); 多尺度 context 深度是核心收益 (M86);
    组合线 (architecture×loss / loss×decoder-access) 多例不叠加 (M146/M147/M148 再证);
    CSORT 对范围扩展有害 (M145-ALL)。
  - 未验证: **CSORT 的惩罚对象与交付消息错位** — champion 中 CSORT 约束的是
    原始 partitioner 质心 (cluster_feats_list), 而真正广播给点的 context 是
    CTF 精炼后的 token (refined_cluster_feats)。若 CTF FFN 混合特征维度使去相关
    后的质心在精炼后重新相关, 则 CSORT 优化的是 proxy 而非实际消息 — 去相关
    收益可能被 FFN 稀释。这是"去相关轴唯一有效方向"上从未检查过的对象错位。
  - 未验证 (尺度作用域): M152-F1 (最细对 256↔64) 在队; 粗对 (64↔8) 单独
    作用域从未测试 → M156-CP (本设计) 补全消融网格。
  - 矛盾/疑问: 若 CSORT 收益集中在最细对, 则"点级冗余"是核心; 若两对独立,
    则解相关是尺度边界通用属性。M152/M156 并行回答。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M155-CTF-HCG-CSORT-RF** (server-4): 把 CSORT 的 abs-cosine 惩罚从原始质心
    移到 CTF 精炼后 token 上 — 直接约束被 HCG 广播的实际消息跨尺度互补。
    填补"regularizer 与交付消息对齐"缺口: 若精炼层重新相关是 seed 脆弱/平台
    瓶颈之一 → 破 0.5020; 若等价 → 证明原始质心去相关已足够 (CTF 保去相关)。
  - **M156-CTF-HCG-CSORT-CP** (server-6): 粗尺度对 (64↔8) 单独去相关 —
    补全 CSORT 尺度范围网格 (champion 相邻对 / M145-ALL 全对 / M152-F1 最细对 /
    M156-CP 粗对), 与 M152-F1 并行定位 CSORT 有效作用域。
  - 预期推进: 无论成败, 两变体分别关闭"对象错位"与"粗对作用域"两个未检假设;
    M155 若破平台 → 新 champion 候选; M156 与 M152 合并 → 确定 CSORT 对范围
    设计是否需调整。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260830-1215.md
================================================================================
