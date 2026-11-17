================================================================================
  Motivation Review — cluster_project
  2026-08-26 13:15:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    归因 seed-1999 红利, 结构真实 mean ~0.498)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-26 13:07:35: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 24h 内无 type=question;
    最近 route_change (08-26 01:10 M134-DUAL 轴关闭) 为已执行决策非保留 → 自主设计允许
  - 触发原因: M138-MLAY-DUAL 推送后 waiting=4 < 容量4+1=5 → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder-access 双通路 {qla,qia}×KV 2×2 | 关闭 | M134-DUAL=0.4970; qla=0.5010 ✓/qia=0.4950 ✗ | 矩阵补格完成 |
  | {decoder-access, 多层}×{DCA,DCM,DCMV} 叠加 | 关闭 | M125=0.4970 / M126=0.4980 — 不叠加 | 关闭 |
  | MFP / CSORT / CTF-token-FFN | 证伪 | MFP 3-seed 均值 0.4950; CSORT 归因 seed1999 | 关闭 |
  | **cluster token 同尺度实例判别性 (CLICA)** | 未测 | M140-CLICA queued | InfoNCE 判别监督 |
  | **cluster token 跨尺度实例一致性 (CSIC)** | 未测 | M141-CSIC queued | 粗 token 对主导实例忠实 |
  | **CLICA × CSIC 双监督交互** | 未测 | **本次设计 M142** | 判别性与一致性是否互补叠加 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M134-DUAL (01:07 终态) | 0.4970 | {qla,qia} 双通路直读 cluster KV | 补齐 2×2 矩阵, 双通路不叠加 |
  | M135-DCM-S42 (07:07 终态) | 0.4970 | DCM × seed42 复现 | 确认 M124=0.5010 含 seed-1999 成分, 机制有效但不够破顶 |
  | M136-MLAY-DCMV (13:07 终态) | 0.4960 | {多层 legacy}×{DCMV} | 多层×decoder-access 轴再证不叠加 |
  | M138-MLAY-DUAL (本 tick 推送) | running | {MLay 2层}×{DUAL} | 满强度正交组合天花板格 |
  | M140-CLICA / M141-CSIC | queued | token 信息量两条 loss 路径 | 判别性 / 一致性 单测 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); 通路组合不叠加; MFP/CSORT/CTF 全灭;
    {qla,qia} 双通路矩阵补格完成; seed 敏感性确认 (M135, MFP 3-seed)。
  - 未验证: cluster token 信息质量的两条 loss 监督路径 (M140-CLICA 判别,
    M141-CSIC 一致) — 均 queued 未跑。
  - **本设计填补的缺口**: 两条 loss 路径是"同尺度内判别"与"跨尺度一致"两个
    独立子假设。它们的**交互** (双监督是否叠加) 完全未测 — 若 CLICA 判别的
    结果同时隐含一致 (细 token 已忠实), CSIC 边际增益小; 若两者正交, 双监督
    应让 cluster token 严格更信息化 → 破 0.50 平台。2×2 格 {判别性}×{一致性}
    缺组合格, 本次补上。
  - 矛盾/疑问: 若 M142 也 ≈0.501 → loss 监督轴与结构轴同样饱和, 需范式级新
    方向 (与 M139 结论交叉, 见 exp_design §7)。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M142-CTF-HCG-CLICA-CSIC: 在 champion ctf_hcg (M81=0.5012, seed 1999)
    上**同时**开启 use_cluster_inst_align + use_cluster_consistency。
  - 因果假设: cluster token 信息瓶颈有**两个独立可分离的缺陷维度** —
    (a) 同尺度内 token 无法判别实例 (CLICA 修复), (b) 跨尺度 token 对同一
    实例看法不一致 (CSIC 修复)。双监督同时修复两维 → token 严格更信息化 →
    多尺度 context 回写质量更高 → 定位 mask 更清晰 → 破 0.50 平台。
  - 为什么是 combo 而非新模块: 两 loss 已在 M140/M141 实现, csic 包 loss.py
    原生支持双 flag 并行 (line 779-798)。组合是 2×2 矩阵的自然补格, 零新增
    参数, 推理零成本, 与单测 (M140/M141) 直接正交对照。
  - 与 CLICA/CSIC 单测的区分: 单测回答"哪个缺陷维度是瓶颈", combo 回答
    "两维是否互补叠加"。三者的并集构成完整证据: 任一有效都能打开新信息路径。
  - 与 banned[]/constraints 校验:
    - 非 gate/非 langroute/非 attnpool/非 residual/非 true_route/非 3-6层注入。
    - 非调参: 双 loss = 新的联合优化计算图 (两条正交梯度路径进 cluster token),
      不是数值配置改动; 两个 λ=0.1 均来自既有 aux loss 量级约定 (sem_loss
      weight[6]=0.1, CLICA=0.1, CSIC=0.1), 非临时拍值。
    - FLOPs: 仅 ~328 token 级 cosine + InfoNCE, 可忽略 → ≤10G 约束满足。
    - 零新增参数 → 峰值显存无增量。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260826-1315.md
================================================================================
