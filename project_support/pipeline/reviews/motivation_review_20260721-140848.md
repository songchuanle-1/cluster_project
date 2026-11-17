================================================================================
  Motivation Review — cluster_project
  2026-07-21 14:15:00
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100
  - Champion: model_base1_quard2_c2f_enc_lite_posA_l1 — 0.5012
  - Gap: +0.0088
  - Phase: 1 (NOT YET)
  - Motivation: "multi-scale cluster context mechanism — cluster bank aggregates point cloud features → cluster_attn writes multi-scale context back to update inst_feats → improves localization accuracy"

## 2. Story Status
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | Multi-scale context improves localization | confirmed | A1−A0 = +0.0118 (champion 0.5012 vs baseline 0.4894) | 需要消融确认各尺度贡献 |
  | Routing is harmful | confirmed | A3=0.4468, A4-shuffle=0.4941 (正确路由 < 随机路由 < 无路由) | — |
  | Detail message ≈ context | confirmed | D1-detail 0.5003 ≈ champion 0.5012 | — |
  | Residual has ceiling at ~0.4944 | confirmed | B5=0.4944, E4=0.4944 | — |
  | Gate mechanisms (cag/cfe/layerscale) ineffective | confirmed | all < 0.4962 | — |
  | Query-conditioned fusion (QSF) | testing | M6-QSF running @ ep1 | pending |
  | Cluster self-refine (CSR) | testing | M16-CSR running @ ep1 | pending |
  | Token orthogonality (ORT) | queued | M17-ORT waiting | pending |
  | **All 3 scales are necessary?** | **untested** | — | **gap: no scale ablation** |

## 3. Experiment Assessment (动机视角)
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion (posA_l1) | 0.5012 | 直接验证 multi-scale context 回写 | 确认核心假设 ✓ |
  | D1-detail | 0.5003 | 验证 context 聚合方式 (均值 vs query加权) | detail≈mean, 均值够用 |
  | A4-shuffle | 0.4941 | 控制组: routing 有害定论 | 排除 routing, 聚焦 context |
  | M1-QGC | 0.4939 | query→cluster gate 无效 | query 信息注入不带来增益 |
  | B5-residual | 0.4944 | residual 注入有上限 | 排除 residual 方向 |
  | E4-res+detail | 0.4944 | residual+detail 无协同 | 确认 residual 方向关闭 |

## 4. Gap Analysis (Q1: 故事缺什么)
  - 已验证: context 回写有效, routing 有害, detail≈context
  - 未验证: 
    1. **多尺度必要性**: 是否所有 3 个尺度 (256/64/8) 都必要? 2 尺度是否足够?
    2. **尺度贡献分解**: coarse (K=8), medium (K=64), fine (K=256) 各自贡献多少?
    3. 跨尺度交互 (token 间 attention) — 待 M6/M16/M17 结果
  - 矛盾/疑问: 无

## 5. Design Rationale (Q2+Q3: 为什么设计这批变体)
  - **M18-S2FM** (2-scale fine+medium, drop coarse): 
    填补缺口 "coarse (K=8) 是否必要?"
    预期: 若 mIoU ≈ 0.5012 → coarse 不必要, "multi-scale" 精简为 bi-scale
         若 mIoU < 0.498 → coarse 有独特贡献, 保留 3-scale 设计
  - **M19-S2FC** (2-scale fine+coarse, drop medium):
    填补缺口 "medium (K=64) 是否必要?"  
    预期: 若 mIoU ≈ 0.5012 → medium 不必要, 256+8 足够
         若 mIoU < 0.495 → medium 是关键中间尺度
  - 故事线推进: 无论结果如何, 都明确了 "multi-scale" 中每个尺度的角色,
    为论文 ablation study 提供核心证据

## 6. Next Batch
  → 见 pipeline/designs/exp_design_${TS}.md
================================================================================
