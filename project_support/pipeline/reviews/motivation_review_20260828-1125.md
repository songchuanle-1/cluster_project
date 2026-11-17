================================================================================
  Motivation Review — cluster_project
  2026-08-28 11:25:00
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-28 11:07:37: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 近 24h 无 type=question;
    最近 10 条 decisions 为 queue_push/early_stop/skip_design/next_batch，无保留型
    route_change/question → 自主设计允许 (Phase 0.5 双闸门通过)
  - 触发原因: M144 推送后 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7 max=2
    = 4 槽位, 阈值 5) → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1=0.5012 vs A0=0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 | 关闭 |
  | 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C/CSF/FLM/pool/TrueRoute | 关闭 |
  | delivery×delivery 组合 | 关闭 | 6 次不叠加 (M125/126/134/136/138/139) | 关闭 |
  | HCG 多层注入 | 证伪 | M96=0.4940 (legacy@2 有效 M86=0.5010) | 关闭 |
  | loss 监督轴 (判别/一致) | 3连败 | M140=0.4970 / M141=0.4960 / M142=0.4890 (本tick) | M143/144 检验中 |
  | CSORT 应用位置 | 非关键 | M109=0.5010 ≈ M95 | 关闭 |
  | CSORT (cross-scale orth) | champion | M95=0.5020 | **跨 seed 脆弱** |
  | **CSORT 跨 seed 鲁棒性** | **未测** | s1999=0.5020 / s42=0.494 / s123=0.493 / s2026=0.490 (mean~0.495 < base 0.5012) | **本设计 M149** |
  | DCM / MLay / detail | 有效 | 0.5010 / 0.5010 / 0.5003 | ×CSORT 组合在队 (M146-148) |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | cross-scale orth 破平台 | 唯一破 0.5012 机制, 但跨 seed 脆弱 (mean~0.495) |
  | M142-CLICA-CSIC (本tick) | 0.4890 | loss 轴双监督组合 | loss 组合格闭合: 比单独低 0.007-0.008 |
  | M141-CSIC | 0.4960 | 跨尺度一致 loss | loss 一致轴饱和 |
  | M140-CLICA | 0.4970 | 判别性 loss | loss 判别轴饱和 |
  | M81-CTF-HCG (base) | 0.5012 | context 回写核心 | 跨 seed 亦敏感 (s123=0.494) |
  | M124-DCM | 0.5010 | decoder 直读 | 独立有效, ×CSORT 在队 M148 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; 结构变换/通路组合/多层注入全关; loss 监督轴 3 连败
    (M142 本 tick 补第 3 败 + 组合格闭合); CSORT 是唯一破平台机制。
  - 未验证: **CSORT 的跨 seed 脆弱能否被结构性修复**。champion 在 seed 1999 达
    0.5020, 但 s42=0.494 / s123=0.493 / s2026=0.490 (mean~0.495), 反而低于
    base 0.5012。论文要 claim CSORT 有效, 必须先解决"只在 1999 有效"的问题。
  - 假设: CSORT 的 abs-cosine 惩罚双侧同时更新 (coarse token 与 fine 聚合参考都
    带梯度) → 两者互相追逐形成反馈环 → 优化景观陡峭, 跨 seed 落入不同病态解。
    结构性修复: 对 fine 聚合参考 stop-gradient (借鉴对比学习 BYOL/SimSiam 的
    非对称更新), 让 coarse 只去相关到一个固定锚点 → 稳定 → 跨 seed 鲁棒。
  - 矛盾/疑问: 0.5020 级别的机制 (CSORT/MFP) 均单 seed 有效; 这是任务本身的
    seed 敏感性还是机制不稳定, 尚无结构性实验区分。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M149-CTF-HCG-CSORT-SG: champion 包 (cluster_mode='ctf_hcg_csort',
    csort_weight=0.01) 基础上, 将 `_cross_scale_orth_loss` 中 fine 聚合参考
    `.detach()` (stop-gradient), 其余完全一致, seed 1999 首筛。
  - 因果假设: "对称 abs-cosine 惩罚两侧同时更新 → coarse/fine 互相追逐反馈环 →
    跨 seed 病态解; 对 fine 参考 stop-gradient → coarse 以固定锚点去相关 →
    稳定优化 → 跨 seed 鲁棒, 且 1999 峰值不降 (去相关强度不变)"。
    一句话: "非对称去相关 (在线侧 chase 固定参考) → 稳定跨尺度互补 → 鲁棒破平台"。
  - 与 banned[]/constraints 校验:
    - 非 gate系/语言路由系/attnpool/true_route/residual 系; 非 3/4/6 层重复注入
      (cluster_att_num_layers=1 不变); 非大型 QKV 投影。
    - 非调参 (Phase 1.6): 无新超参, csort_weight=0.01 沿用 champion; stop-gradient
      是损失计算图的结构性非对称 (新梯度路径), 源自 BYOL/SimSiam 理论; 不以"试值"
      为目标。防御: 变体核心是"固定参考的稳定去相关", 不是调 weight/temperature。
    - FLOPs/显存: 无新增 (loss-only, 梯度路径变更), ≤10G 约束满足。
    - 与"分支停止: 提升<0.002"约束: 若 1999 峰值下降 → CSORT-SG 证伪, 记录为
      稳定机制无效证据; 若 1999 持平/提升 → 补跨 seed (s42/s123) 验证鲁棒性。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260828-1125.md
================================================================================
