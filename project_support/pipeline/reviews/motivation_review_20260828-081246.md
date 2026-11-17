================================================================================
  Motivation Review — cluster_project
  2026-08-28 08:12:46
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-28 08:07:55: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 近 24h 无 type=question;
    最近 10 条 decisions 为 queue_push/early_stop/skip_design, 无保留型 route_change
    /question → 自主设计允许 (Phase 0.5 双闸门通过)
  - 触发原因: M122 推送后 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7 max=2
    = 4 槽位, 阈值 5) → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012 | 关闭 |
  | cluster token 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C/CSF/FLM/pool/TrueRoute | 关闭 |
  | 通路组合叠加 (delivery×delivery) | 关闭 | M125/M126/M134/M136/M138/M139 6次不叠加 | 关闭 |
  | 多层注入 (HCG@2) | 证伪 | M96-CTF-HCG-2LAY=0.4940 | HCG@2 有害 |
  | legacy 2层注入 (MLay) | 有效 | M86-MLAY=0.5010 (γ=+0.0116) | 与 CSORT 组合 M147 在队 |
  | 判别性 loss (CLICA) | 饱和 | M140=0.4970 < base 0.5012 | 判别轴无增益 |
  | 跨尺度一致 loss (CSIC) | 饱和 | M141=0.4960 (本 tick 终态) | 一致轴无增益 |
  | loss 监督轴整体 | 2连败 | CLICA/CSIC 均 < 父模型 | M142/M143/M144 检验中 |
  | CSORT 应用位置 (token vs message) | 非关键 | M109-CSORT-MSG=0.5010 ≈ M95 | 位置轴关闭 |
  | CSORT (cross-scale orth) | champion | M95=0.5020 (唯一破 0.5012 平台) | 跨 seed 脆弱 (mean~0.495) |
  | DCM (decoder qla memory read) | 有效 | M124-CTF-HCG-DCM=0.5010 | **×CSORT 未测 (本设计 M148)** |
  | CSORT × detail 组合 | 在队 | M146 queued | 去相关×残差回写 |
  | CSORT × MLay legacy@2 组合 | 在队 | M147 queued | 去相关×2层注入 |
  | CSORT 全尺度对 | 在队 | M145 queued | 扩展 champion 机制 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 跨尺度 orth 破平台 | 唯一破 0.5012 机制 (seed 脆弱) |
  | M124-CTF-HCG-DCM | 0.5010 | decoder 直接读 cluster tokens 绕过 writeback 瓶颈 | 独立有效交付机制, ×CSORT 未测 |
  | M86-MLAY (legacy 2层) | 0.5010 | 2层注入有效 | 结构深度轴独立有效 |
  | M119-CTF-HCG-MFP | 0.5020 | 与 champion 持平 | 3-seed 证伪 (s42=0.4869/s123=0.4960), 轴关闭 |
  | D1-detail (message_type=detail) | 0.5003 | 残差回写 message | detail 单独有效 |
  | M140-CLICA | 0.4970 | 判别性 loss | 判别轴饱和 |
  | M141-CSIC (本 tick 终态) | 0.4960 | 跨尺度一致 loss | 一致轴饱和, loss 轴 2 连败 |
  | M109-CSORT-MSG | 0.5010 | CSORT 位置非关键 | 位置轴关闭 |
  | M139-MLAY-DUAL-LEGACY | 0.4880 | 组合轴天花板格 | 组合轴第 6 次确认不叠加 (delivery×delivery) |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; 结构变换全灭; delivery×delivery 组合 6 次不叠加;
    HCG@2 有害但 legacy@2 有效; loss 监督轴 (CLICA/CSIC) 2 连败; CSORT 位置非关键;
    DCM/MLay/detail 是仅剩的独立有效 top 机制。
  - 未验证: **champion CSORT 与 DCM (decoder qla memory read) 是否叠加**。CSORT 在
    cluster token 形成侧做跨尺度去相关 (正则化, 提升各尺度信息互补度); DCM 在
    decoder 侧新增 qla KV 记忆通路, 让 decoder query 直接读多尺度 cluster tokens,
    绕过 writeback 单通道有损瓶颈。两者位点不同 (token 形成 vs decoder 读取),
    信息流不重叠, 从未组合。
  - 与在队 M146 的关系: M146 测 CSORT×detail (message 构造轴, 0.5003); DCM 是
    decoder 读取轴 (0.5010), 是独立有效机制中更强的 delivery 通道。M146 与 M148
    一起构成 CSORT×delivery 网格 {message_type, decoder-read} 两格。
  - 矛盾/疑问: 组合轴已 6 次失败 (delivery×delivery 同类); CSORT×DCM 是
    {正则化 loss}×{delivery 通路} 跨类组合, 与失败组合不属同类 (CSORT×detail 亦然)。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M148-CTF-HCG-CSORT-DCM: champion 包 (cluster_mode='ctf_hcg_csort',
    csort_weight=0.01) 基础上加入 use_cluster_mem=True (DCM decoder qla memory read,
    从 M124 已验证实现移植), 其余完全一致, seed 1999。
  - 因果假设: CSORT 使各尺度 cluster tokens 去相关 → 每尺度携带互补 context;
    DCM 让 decoder query 直接读这组互补的多尺度 tokens (绕过 writeback 单通道
    有损瓶颈) → decoder 获得更富的信息容量 → 定位更准 → 破 0.5020。
    一句话: "去相关的多尺度 context 经 decoder 直读通路 → 绕过 writeback 瓶颈
    → 信息容量最大 → 定位更准"。
  - 与 banned[]/constraints 校验:
    - 非 gate系/语言路由系/attnpool/residual 系; 非 true_route; 非 3/4/6 层重复注入
      (cluster_att_num_layers=1 不变, 非层数变更)。
    - 非调参: csort_weight=0.01 沿用 champion; use_cluster_mem=True 沿用 M124 已验证
      值; 无新数值配置; 新增 qla KV 记忆通路是结构性机制变更 (新计算图/新信息路径),
      符合 Phase 1 结构性机制变更要求。种子 1999 结构首筛。
    - FLOPs/显存: DCM 仅 concat cluster tokens 到 lang_mem 的 qla 注意力 (M124 已实测
      ≤10G), csort loss 仅 (8×64+64×256) 对级 abs-cosine → 约束满足。
    - 与"分支停止: 提升<0.002"约束: 若 M148 增益 <0.002 → CSORT×DCM 格关闭,
      作为 CSORT×delivery 网格第二点 (与 M146 一起) 的边界证据。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260828-081246.md
================================================================================
