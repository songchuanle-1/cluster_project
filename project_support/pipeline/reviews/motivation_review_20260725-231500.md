================================================================================
  Motivation Review — cluster_project
  2026-07-25 23:15:00
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100 | Champion: model_base1_quard2_c2f_enc_lite_posA_l1 0.5012 | Gap: +0.0088
  - Description: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度
  - 注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位精度 | confirmed | A1-A0 = +0.0118 (0.5012 vs 0.4894) | 需要确认 context 质量提升机制 |
  | 正交 cluster tokens 提升 context 多样性 | promising | M17-ORT = 0.5005, γ=+0.0111 vs baseline | 需要验证与其他机制的协同 |
  | detail message 提供互补信号 | promising | D1-detail = 0.5003 (stopped_unknown) | 需要稳定复现 + 组合验证 |
  | context+detail hybrid 组合 | testing | M21-HYB = 0.4898@ep18 (running) | 待收敛判定 |
  | cross-scale cluster attention | partial | M22-XCA = 0.4954, γ=+0.0060 | 单独收益有限，需组合 |
  | refine 迭代机制 | testing | M25-REF waiting, C3-refine = 0.4931 | 待 M25 验证新实现 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | 直接验证多尺度 context 注入 | 确认核心假设 ✓ |
  | M17-ORT | 0.5005 | ORT 提升 cluster token 多样性→context 质量 | 验证 orthogonality 有效 ✓ |
  | D1-detail | 0.5003 | detail=偏差信号作为互补 context | 接近 champion，互补信号有效 |
  | M22-XCA | 0.4954 | cross-scale 交互提供额外信息通路 | 有效但不足，需组合 |
  | M20-DET | 0.4955 | detail 干净复现 | 低于 D1 首次运行(0.5003)，复现性问题 |
  | E4-res_detail | 0.4944 | residual+detail 组合 | 无协同，residual 上限固定 |
  | A4-shuffle | 0.4941 | shuffle 对照验证内容路由 | 证实 routing 内容信号弱 |
  | M1-QGC | 0.4939 | query-gated context | 不如 ORT/detail |
  | M18-S2FM | 0.4933 | 2-scale fine+medium | 3-scale > 2-scale，多尺度必要 |
  | C3-refine | 0.4931 | 迭代 refine | 低于 champion，单次 context 充分 |
  | M16-CSR | 0.4875 | cluster self-refine | 低于 baseline 附近 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: 多尺度 context 注入有效 (+0.0118), ORT 正交化接近 champion (0.5005)
  - 未验证: 
    1. ORT + HYB 组合是否协同？ORT 让 cluster tokens 更多样 + HYB 让 context/detail 互补 → 预期 > champion
    2. ORT + detail 组合效果 (M24-ORT-D 已入队，等待中)
    3. M21-HYB 最终收敛值 (running，当前 0.4898 偏低)
  - 矛盾/疑问: 
    1. D1-detail 首次=0.5003 vs M20-DET=0.4955 — detail 复现不稳定
    2. M21-HYB 0.4898 偏低 — hybrid 可能不如单独的 context 或 detail？

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - **M26-ORT-HYB**: 填补"ORT + HYB 协同"缺口。ORT(0.5005) 让 cluster tokens 正交多样 + HYB(context+detail) 互补信号 → 预期协同超越 champion 0.5012
  - 验证的假设: (a) 正交化 cluster tokens 使 context 和 detail 信号都受益; (b) HYB 的 context+detail 在正交化后不会互相干扰
  - 预期: > 0.5012 (champion), 理想 > 0.5050
  - 约束校验: ✓ FLOPs 增量可忽略 (ORT 仅 loss term, HYB 已轻量); ✓ 非 gate/routing/residual; ✓ 不涉及 N² attention; ✓ epochs=50 不变
  - 此变体直接服务于 motivation: "多尺度 cluster context 机制提升定位精度" — 正交化+互补信号 = 更高质量的 context

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260725-231500.md
================================================================================
