================================================================================
  Motivation Review — cluster_project
  2026-08-05 17:10:51
================================================================================

## 1. Goal
  - goal.json description: cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被
    证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51。
  - Target: mIoU ≥ 0.5100 | Champion: model_base1_quard2_c2f_enc_lite_posA_l1_drp = 0.5012
  - Gap: +0.0088 | Phase: 1 (NOT YET) — check_goal.py 判定继续 Phase 1 自主设计
  - 硬约束 (constraints[]): FLOPs≤10G / 禁调参(Phase 1 只许结构机制变更) / 禁单变体改 schedule /
    分支停止(<0.002 且平台不升) / cluster 只更新 inst_feats / 默认仅最后 1 encoder 层注入 / 禁 N² attention
  - 禁区 (banned[]): gate系 / 语言路由系 / attnpool/qcond/agg/multi / prune / nomask 扩展 /
    3/4/6 层重复注入 / 大型 QKV/O 投影 / true_route / residual系 / Phase1 调参系

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed (但交付有 bug) | A1-DRP 0.5012 vs base 0.4894 (γ=+0.0118≥0.005 ✓) | 粗尺度 gather 长度错配, 中/粗尺度只送达前 K_{lvl-1} 点, 0.5012 实为准单尺度 → M65-HCG 验证正确交付 |
  | routing 生效 | falsified | A3-true_route 0.4468 (γ=-0.0544) | 已证伪, banned |
  | readback expressiveness (message 内容形式) | 轴闭合 | BIL 0.4919 / NLR 0.4948 / FILM 0.4936 / FLM 0.4865 / DGC 0.4913 全 < champion | 不再投入 |
  | 融合权重形式 | 轴闭合 | SWI 0.4970 / CSF 0.4958 / SCF 0.4927 (本 tick 终态) 全 < champion | 不再投入 (注意: 均于 broken 交付下测得) |
  | detail message (融合后残差) | 有效但 < champion | D1-detail 0.5003 (γ=+0.0109) | 未与正确多尺度交付组合 — M66 补格 |
  | token 质量非瓶颈 | partial | M41-CTF 0.4995 (token FFN 有效未破 ceiling) → 指向 readback/融合 | — |
  | token 多样性 (正交正则) | 污染待重测 | M17-ORT 0.5005 但 orth 梯度断流 (假说从未真验) | M62-ORTG 已入队重测 |
  | 聚合方式 | mean 最优 | M51-DCA 0.4893 (dual) / max / weighted 均 < mean | — |
  | 多尺度正确交付 | 未验证 (本 tick 最优先级) | champion 准单尺度 (bug) | M65-HCG 已入队 (P0) |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M55-SCF | 0.4927 | 内容自适应融合 (delivery broken) | 融合权重轴收束 ✓ (排除了该方向) |
  | M50-DGC | 0.4913 | diff-gated readback | expressiveness 轴闭合 ✓ |
  | M51-DCA | 0.4893 | dual pooling 聚合 | mean 聚合保持最优 ✓ |
  | M41-CTF | 0.4995 | token FFN 增强 | token 质量非瓶颈 ✓ (指向 readback/融合) |
  | M44-CSF/M47-FILM/M48-BIL/M49-NLR | 0.4958/0.4936/0.4919/0.4948 | 各 message 变体 | 均 < champion, 支撑 "残缺粗尺度交付下所有 message 变体受限于天花板" |
  | D1-detail | 0.5003 | 融合后单残差 message | detail 独立有效 (γ=+0.0109), 第二强机制 |
  | M17-ORT | 0.5005 | 正交正则 | 梯度断流 → 假说污染, M62-ORTG 重测 |
  | M32-DRP (champion) | 0.5012 | 绝对 token 逐尺度 gate 融合 | 核心机制, 但准单尺度 (bug) |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (γ=+0.0118); routing 证伪; expressiveness/融合/聚合三轴闭合;
    detail message 独立有效 (0.5003)。
  - 未验证 (结构空白):
    ① **正确多尺度交付** — 全部 56+ 变体 (含 champion) 均带粗尺度 gather 长度错配 bug,
       "多尺度 context" 故事的核心声称从未被正确检验 (M65-HCG 已入队, P0)。
    ② **{交付正确} × {message 类型} 的交互** — detail (0.5003) 与正确多尺度交付 (HCG)
       从未组合。M58 填 (broken, detail), M65 填 (correct, context), 缺 (correct, detail) 格。
  - 矛盾/疑问: 30+ 变体全 ≤ 0.5012, 且失败集中在 message/融合/投影 — 均在残缺交付下测得;
    需要正确交付下的数据才能判断这些轴是真闭合还是被 bug 遮蔽。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M66-DET-HCG (本次): {正确多尺度交付} × {detail 残差 message} 补格。
    - 填补缺口 ②: 若 HCG 正确交付使多尺度 context 更有信息, detail 的残差 (point − fused_msg)
      在正确 context 上计算 → 残差信号更准 → 可能叠加; 若 HCG 无益, 该格仍给出
      "detail 在正确 context 上是否仍有效" 的独立数据点。
    - 与队列内 M65-HCG (correct+context) 和 M58-DET-DRP (broken+detail) 构成完整 2×2,
      HCG 先跑 (FIFO), M66 的解读可直接利用 HCG 结果。
  - 预期结果对故事线推进:
    - M66 > 0.5012 → 两个有效机制可叠加 → 故事线扩展为 "正确多尺度交付 + 残差 message";
    - M66 ≈ M65 → detail 被正确多尺度 context 吸收 (正交被包含);
    - M66 < 0.5012 → 正确交付下残差 message 无益 → 排除该组合 (仍是证据链推进)。
  - 结论: 本次只设计 1 个变体 (队列深度 5→6), M66-DET-HCG 是成本最低、证据价值最高的补格。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260805-171051.md
================================================================================
