================================================================================
  Motivation Review — cluster_project
  2026-08-26 23:16:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    归因 seed-1999 红利, 结构真实 mean ~0.498)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-26 23:07:36: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 24h 内无 type=question;
    最近 route_change (08-26 01:10 M134-DUAL 轴关闭) 为已执行决策非保留 → 自主设计允许
  - 触发原因: M139-MLAY-DUAL-LEGACY 本 tick 推送后 waiting=4 < 容量4+1=5 → 自主补设计 1 个
  - 本 tick 新证据: **M137-DCMV-S42 终态 0.4920** — qia/DCMV 轴双 seed 确认弱
    (M133=0.4950 / M137=0.4920), 正式关闭 {qla,qia} 矩阵的 qia 侧。

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | {qla,qia}×{cluster KV} 2×2 矩阵 | 关闭 | M124=0.5010 ✓ / M133=0.4950 ✗ / M134=0.4970 ✗ / M137=0.4920 ✗ | 双 seed 补格完成 |
  | {decoder-access, 多层}×{DCA,DCM,DCMV} 叠加 | 关闭 | M125=0.4970 / M126=0.4980 / M136=0.4960 — 不叠加 | 关闭 |
  | MFP / CSORT / CTF-token-FFN | 证伪 | MFP 3-seed 均值 0.4950; CSORT 归因 seed1999 | 关闭 |
  | cluster token 同尺度实例判别性 (CLICA) | 未测 | M140-CLICA queued | InfoNCE 判别监督 |
  | cluster token 跨尺度实例一致性 (CSIC) | 未测 | M141-CSIC queued | 粗 token 对主导实例忠实 |
  | CLICA × CSIC 双监督交互 | 未测 | M142 queued | 判别性×一致性 2×2 组合格 |
  | **cluster token 目标感知 (OBJG)** | 未测 | **本次设计 M143** | 识别语言指定目标对象的簇 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M137-DCMV-S42 (本 tick 终态) | 0.4920 | qia 视觉通路 × seed42 复现 | 确认 qia 轴弱 + seed 敏感性; {qla,qia} 矩阵正式关闭 |
  | M139-MLAY-DUAL-LEGACY (本 tick 推送) | running | {2层 legacy}×{qla+qia 双通路} | 满强度正交组合正确天花板格 |
  | M138-MLAY-DUAL | running | {2层}×{qla+qia} (ctf_hcg base 缺陷) | 组合天花板格 (base 有缺陷, 结论看 M139) |
  | M120-MLAY-S42 / M121-DET-MLAY | running | MLay seed=42 / ×detail | seed 矩阵 + detail 组合 |
  | M140-CLICA / M141-CSIC / M142 | queued | token 信息量三条 loss 路径 | 判别性 / 一致性 / 双监督 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); 通路组合不叠加 (qla/qia 矩阵关闭);
    token-FFN/池化轴全灭; seed-1999 结构性红利确认。
  - 未验证: cluster token 信息质量的 loss 监督轴 —
    M140-CLICA (同尺度判别), M141-CSIC (跨尺度一致), M142 (双监督), 均 queued。
  - **本设计填补的缺口**: 三条 loss 路径覆盖"判别性"与"一致性"两个维度,
    但**没有覆盖任务相关的第三个维度 — 目标感知**。语言查询指定了唯一目标对象;
    如果 cluster token 能识别"哪些簇属于目标对象", context 回写会直接强化
    目标区域的 inst_feats → decoder 定位更准。这是与判别性(CLICA)、一致性(CSIC)
    正交的独立子假设, 且是三者中最直接服务定位任务的一个。
  - 矛盾/疑问: 若 CLICA/CSIC/OBJG 三变体全部 ≈0.501 → loss 监督轴被三个正交
    维度穷尽证伪, 结构与监督双双饱和, 需范式级新方向 (记为 question, 暂停自主
    设计, 等用户拍板)。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M143-CTF-HCG-OBJG: 在 champion ctf_hcg (M81=0.5012, seed 1999) 上给
    cluster token 加**目标对象感知** aux loss — 对含 GT 实例点的有效簇, 监督其
    预测"主导实例是否为语言指定目标" (BCE)。零推理成本, 训练时开启。
  - 因果假设: 当前 cluster token 由 mean-pool 聚合, 携带几何/内容信息但**不知
    道哪个簇是查询目标** → context 回写对目标区域无偏重。给簇 token 目标感知
    监督后, 回写 context 直接强化目标簇 → inst_feats 目标判别更锐 → 定位更准。
    一句话: "认识目标的簇 → 回写目标相关的 context → decoder 定位更准"。
  - 为什么是 loss 而非新模块: 与 CLICA/CSIC 同构 (token 信息量轴的第三条正交
    监督), 复用 clica 包的 token 暴露机制 (cluster_feats_list/cluster_ids_list
    已进 pred), 仅新增一个 MLP 分类头 + BCE, 不碰 cluster 注意力主干路径。
  - 与 CLICA 的区分: CLICA 做全实例判别 (所有实例互相分开, 不知道谁是目标);
    OBJG 做目标选择 (识别查询目标的簇)。判别 ≠ 选择。
  - 与 CSIC 的区分: CSIC 跨尺度一致 (粗簇对主导实例忠实); OBJG 同尺度内目标
    选择。正交。
  - 与 banned[]/constraints 校验:
    - 非 gate/非 langroute/非 attnpool/非 residual/非 true_route/非 prune/
      非 nomask/非 3-6层注入/非大型投影/非重复注入。
    - 非调参: 新 loss = 新优化 landscape (目标信号直接监督 cluster token),
      不是数值配置改动; λ=0.1 沿用既有 aux loss 量级约定 (loss_weight[6]=0.1,
      CLICA=0.1, CSIC=0.1), 非临时拍值。
    - FLOPs: 仅 ~328 token 级 MLP+BCE, 可忽略 → ≤10G 约束满足。
    - 新增参数: 分类头 Linear(256,128)+Linear(128,1) ≈ 33K, 峰值显存增量可忽略。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260826-2316.md
================================================================================
