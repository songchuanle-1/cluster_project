================================================================================
  Motivation Review — cluster_project
  2026-08-05 12:08:03
================================================================================

## 1. Goal
  - goal.json description: cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云
    特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类
    路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51。
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 (DRP) 0.5012 | Gap: +0.0088 | Phase 1 (NOT YET)
  - check_goal: PHASE1_NOT_REACHED → 继续 Phase 1 自主设计

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (A1−A0≥0.005) | confirmed | DRP 0.5012 vs base 0.4894 (γ=+0.0118) | **是否真正"多尺度"存疑 (见§4) |
  | routing 生效反降点 | confirmed(证伪) | TrueRoute 0.4468 vs DRP 0.5012 | — |
  | readback expressiveness 非瓶颈 | confirmed | BIL/NLR/FILM/FLM/DGC 全 < champion | 轴闭合 |
  | 聚合 = mean 最优 | partial | max/weighted/dual(DCA) 全 < mean; CCR/VAC/SAC 在跑 | 等待聚合轴收束 |
  | 融合权重形式非瓶颈 | confirmed(本 tick) | SWI 0.4970 / CSF 0.4958 / SCF 0.4927 全 < champion | 轴闭合 |
  | token 多样性(正交)有帮助 | 未验证(bug 污染) | M17-ORT 梯度断流; M62-ORTG 已入队 | 重测中 |
  | message 构造轴 | closing | 绝对(DRP 0.5012)/残差融合后(D1 0.5003)/残差逐尺度(PSR 入队) | 待 PSR 收束 |
  | 投影放置轴 | testing | 共享 post-fusion(DRP) vs 逐尺度 pre-fusion(SSP 入队) | 待收束 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | DRP (champion) | 0.5012 | 直接验证 context 回写 | 确认核心假设, 但准单尺度(见§4) |
  | M55-SCF (本 tick 终态) | 0.4927 | 内容自适应融合权重 | 失败 → 融合机制轴收束 |
  | D1-detail | 0.5003 | 融合后单残差 message | 残差方向有效但 < 绝对 |
  | M45-NCR | 0.4980 | soft readback | 有效但 < hard-gather |
  | M41-CTF | 0.4995 | token FFN | token 质量非瓶颈 |
  | M51-DCA | 0.4893 | dual pooling | mean 聚合仍最优 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效、routing 有害、readback expressiveness 非瓶颈、token 质量
    非瓶颈、mean 聚合最优、融合权重形式非瓶颈 (本 tick 收束)。
  - **代码审读发现核心缺陷 (本 tick)**: `_cluster_to_points` 的粗尺度 gather 长度错配。
    `cluster_ids_list[lvl]` 对 lvl=0 存"点→簇"映射 (长度 N_b), 对 lvl>0 存"父级 token→簇"
    映射 (长度 K_{lvl-1} = 256/64)。原实现 `msg[b, :n_valid] = cf[b, ids_b]` 把粗尺度
    token 写到前 K_{lvl-1} 个**点**槽 → 索引 > K_{lvl-1} 的绝大多数点收到零中/粗尺度
    context。docstring 声称"每级每个点的 cluster id", 意图 vs 实现不符 (lvl0 正确, lvl>0 错误)。
    ⇒ **champion 的 0.5012 实际是准单尺度 (仅细 256 簇) 回写**。56 个变体全部继承此缺陷。
  - 未验证 (故事核心声称的真正检验): 若用逐级组合 点→lvl0→lvl1→lvl2 正确地把每个点的
    完整多尺度 cluster context 送达, 多尺度是否贡献超过准单尺度? 这是对 "多尺度 context
    有效" 这一核心假设的**决定性补测** — 此前所有"多尺度"变体都在残缺交付下测试。
  - 该缺陷与在队列所有变体 (M58-M64) 正交: 它们改 message 内容/融合/投影, 但都继承同一
    粗尺度 gather 缺陷。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M65-HCG (Hierarchical Composition Gather): 逐级组合 点→lvl0→lvl1→lvl2 簇映射,
    让每个点收到自己真正的多尺度 cluster context, 复用 champion 的 level_gate 融合。
    - 填补缺口: "多尺度 context 的正确交付" — 故事的根基声称。
    - 变体角色: 验证假设 "champion 的增益是准单尺度驱动的; 正确的多尺度 context
      能否超过 0.5012"。
    - 对照基线: DRP champion 0.5012。HCG > 0.5012 → 粗尺度 context 是隐藏收益, 破 ceiling;
      ≈0.5012 → 多尺度 claim 实为单尺度 claim, 故事需修正 (增益来自细尺度 256 簇);
      < 0.5012 → 粗尺度 context 对多数点是噪声。
    - 与在队列变体正交: PSR/SSP/SCF/SCT 均继承同一 gather 缺陷, HCG 是独立的结构修复探针。
  - 无新增超参, 参数数与 champion 相同 (仅改 gather 信息流), 纯结构性变更。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260805-120803.md (M65-HCG 单变体)
================================================================================
