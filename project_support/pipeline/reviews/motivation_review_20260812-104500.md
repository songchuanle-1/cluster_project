================================================================================
  Motivation Review — cluster_project
  2026-08-12 10:45:00
================================================================================

## 1. Goal
  - pipeline/goal.json: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: model_base1_quard2_c2f_enc_lite_posA_l1 0.5012 | Gap: +0.0088
  - Phase 1: NOT YET — continue exploring

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写提升定位 | confirmed | A1 context-only 0.5012 vs base 0.4894 (γ=+0.0118) | 需确认哪些设计必要 |
  | Routing 提升特征表达 | falsified | A3 true_route 0.4468, γ=-0.0544 vs A1 | 已排除 |
  | Token 质量独立提升 (CTF) | confirmed | M41-CTF 0.4995, γ=+0.0101 vs baseline | 单轴未破顶，需组合 |
  | 正确多尺度交付 (HCG) | confirmed | M65-HCG 0.5002, γ=+0.0108 vs baseline | 必要修复但本身不破顶 |
  | CTF×HCG 正协同 | confirmed (prelim) | M81-CTF-HCG 0.5012 (tie champion, stopped@ep31) | 需完整跑完50ep确认 |
  | ORT token 多样性 | promising | M17-ORT 0.5005, γ=+0.0111 vs baseline | 未与 CTF/HCG 组合 |
  | QMOD query 调制 | testing | M85-QMOD ep1 server-6 | 待验证 |
  | MLAY 多层注入 | testing | M86-MLAY ep1 server-6 | 待验证 |
  | CONS 一致性正则 | testing | M81-CONS just launched (waiting→running) | 待验证 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  对关键已完成实验:
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion (A1) | 0.5012 | 直接验证 context 回写有效 | 确认核心假设 ✓ |
  | M81-CTF-HCG | 0.5012★ | 首次正交轴正协同 (token质量×交付) | 证明两个独立机制可组合 ✓ |
  | M65-HCG | 0.5002 | 验证正确多尺度交付 | 确立 HCG 为必要修复 |
  | M41-CTF | 0.4995 | 验证 token FFN 精炼 | 确立 CTF 为有效 token 质量轴 |
  | M17-ORT | 0.5005 | 验证 token 多样性 (orth reg) | 确立 ORT 为有效正则化 |
  | M78-REAGG-HCG | 0.5008 | REAGG×HCG 组合未破顶 | reag 轴无正协同 |
  | M32-DRP | 0.5012 | DRP 单独达 champion 水平 | 但 stopped_unknown, 未确认 |
  | CCP 系列 | 0.4934-0.4952 | 跨尺度传播无效 | CCP 轴排除 |
  | detail 系列 | 0.4979-0.5003 | message 残差构造 | detail 作为 message 变体有效 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (γ=+0.0118); CTF token 精炼有效; HCG 正确交付有效; CTF×HCG 正协同
  - 未验证: 
    ① CTF×HCG 完整收敛 (M81 31/50 中断, 顶部轨迹未确定)
    ② ORT (token 多样性) 与 CTF×HCG 能否三轴正协同
    ③ SE 通道注意力能否增强 token 质量超越 CTF 单 FFN
    ④ ORT 与 HCG 单独组合是否有效 (简化对照)
  - 矛盾/疑问: 为什么 DRP (0.5012) 和 CTF×HCG (0.5012) 都停在 champion 水平? 0.5012 是否是一个平台天花板?

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M92-CTF-HCG-ORT: 填补 gap ② — 三轴协同 (token质量×交付×多样性) 尝试突破 0.5012 平台
  - M93-CTF-SEF: 填补 gap ③ — SE 通道注意力作为 token 质量的替代精炼路径, 对比 CTF 单 FFN
  - M94-HCG-ORT: 填补 gap ④ — 简化对照, 确认 ORT 增益是否依赖 CTF token 精炼
  - 预期: 这批跑完后, 明确 0.5012 是否能被三轴协同突破, 以及 SE 是否优于 CTF 单 FFN
  - Q3 回答: 若 M89 > 0.5012 → 三轴协同有效, 可进一步叠加 QMOD/MLAY; 若持平 → 0.5012 可能是当前架构天花板, 需要新突破方向

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260812-104500.md
================================================================================
