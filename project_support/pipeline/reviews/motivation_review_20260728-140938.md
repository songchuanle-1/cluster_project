================================================================================
  Motivation Review — cluster_project
  2026-07-28 14:03:01
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
  | routing 有害 | confirmed | A3 TrueRoute 0.4468 (γ=-0.0544) | A4 shuffle 0.4941 确认结构性注入有害 |
  | orthogonality 增强多样性 | confirmed | M17-ORT 0.5005 (γ=+0.0111 vs base) | 非 ORT 的正则方式未探索 |
  | detail message 独立有效 | confirmed | D1-detail 0.5003 (γ=+0.0109) | detail+其他组合均失败 |
  | 机制组合协同增益 | refuted | HYB 0.4898, ORT+detail 0.4955, ORT+HYB 0.4998 | 所有组合 < 单机制，组合轴饱和 |
  | context 注入方式影响上限 | unverified | 当前 additive-only, gate×message 范式 | 非 additive 注入方式完全未探索 |
  | cluster token 交互提升质量 | unverified | XCA(cross-scale attn) 0.4954, CSR(refine) 0.4875 | intra-scale 交互从未尝试 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | 多尺度 context + C2F routing | 核心 context 假设确认 ✓ |
  | M17-ORT | 0.5005 | cluster 多样性正则 → 正交约束 | 证明 cluster 质量可优化 ✓ |
  | D1-detail | 0.5003 | detail message type → 点级消息 | 第二有效机制确认 ✓ |
  | M26-ORT-HYB | 0.4998 | ORT 挽救 HYB (+0.0100) | 组合无增益，但 ORT 稳健 ✓ |
  | M25-REF | 0.4892 | refine gather→cluster 更新 | refine 两次均 < baseline ✗ |
  | M21-HYB | 0.4898 | hybrid context+detail | 单用远低于单机制 ✗ |
  | M22-XCA | 0.4954 | cross-scale cluster attn | 跨尺度有微弱增益 ✓ |
  | M1-QGC | 0.4939 | query-gated context | query 信息不带来增益 ✗ |
  | M32-DRP (running) | 0.4743@ep10 | 删除 routing 死代码 | 运行中，早期指标可接受 |
  | M33-DTW (running) | 0.4839@ep10 | density 加权 cluster token | 运行中，上升趋势 |
  | M34-Q2P (waiting) | — | query→point 直接注入 | 待启动 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: cluster context 有效 (+0.0118), ORT 正交有效 (+0.0111), detail 独立有效 (+0.0109)
  - 未验证:
    1. context 注入方式: 当前仅 additive, multiplicative (FiLM) 完全未探索
    2. cluster token 交互: intra-scale self-attention refine (vs cross-scale XCA 0.4954)
    3. 所有有效机制 (context/ORT/detail) 通过不同维度接近 0.5005~0.5012, 但无人超越 champion — 暗示 additive 注入可能是瓶颈
  - 矛盾/疑问: 为什么所有单机制都止步于 ~0.5005 却无法突破? additive context injection 的增益是否存在硬上限?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M38-FLM: 填补 "context 注入方式" 缺口。FiLM (multiplicative modulation) vs champion additive — 测试注入范式本身是否是瓶颈
  - M39-C2C: 填补 "cluster token 交互" 缺口。Intra-scale self-attention (vs XCA cross-scale 0.4954) — 测试同尺度 cluster 间是否需要相互感知
  - 预期: 如果 FiLM > 0.5012 → 注入范式是关键瓶颈，后续聚焦 modulation 方向; 如果 C2C > 0.5012 → cluster token 需要交互 refine; 如果都 ≤ 0.5012 → 当前 single-mechanism 天花板在 ~0.501, 需考虑多机制协同或 loss 创新
  - 与goal的对应: 两条均直接服务 "提升 mIoU 到 0.51" 目标。均为结构性变更 (新 forward/新模块)，符合 Phase 1 约束

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260728-140301.md
================================================================================
