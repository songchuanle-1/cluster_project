================================================================================
  Motivation Review — cluster_project
  2026-08-07 21:03:25
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

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1−A0=+0.0118 (champion 0.5012 vs base 0.4894) | 需消融哪些设计必要 |
  | 显式 routing 有独立收益 | refuted | A3−A1=-0.0544 (TrueRoute 0.4468) | — |
  | 正确多尺度交付 (HCG) 破 0.5012 | **unverified** | M65-HCG 0.4982@ep21 续爬升 (no_impr 3/10) | P0 待终态 |
  | detail 残差 message 有效 | confirmed | D1=0.5003 (γ=+0.0109), M58/M66 组合跑中 | 与 CCP/交付 组合待测 |
  | per-scale 投影在正确交付下叠加 | unverified | M64-SSP=0.4928 残缺陷下终态 | M68-SSP-HCG 排队 |
  | 迭代 readback (M69/M70) 有效 | unverified | 未跑 | 排队 |
  | cluster bank 源质量 (CCP top-down) 有效 | **unverified** | 57+ 变体全改 readback, 从未改 cluster token | M71/M72 排队 |
  | **CCP×detail 组合有效** | **unverified** | **两个 confirmed 轴 (token质量×message构造) 从未正交** | **本次 M73/M74** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | DRP (champion) | 0.5012 | context 回写本体 | 确认核心假设 ✓ (准单尺度) |
  | D1-detail | 0.5003 | 残差 message 构造 | message 内容轴有效 |
  | M62-ORTG | 0.4979 | orth 正则重测 | 正交轴仍低于 champion |
  | M63-PSR | 0.4964 | per-scale 残差 message | 残缺陷下有效但 < champion |
  | M64-SSP | 0.4928 | per-scale 独立投影 | 残缺陷下机制被抑制 |
  | M61-SCT | 0.4854 | 顺序 readback | 顺序依赖子维度闭合 |
  | M65-HCG | running 0.4982 | 正确多尺度交付 (P0) | 检验中, 续爬升逼近 champion |
  | M66-DET-HCG | running 0.4750 | detail×HCG 组合 | 起步爬升 |
  | M52-CCR | running 0.4948 | cascade 精化 | no_impr 9/10 临近早停 |
  | M53-VAC | 进程未见 | variance-aug 上下文 | deathwatch 2/3 暂不处置 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); detail 有效 (0.5003, γ=+0.0109); 融合/门控/聚合/
    顺序依赖全 ≤ champion; routing 证伪。
  - 未验证: HCG 正确交付是否破顶 (M65 续爬升中); CCP 源质量是否有效 (M71/M72 排队);
    detail × CCP 的正交组合从未被测试。
  - **核心缺口 (本次)**: 队列已有 {token质量}×{交付} 2×2 (M71-CCP / M72-CCP-HCG / M65-HCG /
    champion) 与 {message构造}×{交付} 2×2 (M66-DET-HCG / M67-PSR-HCG / M58-DET-DRP /
    M60-DET-CSF), 但 **{token质量}×{message构造} 2×2 从未补格** —— CCP (源质量新轴) 与
    detail (确认有效的 message 构造) 正交性未测。若二者独立增益可叠加, 是破 0.5012 天花板
    的组合路径; 若互斥, 则揭示两轴信息冗余。
  - 矛盾/疑问: D1-detail (0.5003) 距 champion 仅 0.0009, 说明 message 构造轴已逼近饱和;
    CCP 是唯一未测的源质量轴。二者组合 (M73-CCP-DET) 是 2×2 因子矩阵的最后空白格。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M73-CCP-DET**: 在 ccp 包基础上设 cluster_message_type=detail. CCP 提供 top-down 传播
    的高质量 cluster token (源), detail 提供残差 message 构造 (内容). 因果机制: 细簇 token
    获全局上下文 → 残差 message 携带「局部-全局差」的更高质量信号 → readback 更新更准.
    若源质量是瓶颈, detail 已确认的 +0.0109 应叠加.
  - **M74-CCP-HCG-DET**: CCP×HCG×detail 三维满格. HCG 修复交付 (每点收真多尺度 token),
    CCP 提升 token 质量, detail 优化 message 内容. 三者正交, 是 {源质量}×{交付}×{message}
    因子矩阵的完整补格, 最可能破 0.5012 的组合路径.
  - 与先例同构: 与 M72-CCP-HCG ({token质量}×{交付}), M66-DET-HCG ({message}×{交付})
    完全同构, 是同一因子矩阵方法论的自然延伸.

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260807-210301.md
================================================================================
