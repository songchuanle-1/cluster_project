================================================================================
  Motivation Review — cluster_project
  2026-08-14 03:21:44
================================================================================

## 1. Goal
  - pipeline/goal.json: "cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: model_base1_quard2_c2f_enc_lite_posA_l1 0.5012 | Gap: +0.0088
  - Phase 1: NOT YET — continue exploring

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写提升定位 | confirmed | A1 0.5012 vs base 0.4894 (γ=+0.0118) | 需确认哪些设计必要 |
  | Routing 提升特征表达 | falsified | A3 true_route 0.4468, γ=-0.0544 | 已排除 |
  | Token 质量 (CTF FFN) | confirmed | M41-CTF 0.4995, γ=+0.0101 | 单轴未破顶 |
  | 正确多尺度交付 (HCG) | confirmed | M65-HCG 0.5002, γ=+0.0108 | 必要修复, 本身不破顶 |
  | CTF×HCG 正协同 | confirmed (prelim) | M81 0.5012 tie champion (31/50 中断) | 完整收敛种子验证 M89/M90/M91 进行中 |
  | ORT token 多样性 | **已证伪(梯度断流)** | 2026-08-14 发现 ORT 老实现 orth_loss 被 detached 累积, dec 重建常数 tensor, 梯度从不回流 → M17-ORT 0.5005 非 ORT 机制所致 | 需修复后重测 |
  | CONS 一致性正则 | falsified | M81-CONS 0.4950 done_earlystop (本 tick 终态) | 排除 |
  | QMOD query 调制 | falsified | M85-QMOD 0.4930 | 排除 |
  | MLAY 多层注入 | testing | M86-MLAY 2/50 server-6 | 待验证 |
  | DET detail message | 单独有效/组合被稀释 | D1 0.5003, M84-DET-CTF-HCG 0.4990 | 不再与其它机制组合 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion (A1) | 0.5012 | 直接验证 context 回写有效 | 确认核心假设 ✓ |
  | M81-CTF-HCG | 0.5012★ | 首次正交轴正协同 (token质量×交付) | 证明两独立机制可组合 ✓ |
  | M32-DRP | 0.5012 | 与 champion 持平, stopped_unknown | 平台天花板信号 |
  | M17-ORT | 0.5005 | 曾被归因于 ORT — 现证伪(梯度断流) | 需修复后重测多样性轴 |
  | M84-DET-CTF-HCG | 0.4990 | detail × CTF×HCG 无叠加 | detail 组合轴排除 |
  | M81-CONS | 0.4950 | 一致性正则无效 (本 tick) | consistency 型排除 |
  | M85-QMOD | 0.4930 | query 调制弱 | 突破①方向弱 |
  | M86-MLAY | running 2/50 | 多层注入 | 突破②方向测试中 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; CTF token 精炼有效; HCG 正确交付有效; CTF×HCG 正协同达 champion-tie
  - 未验证:
    ① **多样性轴从未被真正测试** — ORT 老实现梯度断流, M92-CTF-HCG-ORT 队列中(修复后)将首次真正施压多样性
    ② **跨尺度多样性** — ORT 只做尺度内 token 去相关; 尺度间(粗 vs 细)去相关从未测试
    ③ 多层注入 × CTF×HCG 协同 (M86 只测 champion 基底)
    ④ 0.5012 是否为当前架构天花板 (多机制反复命中)
  - 矛盾/疑问: 为何 M17-ORT (0.5005) / DRP (0.5012) / CTF×HCG (0.5012) 都停在 0.5012 附近?
    若 ORT 从未真正生效, 则多样性轴是**全新未探索**的优化方向, 可能是破顶关键。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M95-CTF-HCG-CSORT: 填补 gap ② — 跨尺度正交 loss (粗 token ⊥ 细子簇聚合), 首次
    从"尺度间多样性"角度施压, 让各尺度携带互补 context, 直接服务"多尺度"故事核心。
    新 loss, 新计算图, 梯度真实回流 (修复版累积器)。
  - M96-CTF-HCG-2LAY: 填补 gap ③ — 多层注入 × 更强的 CTF×HCG 基底, 复用 M86 正在
    验证的 cluster_att_num_layers=2 结构变更。
  - M92 修复 (ctf_hcg_ort): 填补 gap ① — 让队列中已存在的三轴组合首次真正施压
    ORT 多样性。
  - Q3 回答: 若 M95/M92 破 0.5012 → 多样性轴是破顶关键, 故事线新增"尺度间/内多样性"
    证据; 若持平 → 0.5012 为架构天花板, 需转向更激进的机制 (如 query 侧深层调制)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260814-0321.md
================================================================================
