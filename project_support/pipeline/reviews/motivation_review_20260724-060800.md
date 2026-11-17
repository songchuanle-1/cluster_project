================================================================================
  Motivation Review — cluster_project
  2026-07-24 06:08:00
================================================================================

## 1. Goal
  - pipeline/goal.json: cluster 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度
  - Target: mIoU ≥ 0.51 | Champion: posA_l1 0.5012 | Gap: +0.0088
  - Phase 1: NOT YET

## 2. Story Status
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | context 已达上限? |
  | routing 有害 | confirmed | true_route 0.4468 (γ=-0.0544) | — |
  | detail message 有效 | confirmed | D1-detail 0.5003 (γ=+0.0109) | 与 context 协同待验证 |
  | orthogonality regularization 有效 | confirmed | M17-ORT 0.5005 (γ=+0.0111) | 与其他机制组合待验证 |
  | hybrid message 有效 | testing | M21-HYB running | 待结果 |
  | cross-scale cluster attn 有效 | queued | M22-XCA waiting | — |
  | max-pool aggregation 有效 | queued | M23-CMX waiting | — |

## 3. Experiment Assessment
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | context-only baseline | 核心验证 context 有效 ✓ |
  | M17-ORT | 0.5005 | orthogonality → diverse cluster bank | context 质量可提升 ✓ |
  | D1-detail | 0.5003 | fine-grained message type | 替代 context 路径 ✓ |
  | M18-S2FM | 0.4933 | 2-scale ablation [256,64] | coarse scale 必要, medium 更重要 |
  | M19-S2FC | 0.4944 | 2-scale ablation [256,8] | fine scale 关键, coarse 辅助 |
  | M16-CSR | 0.4875 | cluster self-refine | 自优化路径失败 |
  | M1-QGC | 0.4939 | query-gated context | gate 机制无增益 |
  | A4-shuffle | 0.4941 | random routing control | 证实 routing 无内容依赖 |

## 4. Gap Analysis (Q1: 故事缺什么)
  - 已验证: context 有效, detail 有效, ORT 有效, routing 无效
  - 未验证: ORT+detail 组合能否超越 champion? context+detail hybrid 是否优于单独?
  - 矛盾/疑问: ORT(0.5005) 和 detail(0.5003) 各自接近 champion, 但都是单独使用 context/detail messages. 两者的机制互补(ORT→cluster diversity, detail→message granularity), 组合可能超 champion.

## 5. Design Rationale (Q2+Q3: 为什么设计这批变体)
  - M24-ORT-D: ORT + detail message_type. 填补"ORT 的正交正则化 + detail 的细粒度消息能否协同"缺口. 预期: ORT(context)=0.5005 + detail message → 0.503+, 可能超越 champion.
  - 故事线推进: 若 ORT+detail > 0.5012, 证明"正交 cluster bank + 细粒度消息"的协同有效→ 论文 story 从 single-mechanism 升级为 mechanism combination.

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260724-060800.md
================================================================================
