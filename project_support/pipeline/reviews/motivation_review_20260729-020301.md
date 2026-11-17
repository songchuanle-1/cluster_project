================================================================================
  Motivation Review — cluster_project
  2026-07-29 02:03:01
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 0.5012 | Gap: +0.0088
  - Description: cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
  - Phase 1: NOT YET (champion 0.5012 < target 0.5100)
  - Baseline: model_base1 = 0.4894

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 有效 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | context 最优注入方式未消融 |
  | routing 有害 | confirmed | A3 TrueRoute 0.4468 (γ=-0.0544) | DRP(running) 将最终确认 routing 是死代码 |
  | orthogonality 增强多样性 | confirmed | M17-ORT 0.5005 (γ=+0.0111) | 非 ORT 的多样性方式未探索 |
  | detail message 独立有效 | confirmed | D1-detail 0.5003 (γ=+0.0109) | 已确认, 不再深入 |
  | 机制组合协同增益 | refuted | HYB/ORT+detail/ORT+HYB 全部 < 单机制 | 组合轴饱和 |
  | additive 注入范式存在天花板 | confirmed | 所有 additive 变体 ≤ 0.5012, DTW 0.4968 | 非 additive 范式已入队(FLM), 待验证 |
  | cluster token 交互提升质量 | unverified | C2C 在队列中 | intra-scale 交互待验证 |
  | cluster token 与 points 的 alignment | unverified | 无任何机制确保 cluster 反映 point 特征 | **本次新探索: PCL 对齐 loss** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | 多尺度 context + L1 loss | 核心 context 假设确认 ✓ |
  | M17-ORT | 0.5005 | cluster 正交正则 → 多样性 | 证明 cluster 质量可优化 ✓ |
  | D1-detail | 0.5003 | detail message 独立验证 | 第二有效机制 ✓ |
  | M32-DRP (running) | 0.4998@ep16 | 删除 routing 死代码消融 | 确认 routing 无益(上升趋势) |
  | M33-DTW | 0.4968 | density-weighted 加权回写 | 再次确认 additive 天花板 ✗ |
  | M26-ORT-HYB | 0.4998 | ORT 提升 HYB 但不及单机制 | 组合无增益 ✓ |
  | M27-ORT-W5 | 0.4959 | orth_weight=0.05 过强 | 确认 0.01 是最优值 ✓ |
  | M25-REF | 0.4892 | refine gather→cluster 更新 | refine 连续失败 ✗ |
  | M34-Q2P (running) | — | query→point 直接投影注入 | 刚启动, 早期指标待观察 |
  | M38-FLM (waiting) | — | FiLM multiplicative modulation | 首次非 additive 注入, 关键实验 |
  | M39-C2C (waiting) | — | intra-scale cluster self-attention | cluster token 交互方向 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 有效 (+0.0118), ORT 有效 (+0.0111), additive 天花板 ~0.5005
  - 未验证:
    1. Non-additive injection (FLM in queue) — 最关键缺口
    2. Cluster token interaction (C2C in queue)
    3. **Cluster token quality beyond orthogonality: do tokens represent their points?** ← 本次填补
    4. Multi-loss synergy (ORT + new loss)
  - 矛盾/疑问: ORT 证明 cluster 多样性重要, 但没回答 "cluster 是否准确反映其点云区域"。如果 cluster tokens 偏离了原始 points, 回写的 context 可能是噪声。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M40-PCL: 填补 "cluster token quality" 缺口。Point-Cluster alignment loss 拉近 cluster token 与 assigned points 的均值。假设: cluster 经过 attention 处理后可能偏离原点云特征, 对齐 loss 保持 grounding → 回写 context 更准确 → mIoU 提升。
  - 与 FLM/C2C 互补: FLM 改注入方式, C2C 改 token 交互, PCL 改 token 质量 — 三个正交维度
  - 如果 PCL > 0.5012 → cluster token alignment 是关键, 后续可扫 alignment weight
  - 如果 PCL ≤ 0.5012 → alignment 不解决天花板问题, 等待 FLM/C2C 结果
  - 与 goal.json 对应: 直接服务 mIoU ≥ 0.51, 结构性变更 (新 loss 函数)

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260729-020301.md
================================================================================
