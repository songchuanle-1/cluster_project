================================================================================
  Motivation Review — cluster_project
  2026-08-27 04:12:00
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
  - check_goal 2026-08-27 04:07:44: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 近 24h 无 type=question;
    最近 route_change (08-26 01:10 M134-DUAL 轴关闭) 为已执行决策非保留 → 自主设计允许
  - 触发原因: M138 早停 + M140 推送后 waiting=4 < 容量4+1=5 → 自主补设计 1 个
  - 本 tick 新证据: **M138-MLAY-DUAL 终态 0.4990** — {2层}×{DUAL} 组合不叠加
    (base 有缺陷, 结论以 M139-legacy 为准); **M140-CLICA 已推送 server-4 gpu0**。

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | cluster token 结构变换 (FFN/交互/池化/融合) | 全灭 | CTF=0.4995 / C2C=0.4865 / CSF=0.4958 / FLM=0.4865 / pool 全灭 / TrueRoute=0.4468 | 关闭 |
  | 通路组合叠加 (qla/qia/MLay/detail ×) | 关闭 | M125/M126/M134/M136/M138 均不叠加 | 关闭 |
  | cluster token 同尺度实例判别 (CLICA) | 未测 | M140 queued (本 tick 推送) | InfoNCE 判别监督 |
  | cluster token 跨尺度实例一致 (CSIC) | 未测 | M141 queued | 粗 token 对主导实例忠实 |
  | CLICA × CSIC 双监督交互 | 未测 | M142 queued | 判别性×一致性 2×2 组合格 |
  | cluster token 目标感知 (OBJG) | 未测 | M143 queued | 识别语言指定目标对象的簇 |
  | **cluster token 语言语义对齐 (LQA)** | 未测 | **本次设计 M144** | 簇内容耦合查询语言语义 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M138-MLAY-DUAL (本 tick 终态) | 0.4990 | {2层}×{双通路} 组合 | 再证组合不叠加 (base 缺陷, 以 M139 定论) |
  | M139-MLAY-DUAL-LEGACY | running | {2层 legacy}×{双通路} 修正版 | 满强度正交组合正确天花板格 |
  | M120/M122-MLAY-S42/S123 | running/queued | MLay seed 矩阵 | seed 稳健性 |
  | M140-CLICA / M141-CSIC / M142 / M143-OBJG | queued | token 信息量 loss 监督轴 3 维 | 判别/一致/目标感知 |
  | M39-C2C (先例) | 0.4865 | intra-scale token 交互 | token 结构交互无增益 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); 结构性 token 变换全灭 (C2C/CSF/FLM/CTF 单测、
    pooling、TrueRoute); 通路组合不叠加; seed-1999 结构性红利确认。
  - 未验证: cluster token 信息质量的 loss 监督轴 — M140-CLICA / M141-CSIC /
    M142 (双) / M143-OBJG 均 queued, 尚无结果。
  - **本设计填补的缺口**: 已设计的三条 loss 路径分别用"实例判别性"(CLICA)、
    "跨尺度一致性"(CSIC)、"目标身份"(OBJG) 监督 cluster token, 但**三者都只用
    实例/目标的身份标签 (离散 id), 没有把查询语言的语义内容 (如 "red chair
    near the table" 的属性/关系) 注入簇 token**。cluster token 依旧对查询语义
    盲 —— 它不知道 "红椅子" 长什么样。LQA 直接把语言查询嵌入作为监督信号,
    让目标簇 token 的表示向查询语义靠拢, 是三个维度之外的第四正交维。
  - 矛盾/疑问: 若 CLICA/CSIC/OBJG/LQA 四维全部 ≈0.501 → loss 监督轴被穷尽证伪,
    结构与监督双双饱和, 需范式级新方向 (记为 question, 暂停自主设计, 等用户拍板)。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M144-CTF-HCG-LQA: 在 champion ctf_hcg (M81=0.5012, seed 1999) 上给
    cluster token 加**语言查询语义对齐** aux loss — 对含 GT 点的有效簇, 用
    InfoNCE 让"主导实例==目标"的簇 token 与语言查询嵌入 (proj_tokens 池化) 相似度
    高于非目标簇。零推理成本, 训练时开启。
  - 因果假设: 当前 cluster token 由 mean-pool 聚合, 携带几何/内容信息但**不知道
    查询语言的语义内容** → context 回写对目标区域无语义偏重。LQA 让目标簇 token
    的表示与查询语义对齐后, 回写 context 携带语义定向信息 → inst_feats 目标区域
    特征与查询语义更契合 → decoder 定位更准。
    一句话: "目标簇的 token 认识查询语义 → 回写 context 语义定向 → 定位更准"。
  - 与 OBJG 的区分: OBJG 是"是不是目标"的二值分类 (离散 id, 无语义内容);
    LQA 是"簇内容与查询语义的相似度"连续对齐 (携带属性/关系语义方向)。判别 ≠ 语义。
  - 与 CLICA/CSIC 的区分: CLICA/CSIC 用实例身份标签做判别/一致; LQA 用语言嵌入
    做语义定向, 三者信号源正交。
  - 与 banned[]/constraints 校验:
    - 非 gate系/非语言路由系 (langroute/langc2f/scale 是路由/条件机制; LQA 是
      loss 监督, 不改变前向信息流路径, 仅改变训练信号 → 非 banned)。
    - 非调参: 新 loss = 新优化 landscape (语言语义直接监督 cluster token),
      非数值配置改动; weight=0.1 沿用同轴既有约定 (CLICA/CSIC/OBJG 均 0.1);
      temperature=0.1 沿用 CLICA 约定。
    - FLOPs: 仅 ~328 token 级 Linear(256,64)+InfoNCE, 可忽略 → ≤10G 约束满足。
    - 新增参数: cluster_lqa_head Linear(256,64) ≈ 16.4K + 1 标量, 峰值显存增量可忽略。
    - 结构首筛 seed 1999 ✓; 非 N² attention (token 级, ~328 尺度) ✓; 禁改 schedule ✓。
  - 为何仍值得赌: 结构性 token 变换已被证伪 (C2C=0.4865), 但 loss 监督轴从未
    测试; LQA 是该轴上与既有三维信号源正交的第四赌注, 若四维全败即触发范式级
    question, 不追加更多变体。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260827-0412.md
================================================================================
