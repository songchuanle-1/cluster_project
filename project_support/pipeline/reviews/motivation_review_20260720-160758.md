================================================================================
  Motivation Review — cluster_project
  2026-07-20 16:07:58
================================================================================

## 1. Goal
  Target mIoU ≥ 0.51, champion 0.5012 (posA_l1, context-only), gap −0.0088.
  机制: 多尺度 cluster context (routing 已证伪). context✓(A1−A0=+0.0118).

## 2. Story Status
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | H1 多尺度context是主要收益 | confirmed | A1=0.5012, routing丢弃仍最优 | — |
  | H3 routing独立贡献有限 | confirmed | A3=0.4468<A1, routing反害 | A4-shuffle控制组(running) |
  | H4 detail-preserving update | confirmed | D1-detail=0.5003≈champion, γ=-0.0009 | 在detail上叠加机制 |
  | H5 query信息能否提升context | running | M1-QGC(just started) | 等M1结果 |
  | H6 尺度融合query-aware | waiting | M6-QSF(waiting) | 等M6结果 |
  | H7 cluster token质量是否瓶颈 | waiting | M16-CSR(waiting) | 等M16结果 |
  | H8 residual机制上限 | confirmed(失败) | E4=0.4944=B5, 组合无协同 | 正式归档banned |

## 3. Experiment Assessment
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion(Lite) | 0.5012 | 核心: 多尺度context回写 | 锚点, 所有变体对标 |
  | D1-detail | 0.5003 | detail聚合≈context效果 | 第二条有效机制✓ |
  | E4-res+detail | 0.4944 | residual+detail无协同 | 排除residual路线✗ |
  | A4-shuffle | running(0.3900@ep4) | routing控制组 | 定论routing有害原因 |
  | M1-QGC | running(just started) | query-gated context | 验证query能否提升 |
  | M6-QSF | waiting | query-aware尺度融合 | 互补M1(不同注入位置) |
  | M16-CSR | waiting | cluster token精炼 | 验证token质量瓶颈 |

## 4. Gap Analysis (Q1: 故事缺什么)
  - 已验证: context✓, routing✗, detail≈context, residual✗
  - 正在验证: query注入(M1), 尺度融合(M6), token精炼(M16), routing归因(A4)
  - 未验证(新缺口):
    (a) cluster token 多样性 — 当前所有变体假设token充分表达, 从未验证token是否冗余;
        如果多尺度 cluster bank 中同一尺度的token高度相似, context 质量受限
    (b) context 回写后的特征整合 — 当前直接用attention输出, 无后处理
    (c) 跨尺度信息流 — 粗/中/细三尺度token独立, 无显式交互

## 5. Design Rationale (Q2+Q3: 为什么设计这批变体)
  - M17-ORT (Cluster Orthogonality Regularization):
    填补: Gap(a) — cluster token 多样性
    机制: 对每尺度 cluster tokens 加 cos-sim orthogonality penalty,
          鼓励不同 token 捕获不同空间语义, 减少冗余
    预期: 更多样的 cluster tokens → 更丰富的 context → mIoU > 0.5012
    若成功: 证明 cluster token 冗余是当前性能瓶颈之一
    若失败: 排除 token 多样性问题, 转向 gap(b)/(c)
    与 constraints 校验:
    - FLOPs ≤ 10G: ✓ (仅矩阵乘法, ~0.01G FLOPs)
    - 显存 +15%: ✓ (无新参数, 仅额外loss计算)
    - 不改schedule: ✓ (仅加正则项)
    - 只更新inst_feats: ✓ (orth loss是额外loss, 不改forward flow)
    - 禁N² attention: ✓ (orth loss在cluster tokens上, K=8~256, 非N²)
    - banned: 无冲突(非gate/routing/attnpool/prune系)

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260720-160758.md
================================================================================
