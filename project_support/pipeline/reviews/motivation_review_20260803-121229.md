================================================================================
  Motivation Review — cluster_project
  2026-08-03 12:12:29
================================================================================

## 1. Goal
  - Target: mIoU >= 0.5100 | Champion: posA_l1 0.5012 | Gap: +0.0088 | Phase: 1 (NOT YET)
  - goal.json description: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
  - Phase 0.5 活跃保留检查: goal.json constraints[] 无"活跃保留"条款; decisions/_index.md 最近 10 条无 route_change/question
    (全为 skip_design/queue_push/next_batch/terminal) → 双源无保留, 自主设计允许。

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位 | confirmed | champion 0.5012 vs baseline 0.4894 (γ=+0.0118) | 距 target 0.5100 差 +0.0088 |
  | C2F routing 贡献 | refuted | DRP(无 routing)=0.5012 = champion; A3 true_route=0.4468 有害 | — |
  | 读回形式(additive) 已达天花板 | partial | DRP/ORT/CTF/NCR 全部收敛 ~0.5012 | BIL/NLR/DGC 在测(ep2) |
  | 逐通道调制(FiLM/FLM) | refuted | M47-FILM=0.4936, M38-FLM=0.4865 | — |
  | cluster-token 交互(C2C/CSF) | refuted | M39-C2C=0.4865, M44-CSF=0.4958 | — |
  | 多簇 gather(NCR) | refuted | M45-NCR=0.4980 < champion | — |
  | 融合方式(softmax vs sigmoid) | refuted | M40-SWI=0.4970 < champion | — |
  | **cluster token 聚合质量 (aggregation)** | **untested (除 max/weighted 失败)** | mean(champion) > max(0.4910) > weighted(0.4890); **dual(mean+max) 从未跑过** | M51-DCA + M52-CCR 本次补齐 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion (posA_l1) | 0.5012 | 多尺度 context 回写 | 核心假设确认 ✓ |
  | M32-DRP | 0.5012 | 去 routing 死代码 | DRP 成为干净 baseline ✓ |
  | M17-ORT | 0.5005 | token 正交正则 | token 多样性有帮助但不破 ceiling |
  | M41-CTF | 0.4995 | token FFN 精炼(读回前) | token 质量可提升但非瓶颈 |
  | M45-NCR | 0.4980 | 多簇 top-K gather | 簇选择机制不优于 own-cluster |
  | M40-SWI | 0.4970 | sigmoid 尺度融合 | 融合竞争方式不重要 |
  | M44-CSF | 0.4958 | 跨尺度 token 交互 | 交互类无益 |
  | M47-FILM | 0.4936 | 逐通道 FiLM 调制 | 调制类死胡同 |
  | M23-CMX | 0.4910 | max 池化聚合 | 单 max 聚合差于 mean |
  | M42-WCA | 0.4890 | weighted 池化聚合 | learned-weight 聚合失败 |
  | M46-SHC | 0.4946 | split-head 读回 | 通道划分无益 |

  关键规律: 读回形式、融合方式、簇选择、token 交互、调制类全部收敛于或低于 0.5012。
  **聚合池化函数是消息内容维度最后一个未探明的结构方向** — mean 胜出但 dual(mean+max) 从未实验。

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回读有效; routing 无用; 读回形式/融合/选择/交互/调制均非瓶颈。
  - 未验证: 
    (a) 聚合池化是否丢失信息 — mean 只保留分布中心, 丢失簇内显著/离群信号 → **M51-DCA**
    (b) 级联聚合是否放大池化噪声 — 256→64→8 逐级 mean 会传播平滑误差 → **M52-CCR**
  - 矛盾: 所有 >0.5 变体都是"简单 additive readback + mean 池化"。0.5012 天花板可能源于
    消息内容本身(mean 池化丢失信息), 而非读回形式。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  ### M51-DCA (Dual-branch Cluster Aggregation)
  - 填补缺口: 聚合池化函数维度 (a)。mean 池化是分布中心, max 池化是显著信号。
    concat(mean, max)→MLP 让 cluster token 同时携带分布与显著信息。
  - 结构: 新聚合计算图(双分支池化+融合投影)。代码已在 SharedClusterBank(dual_proj) 中,
    config cluster_pool_type=dual 即可启用。这是 07-27 设计但从未入队的 M29 复活。
  - 因果: 边界/显著点特征被 mean 平均掉, 簇 token 无法表达"簇内最有辨识度的信号";
    显式保留 max 分支使 context 携带显著特征, 提升边界点定位。
  - 预期: >0.5012 → 聚合信息量是瓶颈; ≈0.5012 → 池化函数非瓶颈。

  ### M52-CCR (Cascade Cluster Refinement)
  - 填补缺口: 级联聚合质量 (b)。当前 256→64→8 级联中每层 raw mean 池化后直接进入下一层,
    mean 的平滑误差逐级放大。CCR 在每层池化后插入共享 pre-norm FFN 精炼 token,
    再送入下一层聚合。
  - 结构: 新计算图(池化后精炼路径)。与 M41-CTF(读回前精炼)位置不同 — CCR 在聚合管线内部,
    影响 coarse token 的构建, 而非仅最终消息。
  - 因果: 精炼后的 fine token 携带更清晰语义, coarse token 由精炼特征聚合, 减少噪声传播。
  - 预期: >0.5012 → 级联噪声是瓶颈; ≈0.5012 → 精炼位置不影响。

  两者均直接服务"cluster token 聚合质量是未探明方向"(M44/M47 分析结论), 与 running 批次
  (BIL/NLR/DGC 读回形式) 正交。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260803-121229.md
================================================================================
