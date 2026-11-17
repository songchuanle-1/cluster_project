================================================================================
  Motivation Review — cluster_project
  2026-08-04 21:15:00
================================================================================

## 1. Goal
  - goal.json description: cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云
    特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类
    路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51。
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 (DRP) 0.5012 | Gap: +0.0088 | Phase 1 (NOT YET)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | DRP 0.5012 vs base 0.4894 (γ=+0.0118) | 需消融哪些设计必要 |
  | routing 生效反降点 | confirmed(证伪原假设) | TrueRoute 0.4468 vs DRP 0.5012 | — |
  | readback expressiveness 不是瓶颈 | confirmed | BIL 0.4919 / NLR 0.4948 / FILM 0.4936 / FLM 0.4865 全 < champion | — |
  | token 质量不是瓶颈 | confirmed | CTF 0.4995 → 结论指向 readback/融合机制 | — |
  | token 多样性(正交正则)有帮助 | 未验证(被 bug 污染) | M17-ORT 0.5005 因 ORT 梯度断流无效; M62-ORTG 已入队 | M62 重测 |
  | 融合机制顺序依赖(粗→细) | 待测 | M61-SCT 已入队 waiting | running 队列消化中 |
  | 内容自适应尺度融合 | 待测 | M55-SCF running (1/50) | running 队列消化中 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | DRP (champion) | 0.5012 | 直接验证 context 回写 | 确认核心假设 ✓ |
  | D1-detail | 0.5003 | 点-簇归一化残差 message | 接近 champion, 但 < 0.5012 |
  | M17-ORT | 0.5005 | 验证 token 正交正则 | **无效**: orth 梯度断流, 假说未验证 |
  | M50-DGC | 0.4913 (dead) | diff-gated context | 失败, 进程死亡 (deathwatch 2/3) |
  | M51-DCA | 0.4893 (running) | dual pooling | running, no_impr 9/10 近早停 |
  | M52/M53/M54 | running ep1 | CCR/VAC/SAC | 刚启动, 无数据 |
  | M55-SCF | running ep1 | per-point 内容融合 | 刚启动 (gpu0), 无数据 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效、routing 有害、readback expressiveness 非瓶颈、token 质量非瓶颈。
  - 未验证: token 多样性 (M62-ORTG 已入队)、融合顺序依赖 (M61-SCT 已入队)、内容自适应融合
    (M55-SCF running)、聚合质量 (M51-53/54 running)、detail 组合 (M58/59/60 已入队)。
  - 队列缺口: 以上全部已覆盖, 但队列深度 5 < 可用槽 5+1=6, 需补 1。
  - 尚未消融的 message 构造: 所有 message 变体均在"融合后"做残差 (detail) 或在"融合前"
    用绝对 cluster token (context)。**从未在融合前逐尺度计算 point-cluster 残差** —
    即 per-scale deviation: 每尺度 message = point_feats − cluster_token_l (归一化), 再融合。
    这是 D1-detail (单融合残差) 与 champion (绝对 token) 之间的结构空白。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M63-PSR (Per-Scale Residual readback): 逐尺度计算 点−簇token 残差 → 融合。
    - 填补缺口: D1-detail 证明 "点-簇归一化残差 message" 有效 (0.5003), 但只在多尺度融合后
      取一次残差, 丢失了"该点相对各尺度簇的偏差"的尺度分解信息。PSR 在融合前逐尺度取残差,
      让每个尺度的 message 变成该点相对该尺度簇 token 的偏差信号, 由 per-point gate 融合。
    - 变体角色: 验证假设 "readback 注入的应是'点相对簇的偏差'而非'簇的绝对表示' —
      边界点/离群点相对细簇偏差大, 融合后单残差会稀释这个信号, 逐尺度残差保留它"。
    - 对照基线: DRP champion 0.5012。PSR > 0.5012 → deviation 假说有效; ≈ 0.5012 → 偏差
      信号无独立增益, 排除该 message 构造方向。
    - 预期推进: 无论结果, "readback message 构造" 轴的 context(绝对)/detail(融合后残差)/
      PSR(逐尺度残差) 三态闭合, 故事线的 readback 机制证据链完整。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260804-212409.md (M63-PSR 单变体)
================================================================================
