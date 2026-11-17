================================================================================
  Motivation Review — cluster_project
  2026-08-04 04:03:29
================================================================================

## 1. Goal
  - Target: mIoU >= 0.5100 | Champion: posA_l1 (DRP) 0.5012 | Gap: +0.0088 | Phase: 1 (NOT YET)
  - goal.json description: cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被
    证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51。
  - Phase 0.5 活跃保留检查: goal.json constraints[] 无"活跃保留"字样条款; decisions/_index.md
    最近 10 条全为 skip_design/queue_push (无 route_change/question) → 双源无保留, 自主设计允许。
  - check_goal.py: Phase 1 NOT YET (champion=0.5012, target=0.5100, gap=+0.0088)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位 | confirmed | champion 0.5012 vs baseline 0.4894 (γ=+0.0118) | 距 target +0.0088 |
  | C2F routing 贡献 | refuted | DRP(无routing)=0.5012=champion; A3 true_route=0.4468 有害 | — |
  | 读回形式 (additive) 最优 | closing | BIL(0.4919)/NLR(0.4948)/FILM(0.4936)/FLM(0.4865) 全 < champion | M50-DGC 待验 |
  | 聚合池化 mean 最优 | partial | max(0.4910)/weighted(0.4890) 差于 mean; dual=M51-DCA 在跑 | var 从未测 |
  | 级联聚合噪声 | untested | — | M52-CCR 待验 |
  | 尺度数 | closed | M18[256,64]=0.4933, M19[256,8]=0.4944 均 < 3-scale 0.5012 | 三尺度均有贡献 |
  | 组合 (ORT+detail 等) | refuted | M24-ORT-D=0.4955, M26-ORT-HYB=0.4998, E4=0.4944 | — |
  | **cluster token 表示富化 (dispersion/spatial)** | **untested** | token 仅 mean 特征聚合, 无二阶统计/显式空间信号 | M53-VAC + M54-SAC 本次补齐 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion/DRP | 0.5012 | 多尺度 context 回写 | 核心假设确认 ✓ |
  | M17-ORT | 0.5005 | token 正交正则 | token 多样性帮助但非瓶颈 |
  | M48-BIL | 0.4919 | 双线性读回 | 读回非线性无益 ✗ |
  | M49-NLR | 0.4948 | 非线性读回 | 读回非线性无益 ✗ |
  | M51-DCA | running | dual(mean+max) 聚合 | 聚合信息量维度 |
  | M52-CCR | waiting | 级联精炼 | 级联噪声维度 |
  | M18-S2FM | 0.4933 | 2-scale [256,64] | 尺度消融: 三尺度均有贡献 |
  | M19-S2FC | 0.4944 | 2-scale [256,8] | 尺度消融: 三尺度均有贡献 |

  关键规律 (30+ 变体): 读回形式/融合/选择/交互/调制/尺度数/组合全部收敛 ≤ 0.5012。
  **cluster token 表示本身 (纯 mean 特征聚合) 是最后未探明的结构维度** — token 只携带
  分布中心 (mean), 不携带簇内离散度 (variance) 与显式空间位置 (coordinates)。

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回读有效 (+0.0118); routing 无用; 读回形式/融合/选择/交互/调制/尺度数
    均非瓶颈; 组合 (ORT+detail 等) 无协同。
  - 未验证:
    (a) **簇内离散度 (variance)** — mean 池化丢弃二阶统计; 高离散簇的 mean token 不可靠,
        但 readback 无从得知 → **M53-VAC**
    (b) **显式空间信号** — cluster token 特征无空间编码; 引用表达多含空间关系 (next to/above),
        token 无法显式表示 → **M54-SAC**
  - 矛盾: 30+ 变体 ≤ 0.5012, 但没有任何变体动过"cluster token 表示由什么组成"。
    token 是纯特征均值, 表示容量受限可能是天花板根源。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  ### M53-VAC (Variance-Augmented Cluster Context)
  - 填补缺口 (a): cluster token 携带 mean + variance 两个统计量 (concat 后投影)。
    variance=簇内特征离散度, 表示"该簇上下文有多可靠"。高离散簇 (边界混合) 的 context
    应该被折扣; 低离散簇 (语义一致) 的 context 可靠。token 携带离散度后, 下游 readback/
    attention 可以隐式利用它。
  - 结构: 新的二阶统计聚合路径 (scatter_mean(feat) + scatter_mean(feat²)-mean² → concat → MLP)。
    与 M51-DCA (mean+max=显著信号) 正交: max 捕捉极端值, variance 捕捉整体离散度。
  - 因果: mean 池化只保留簇内分布中心; 对高离散簇, mean 是劣质代表。显式携带离散度使
    cluster token 能表达"这个簇的上下文置信度", 提升边界点定位。
  - 预期: >0.5012 → 离散度信息是瓶颈; ≈0.5012 → 二阶统计不影响。

  ### M54-SAC (Spatial-Aware Cluster Context)
  - 填补缺口 (b): 聚合前将每点坐标通过小型 MLP (3→d) 编码为空间嵌入, 加到 inst_feats 上,
    使 cluster token 携带显式空间信号。当前 cluster token 仅由特征均值组成, 无坐标信息
    (分区用了坐标, 但 token 特征没有)。
  - 结构: 新的空间嵌入路径 (Linear(3,64)+ReLU+Linear(64,256) → 加到聚合输入)。
    与 posA/posB/posC (encoder 顺序) 不同, 这是给 cluster 聚合输入加显式空间编码。
  - 因果: 引用表达常引用空间关系 ("桌子旁边的椅子"); 无空间信号的 cluster token 无法
    显式表示空间布局; 空间嵌入使 coarse cluster token 能表达"场景的哪个区域",
    直接服务于定位。
  - 预期: >0.5012 → 空间信号是瓶颈; ≈0.5012 → 空间信息已由 backbone 隐式携带。

  两者均直接服务"cluster token 表示富化"这一最后未探明维度, 与 running 批次
  (M50-DGC 读回 / M51-DCA 聚合 / M52-CCR 级联) 正交。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260804-040301.md
================================================================================
