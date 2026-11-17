================================================================================
  Motivation Review — cluster_project
  2026-08-31 08:37:14
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非
    routing。目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续 Phase 1 自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-31 08:07: Phase 1 NOT YET (champion 0.5020, gap +0.0080)
  - 活跃保留 (Phase 0.5 双闸门): goal.json constraints 无"活跃保留"条款;
    近 24h decisions 无保留型 route_change/question (均为 skip_design/
    early_stop/queue_push/terminal/next_batch) → 自主设计允许
  - 触发原因: 队列深度 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7
    max_tasks_per_gpu=2 = 4 槽位, 阈值 5) → 自主补设计

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1=0.5012 vs A0=0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 | 关闭 |
  | 多尺度 context 深度是核心收益 | 确认 (M86) | legacy 2层=0.5010 | 深度已 2 层 |
  | 组合不叠加 | 多例确认 | M146/M147/M148/M134 均 < champion | 组合线关闭 |
  | CSORT 跨 seed 脆弱 | 脆弱 | s1999=0.5020 / mean~0.495 | 对称项 load-bearing (M149) |
  | 去相关操作数 (源侧→精炼→receiver) | 在队消融 | M155-RF/M157-PMD 在队 | 操作数维度完成中 |
  | **cluster token 信息量是瓶颈 (M134)** | **诊断** | M140-144 五连败 (loss 监督) | **token 缺几何锚定 — 结构注入从未测** |
  | **token 几何信息 (centroid/radius)** | **未检** | 分划器算 centroid 却丢弃 | **本设计 M159-GEO + M160-GEO-SH** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 源侧跨尺度 token 去相关 | 唯一破平台机制之一 |
  | M151-ODW (本tick 终态) | 0.4970 | 硬约束正交写回 | 写回正交轴关闭 (软/硬双证伪) |
  | M150-OWC (本tick 终态) | 0.4920 | 软 loss 正交写回 | 写回正交轴关闭 |
  | M149-CSORT-SG (本tick 终态) | 0.4940 | 非对称 stop-grad | 对称追逐项是收益负载 |
  | M148-CSORT-DCM | 0.4990 | CSORT×decoder-access | 组合不叠加再证 |
  | M134-DUAL | 0.4970 | 双通路 decoder-access | **瓶颈定位: token 信息量, 非通路数** |
  | M51-DCA / M53-VAC / M42-WCA | ≤0.489 | 池化统计量变体 | 池化统计量轴封顶 (特征统计) |
  | M23-CMX | ~0.49 | max-pool 聚合 | max-pool 弱于 mean |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; 深度是核心; 组合不叠加; 写回正交轴关闭;
    loss 监督轴关闭; **特征池化统计量轴关闭** (mean/max/var/dual/weighted 全测)。
  - 未验证: **cluster token 的几何锚定** — 分划器 (PointCloudPartitioner) 在
    `cluster_layer` 中已计算每个簇的 centroid (`center = aggregate_cluster(pos, cid)`)
    用于 FPS 聚类, 但 `build_cluster_feats` 只聚合 `sp_feats` (特征均值), **位置信息
    被完全丢弃**。cluster token 只编码"簇内特征均值", 不含"簇在哪/有多大"。
    定位任务是 3D 空间回归 — token 无几何锚定 → 多尺度 context 写回缺少空间
    基准 → 定位精度受限。
  - 矛盾/疑问: 特征池化统计量 (M51/M53/M42) 失败 ≠ 几何统计量 (centroid/radius)
    无效 — 前者是对已聚合特征的二次变换 (信息冗余), 后者是注入**被丢弃的独立
    模态** (位置坐标)。点级有 posA 位置编码, 但 **cluster token 级无任何位置锚**。
    这是结构上缺失的一环, 从未被测试。
  - 结论: M134 诊断"token 信息量是瓶颈" + 池化统计量轴关闭 → 剩余的结构性信息
    增量是**把分划器已算出的几何 centroid/radius 注入 token** (新模态, 非新统计)。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M159-CTF-HCG-CSORT-GEO** (champion 单变量): 在 `build_cluster_feats` 每级
    聚合特征均值的同时, 级联聚合成员位置 → 每簇 centroid(3) + 归一化 radius(1),
    经 `geo_proj: Linear(4→C)` 投影后残差加到 cluster token。给 cluster token
    空间锚定。若 cluster_attn/CSORT 因 token 无几何信息而受限 → 注入后写回更准
    → 破 0.5020。失败结论 = "几何非瓶颈, 特征均值已含足够信息" (机制级结论)。
  - **M160-CTF-HCG-CSORT-GEO-SH** (控制组): 同 GEO 但 centroid/radius 按簇序
    固定偏移重排, 破坏"簇↔位置"内容对应, 只保留几何统计量的结构注入。若
    GEO-SH ≈ GEO → 收益来自结构容量非几何内容; 若 GEO-SH < GEO → 几何内容
    是关键。与 M158-PMD-SH (shuffled 控制) / A4-shuffle 同构, 保证 GEO 结论
    可解释。
  - 预期推进: 无论成败, M159/M160 关闭或确认"cluster token 几何锚定"假设 —
    M134 诊断 (token 信息量瓶颈) 在 loss 监督轴关闭后的最后一个结构性检验。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260831-083714.md
================================================================================
