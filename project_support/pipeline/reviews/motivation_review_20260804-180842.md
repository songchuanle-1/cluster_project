================================================================================
  Motivation Review — cluster_project
  2026-08-04 18:08:42
================================================================================

## 1. Goal
  - Target: mIoU >= 0.5100 | Champion: posA_l1 (Lite/DRP) 0.5012 | Gap: +0.0088 | Phase: 1 (NOT YET)
  - goal.json description: cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被
    证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51。
  - Phase 0.5 活跃保留检查: goal.json constraints[] 无"活跃保留"字样条款; decisions/_index.md
    最近 10 条为 skip_design/queue_push/next_batch/terminal/question (question 仅关于 server-6
    集成方式, 非设计保留, 且 17:34 next_batch 已按可用槽=5 继续设计) → 双源无保留, 自主设计允许。
  - check_goal.py: Phase 1 NOT YET (champion=0.5012, target=0.5100, gap=+0.0088)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位 | confirmed | champion 0.5012 vs baseline 0.4894 (γ=+0.0118) | 距 target +0.0088 |
  | C2F routing 贡献 | refuted | A3 true_route=0.4468; A4 shuffle=0.4941; DRP(去路由)=0.5012 | — |
  | 读回形式 (additive/detail) 最优 | closing | BIL(0.4919)/NLR(0.4948)/FILM/FLM 全 < champion; DGC 在跑 | DGC 待验 |
  | 聚合池化 mean 最优 | partial | max/weighted 差于 mean; dual=M51-DCA 在跑; var=M53-VAC 待验 | DCA/VAC |
  | 级联精炼 | untested | — | M52-CCR 在跑 |
  | cluster token 表示富化 | untested | — | M53-VAC + M54-SAC 在跑 |
  | 融合机制 = 瓶颈 (CTF 分析) | partial | CTF(0.4995): 瓶颈在 readback/融合机制; 已试 XCA/CSF/SWI/M60 均 token 级或 gate 形式级 | point-level 内容自适应(M55-SCF) + 顺序依赖(本次 M61) |
  | 组合可叠加性 (detail/ORT/DRP) | untested | — | M56-M60 已入队 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion/DRP | 0.5012 | 多尺度 context 回写 | 核心假设确认 ✓ |
  | M17-ORT | 0.5005 | token 正交正则 | token 多样性有帮助但非瓶颈 |
  | M41-CTF | 0.4995 | cluster token FFN 精炼 | token 质量非瓶颈; 结论指向 readback/融合 |
  | M45-NCR | 0.4980 | soft readback | soft 稀释信息, 不如 hard gather |
  | M48-BIL | 0.4919 | 逐点双线性读回 | 乘法交互不稳定, 读回 expressiveness 轴基本闭合 |
  | M49-NLR | 0.4948 | 非线性 MLP 读回 | 非线性读回不破 ceiling, 闭合 expressiveness 轴 |
  | M44-CSF | 0.4958 | token 级跨尺度交叉注意力 | token 级跨尺度交互无益 |
  | M22-XCA | 0.4954 | 全部 token self-attention | N² 跨尺度交互无益 |
  | M50-DGC | running | difference-gated readback | readback 门控维度, no_impr 7/10 近早停 |
  | M51-DCA | running | dual mean+max 聚合 | 聚合信息量维度, no_impr 5/10 近早停 |

  关键规律 (30+ 变体): 读回形式/融合/选择/交互/调制/尺度数/组合全部收敛 ≤ 0.5012。
  融合机制轴从未被探过的一个子维度: 各尺度的融合权重是否应"看见"其他尺度已注入的 context。

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回读有效 (+0.0118); routing 无用; 读回 expressiveness 轴闭合;
    token 质量非瓶颈; token 级/静态 gate 级融合非瓶颈。
  - 未验证 (本次队列覆盖):
    (a) point-level 内容自适应的多尺度融合 — M55-SCF (等待队列, 已入队 17:11)
    (b) 组合可叠加性 detail/ORT/DRP — M56-M60 (已入队 17:34)
    (c) 聚合池化 (DCA 在跑/VAC 待验)、级联 (CCR 在跑)、空间信号 (SAC 在跑) — 队列中
  - **新缺口 (d) 融合机制的"顺序依赖"子维度**: champion 的多尺度融合把所有尺度的权重
    从同一输入 [point, global_mean] 并行算出, 各尺度权重互不知晓其他尺度已注入的内容。
    顺序 readback (先粗后细, 细尺度权重看到粗尺度注入后的特征) 是 CTF 指向的
    readback/融合机制里唯一未被探的信息流依赖。M61-SCT 是精确探针。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  ### M61-SCT (Sequential Coarse-then-Fine Context Readback)
  - 填补缺口 (d): 两阶段 readback — 阶段1 注入最粗尺度 (8簇) context 更新 inst_feats;
    阶段2 融合 fine+medium 尺度, 融合权重基于"粗注入后的"点特征计算。
    细尺度权重由此条件于粗尺度已注入的 context → 粗→细 顺序依赖 (coarse-to-fine refinement)。
  - 结构: stage1_gate Linear(2C→1) + stage2_gate Linear(2C→2), ~1.5K 新参数,
    但产生新的信息流依赖 (阶段2 gate 输入 = 阶段1 输出), 非单算子加法。
  - 因果: "并行融合时, 细尺度权重无法对粗尺度已注入的 context 作出反应 — 若某点所在
    粗簇被污染 (跨物体), 即使细 token 干净也会被拖低。顺序 readback 让细尺度看到粗注入
    后的特征, 恰在粗注入把点特征推向错误语义时提高细尺度权重。"
  - 预期: >0.5012 → 顺序依赖是融合机制瓶颈的一环; ≈0.5012 → 融合机制轴进一步闭合
    (与 SCF/XCA/CSF 一起排除该方向)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260804-180842.md
================================================================================
