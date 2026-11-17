================================================================================
  Motivation Review — cluster_project
  2026-07-27 16:10:00
================================================================================

## 1. Goal
  - pipeline/goal.json: cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51
  - Target: mIoU ≥ 0.5100 | Champion: 0.5012 | Gap: +0.0088

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 注入提升定位 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | 能否突破 0.5100? |
  | ORT 正则化有效 | confirmed | M17-ORT 0.5005 vs base 0.4894 (γ=+0.0111) | 权重 sweep (M27/M28 running) |
  | detail message 有效 | partial | D1 R2=0.5003 但波动大(0.4955-0.5003) | 稳定性不足 |
  | 机制组合有协同 | falsified | ORT+detail=0.4955, HYB=0.4898, residual+detail=0.4944 — 3/3失败 | 组合策略需要重新思考 |
  | refine 迭代改善 | falsified | M25-REF=0.4892 (< baseline), M16-CSR=0.4875 | 放弃 |
  | aggregation 变体 | partial | max-pool=0.4910 (失败), XCA=0.4954 (有效不足), DCA running | DCA 结果待定 |
  | C2F topk 过滤充分 | UNTESTED | 当前 [32,16,8] — fine scale 仅 12.5% 集群参与路由 | 是否 bottleneck? |
  | ORT weight 调优 | testing | M27(W5=0.05), M28(W1=0.001) | running/waiting |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion (posA_l1) | 0.5012 | 直接验证 context injection | 核心假设 confirmed ✓ |
  | M17-ORT | 0.5005 | ORT 提供多样性正则 | 平行机制, 距 champion 0.0007 |
  | D1-detail R2 | 0.5003 | detail message_type | 独立有效, 但波动大 |
  | M24-ORT-D | 0.4955 | ORT+detail 组合 | 组合失败 ✗ |
  | M22-XCA | 0.4954 | cross-scale attention | 有效不足 |
  | M21-HYB | 0.4898 | hybrid message | 组合失败 ✗ |
  | M25-REF | 0.4892 | iterative refine | 不及 baseline ✗ |
  | M23-CMX | 0.4910 | max-pool aggregation | mean > max |
  | A4-shuffle | 0.4941 | random routing control | 内容路由证伪 ✓ |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context injection (+0.0118), ORT 正则 (+0.0111), detail message (+0.0109)
  - 已验证失败: 机制组合(3/3), refine(2/2), routing(A3=0.4468), max-pool
  - 未验证: C2F topk 过滤是否过强? ORT weight 最优值? DCA dual-branch?
  - 核心缺口: **如何突破 0.5012 ceiling?** 所有独立有效机制都约在 0.500-0.501, 距 target 0.5100 差 0.0088, 需要结构性的新方向

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M30-ITK: 当前 C2F routing 在 fine scale 仅保留 32/256 (12.5%) 集群, medium scale 16/64 (25%)。这个 aggressive 过滤可能丢弃了有用 context。增加到 [64,32,8] 让更多集群参与 routing。Hypothesis: 更丰富的 context flow → > champion。
  - 如果结果 > 0.5012: context richness 是关键瓶颈, 可进一步探索更宽的 topk 或完全 dense routing
  - 如果结果 ≈ 0.5012: topk 过滤不是瓶颈, 需要找其他突破方向
  - 如果结果 < 0.5012: 当前 topk 值最优, 过滤 noise 是有益的

## 6. Next Batch
  → 见 pipeline/designs/exp_design_<ts>.md
================================================================================
