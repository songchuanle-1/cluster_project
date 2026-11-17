================================================================================
  Motivation Review — cluster_project
  2026-08-08 04:08:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云
    特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
    假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1/DRP 0.5012 (done_complete 36/50)
  - Gap: +0.0088 | Phase 1 (NOT YET) — 继续自主设计服务指标提升
  - 硬约束: FLOPs≤10G / 禁改 schedule / Phase1 禁调参只许结构性机制变更 / 分支停止<0.002 /
    cluster 只更新 inst_feats / 默认仅最后1层注入 / 禁 N² attention / seed 1999
  - banned: gate系/语言路由系/attnpool/qcond/agg/multi/prune/nomask扩展/3-4-6层重复注入/
    大型QKVO/true_route/residual系(B5/E4)/Phase1 调参系
  - 活跃保留检查 (双源): ① goal.json constraints 无"活跃保留"条款 ② decisions/_index.md
    近 10 条无 route_change/question 保留关键词 — 无保留, 可自主设计.

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1−A0=+0.0118 (champion 0.5012 vs base 0.4894) | 需消融哪些设计必要 |
  | 显式 routing 有独立收益 | refuted | A3−A1=-0.0544 (TrueRoute 0.4468) | — |
  | 正确多尺度交付 (HCG) 破 0.5012 | **refuted** | M65-HCG=0.5002 终态 (γ=-0.0010 vs champion) | **交付轴闭合** |
  | detail 残差 message 有效 | confirmed | D1=0.5003 (γ=+0.0109) | 与迭代/CCP 组合待测 |
  | 迭代 readback (M69/M70) 有效 | unverified | M69-ITER running (刚推送) | M69/M70 待终态 |
  | cluster bank 源质量 (CCP top-down) 有效 | unverified | 57+ 变体全改 readback, 从未改 cluster token | M71-M74 排队 |
  | **迭代 × detail 组合有效** | **unverified** | **detail 确认有效, 迭代新轴从未与其正交** | **本次 M75/M76** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | DRP (champion) | 0.5012 | context 回写本体 | 确认核心假设 ✓ (准单尺度) |
  | M17-ORT | 0.5005 | orth 正则 | 弱正则有效但 < champion |
  | D1-detail | 0.5003 | 残差 message 构造 | message 内容轴有效 |
  | M65-HCG | 0.5002 | 正确多尺度交付 | **本 tick 终态: 交付修复≈champion, 交付轴闭合** |
  | M62-ORTG | 0.4979 | 真梯度 orth | 强约束与任务 loss 竞争 |
  | M60-DET-CSF | 0.4973 | detail+CSF 组合 | 融合轴叠加无增益 |
  | M63-PSR | 0.4964 | per-scale 残差 message | 残缺陷下有效但 < champion |
  | M64-SSP | 0.4928 | per-scale 投影 | 残缺陷下机制被抑制 |
  | M66-DET-HCG | running 0.4955@ep21 | detail×HCG | 本 tick 刷新 best, 距 champion 0.0057 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); detail 有效 (+0.0109); 交付正确性≈champion
    (M65-HCG 0.5002, 交付轴闭合); 融合/门控/聚合/顺序全 ≤ champion; routing 证伪。
  - 未验证: 迭代 readback (M69/M70 待跑); CCP 源质量 (M71-M74 排队)。
  - **核心缺口 (本次)**: 迭代轴 (M69-ITER/M70-REAGG) 和 detail message 轴 (D1 确认
    +0.0109) 从未正交。当前 M69-ITER 用 context message, M70-REAGG 用 context message,
    detail 只与单轮 readback 组合过 (D1/det_* 系列)。**{迭代}×{message} 2×2 因子矩阵
    最后一格** (iter×detail, reag×detail) 缺失。
  - M65-HCG 的启示: 交付轴已闭合 (修复交付≈0.000 增益), 剩余增量只能来自
    **消息内容精化** (detail, 已确认) 与 **多轮消息精化** (迭代, 新轴) 的组合。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M75-DET-ITER**: iter 包 + cluster_message_type=detail。因果机制: ITER 每轮用更新后
    feats 再 gather (消息逐步精化), detail 把 message 换成残差 (inst_feats - cluster_msg)
    → 每轮更新的都是"未对齐残差", 迭代放大残差校正信号。若 detail 的 +0.0109 与迭代的
    多轮精化正交 → 超 champion; 若迭代已覆盖残差信息 → ≈M69。
  - **M76-DET-REAGG**: reag 包 + cluster_message_type=detail。REAGG 每轮重新聚合 cluster
    token (cluster 表示进化), detail 残差使每轮更新的都是与当前 cluster 表示的偏差
    → 测试"cluster 进化 × 残差校正"是否叠加。
  - 与先例同构: det_hcg/det_ccp/det_ccp_hcg 均为"包复制 + cluster_message_type: detail"
    配置级组合, 已通过 Phase 1.6; 本批与 M66-DET-HCG (message×交付补格) 完全同构,
    是同一因子矩阵方法论在 {迭代} 轴上的自然延伸。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260808-040800.md
================================================================================
