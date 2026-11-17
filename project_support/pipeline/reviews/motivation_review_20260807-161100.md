================================================================================
  Motivation Review — cluster_project
  2026-08-07 16:11:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云
    特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'
    假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 (DRP) 0.5012 (done_complete 36/50)
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
  | 正确多尺度交付 (HCG) 破 0.5012 | **unverified** | M65-HCG 运行中 (14/50, 0.4940 起步爬升) | P0 待终态 |
  | detail 残差 message 有效 | confirmed | D1=0.5003 (γ=+0.0109) | 与 HCG/CCP 协同排队 |
  | per-scale 投影在正确交付下叠加 | unverified | M64-SSP=0.4928 残缺陷下 (本 tick 终态) | M68-SSP-HCG 排队 |
  | 迭代 readback (M69/M70) 有效 | unverified | 未跑 | 排队 |
  | **cluster bank 源质量 (top-down 传播) 有效** | **unverified** | **57+ 变体全改 readback, 从未改进 cluster token 本身** | **本次 M71/M72** |
  | 融合权重/门控/聚合/顺序依赖 | confirmed ≤champion | SWI/CSF/SCF/QSF/SCT/M61 全 < champion | 各轴闭合 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | DRP (champion) | 0.5012 | context 回写本体 | 确认核心假设 ✓ (准单尺度) |
  | D1-detail | 0.5003 | 残差 message | message 内容轴有效 |
  | M62-ORTG | 0.4979 | orth 正则重测 | 正交轴仍低于 champion |
  | M63-PSR | 0.4964 | per-scale 残差 message | 残缺交付下有效但 < champion |
  | M64-SSP | 0.4928 | per-scale 独立投影 | 本 tick 终态: 残缺交付下机制被抑制 |
  | M60-DET-CSF | 0.4973 | detail+CSF 组合 | 融合轴再闭一格 |
  | M61-SCT | 0.4854 | 顺序 readback (粗→细) | 顺序依赖子维度闭合 |
  | M65-HCG | running 0.4940 | 正确多尺度交付 (P0) | 检验中 |
  (来源: pipeline/analyses/ + experiments.csv + 本 tick 终态 M64-SSP)

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (但准单尺度, 粗尺度交付残缺); detail 有效; 融合/门控/聚合/
    顺序依赖全 ≤ champion; routing 证伪。
  - 未验证: 正确交付 (HCG) 是否破顶; per-scale 投影/残差 message 在正确交付下是否叠加;
    迭代 readback 是否有效。
  - **核心缺口 (本次)**: 57+ 变体全部只改 readback (message 构造/加权/交付/顺序), 从未
    改进 **cluster bank 输出的 cluster token 质量**. cluster_feats 始终是 `scatter_mean`
    的原始级联聚合 (lvl0 从点聚合, lvl1 从 lvl0 token 聚合, lvl2 从 lvl1 token 聚合),
    即纯 bottom-up 压缩. 模块名为 "C2F (Coarse-to-Fine)", 但 coarse→fine 的 top-down
    信息传播从未实现. 粗尺度 (8/64 簇) 的全局场景上下文只存在于最粗 token 中, 细簇 token
    是纯局部 mean, 无全局感知. 所有 readback 机制消费的都是这个局部噪声为主的 token 集.
  - 矛盾/疑问: 若 readback 是瓶颈, 57 个变体应有一个明显突破; 实际全收敛 ≤0.5012 →
    瓶颈可能不在 readback 而在 **context 源 (cluster token 质量)**. 这是本故事的未测轴.

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M71-CCP (Coarse-to-Fine Cluster Context Propagation)**: 用已存在的父子映射
    (cluster_ids_list, 长度 K_{lvl-1}) 把粗簇 token 的全局上下文 top-down 注入细簇 token:
    对 lvl=2→1→0, `child_feats += parent_feats.gather(parent_ids)`. 零新增参数, 纯新信息
    路径. 因果机制: 细簇 (256) 局部但噪声大, 粗簇 (8) 全局但被残缺陷压制; CCP 让每个
    细簇 token 携带"局部+全局"层级上下文, readback 消息同时含局部细节与全局布局.
    这直接补上模块命名中缺失的 C2F 半边. 在 DRP (champion) 基座上测, 粗尺度经细簇
    token 间接到达点 (规避残缺陷).
  - **M72-CCP-HCG**: CCP × HCG 组合. HCG 修复交付 (每点收到真多尺度 token), CCP 提升
    token 质量. 二者正交, 是 {token 质量}×{交付正确性} 2×2 因子矩阵的完整补格:
      (无 CCP, 残缺交付)=champion 0.5012 ✓
      (CCP, 残缺交付)=M71-CCP 本次
      (无 CCP, HCG 正确交付)=M65-HCG 运行中
      (CCP, HCG 正确交付)=M72-CCP-HCG 本次
    M65-HCG 若有效, M72 应叠加; M71 单独若有效, M72 应 ≥ M71.
  - 与先例同构: 与 M68-SSP-HCG 的 {投影放置}×{交付} 2×2 补格完全同构, 本批补
    {token 质量}×{交付} 2×2, 是同一方法论的自然延伸.

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260807-161100.md
================================================================================
