================================================================================
  Motivation Review — cluster_project
  2026-07-22 08:03:01
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100
  - Champion: model_base1_quard2_c2f_enc_lite_posA_l1, mIoU=0.5012
  - Gap: +0.0088
  - Phase: 1 (NOT YET)
  - Motivation: "多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度"

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 提升定位精度 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | 哪些尺度必要?(M18/M19消融中) |
  | 内容路由提升 context 质量 | refuted | A3-true_route 0.4468; A4-shuffle 0.4941 证实路由有害 | — |
  | detail message 独立有效 | confirmed | D1-detail 0.5003 (relaunch), γ=+0.0109 | 需clean rerun确认 (M20-DET waiting) |
  | refine 机制增强 context | refuted | C3-refine 0.4931; M16-CSR 0.4875(8/10→early) | — |
  | residual 机制有效 | refuted | B5-residual 0.4944; E4-res+detail 0.4944 | — |
  | gate 机制 (QGC/QSF) 有用 | refuted | M1-QGC 0.4939; M6-QSF 0.4866 | — |
  | 正交正则化促进 token 多样性 | untested | M17-ORT crashed, fix pending | 需重跑 |
  | context+detail 互补 | untested | context=0.5012, detail=0.5003 — 两者都强但独立 | M21-HYB 本次入队 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion (posA_l1, context) | 0.5012 | 核心验证: 多尺度 context 有效 | 确认核心假设 ✓ |
  | D1-detail (relaunch) | 0.5003 | detail message 独立验证 | 确认 detail 几乎等同 context ✓ |
  | M1-QGC | 0.4939 | query-gated context | 证伪 query gate 路线 ✗ |
  | M6-QSF | 0.4866 | query-selective fusion | 证伪 query 进融合 gate ✗ |
  | A4-shuffle | 0.4941 | routing 控制组 | 证伪 routing 路线 ✗ |
  | C3-refine | 0.4931 | refine 消融 | 证伪 refine ✗ |
  | M16-CSR | 0.4875* | cluster self-refine | 证伪 token self-attn refine ✗ |
  | M18-S2FM | running | 2-scale 消融 (drop coarse) | 尺度必要性验证 ⟳ |
  | M19-S2FC | waiting | 2-scale 消融 (drop medium) | 尺度必要性验证 ⟳ |
  | M20-DET | waiting | detail clean rerun | 确认 detail 可复现 ⟳ |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: 多尺度 context 工作机制有效 (0.5012), detail 变体几乎等同
  - 未验证: (1) context 和 detail 是否提供互补信号? (2) 尺度必要性 (M18/M19 正在验证)
  - 矛盾/疑问: 为何多种 refine-like 机制全部失败? 是否 cluster token 已足够好, 进一步处理有害?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M21-HYB (hybrid context+detail)**: context 和 detail 各自 close to champion,
    但机制不同 — context 提供 "cluster 认为应该是什么", detail 提供 "偏离 cluster 期望的细节".
    如果两者之和 >0.5012, 说明它们互补 → 故事线增加 "多信号融合" 维度.
    如果 <0.5012, 说明一种信号占主导 → 故事线收敛到单信号.

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260722-080301.md
================================================================================
