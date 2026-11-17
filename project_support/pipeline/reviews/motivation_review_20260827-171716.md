================================================================================
  Motivation Review — cluster_project
  2026-08-27 17:17:16
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    归因 seed-1999 红利, 结构真实 mean ~0.495)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-27 17:07:36: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 近 24h 无 type=question;
    最近 route_change (08-26 01:10 M134-DUAL 轴关闭) 为已执行决策非保留 → 自主设计允许
  - 触发原因: M141 推送后 waiting=4 < 容量4+1=5 → 自主补设计 1 个
  - 本 tick 新证据: **M140-CLICA 终态 0.4970** — 判别性 loss 单轴 < ctf_hcg base
    (0.5012), 与 DUAL 双通路 (M134=0.4970) 同水平, 判别性监督轴已饱和;
    **M141-CSIC 已推送 server-4 gpu0** (跨尺度一致 loss 检验中)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012 | 关闭 |
  | cluster token 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C/CSF/FLM/pool/TrueRoute | 关闭 |
  | 通路组合叠加 (qla/qia/MLay/detail ×) | 关闭 | M125/M126/M134/M136/M138 均不叠加 | 关闭 |
  | 多层注入 (ctf_hcg@2) | 证伪 | M96-CTF-HCG-2LAY=0.4940 < ctf_hcg@1 0.5012 | 关闭 (legacy@2 有效=0.5010) |
  | cluster token 同尺度实例判别 (CLICA) | 饱和 | M140=0.4970 < base 0.5012, 与 DUAL 同水平 | 判别轴无增益 |
  | cluster token 跨尺度一致 (CSIC) | 检验中 | M141 running | 粗 token 对主导实例忠实 |
  | CLICA×CSIC 双监督 / OBJG / LQA | queued | M142/M143/M144 | loss 监督其余维度 |
  | **champion CSORT 全尺度对去相关** | 未测 | **本次设计 M145** | 非相邻尺度 8↔256 冗余 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 跨尺度 orth loss 破 0.5012 平台 | 核心机制 ✓ (seed-1999 脆弱) |
  | M140-CLICA (本 tick 终态) | 0.4970 | 判别性 loss 监督 cluster token | 判别轴无效, 监督轴需换方向 |
  | M96-CTF-HCG-2LAY | 0.4940 | 多层注入 ctf_hcg | 层数轴对 HCG 有害, 关闭 |
  | M86-MLAY (legacy@2) | 0.5010 | legacy 基底 2 层 | 层数轴对 legacy 有效 |
  | M138-MLAY-DUAL (本 tick 早前终态) | 0.4990 | 组合轴 | 组合不叠加再证 |
  | M134-DUAL / M133-DCMV | 0.4970/0.4950 | 通路变体 | 通路轴饱和 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; 结构变换全灭; 组合不叠加; 多层对 HCG 有害;
    判别性 loss (CLICA) 无效。
  - 未验证: **champion CSORT 机制的作用边界** — CSORT 只对相邻尺度对 (64↔256,
    8↔64) 去相关, 非相邻尺度对 (8↔256) 的去相关从未测试。8 个全局尺度 token 与
    256 个细尺度 token 之间若仍共享全局冗余, 则 context 回写的信息容量被冗余
    占用。这是唯一未探索的、直接扩展 champion 获胜机制的空白。
  - 矛盾/疑问: CLICA 判别轴已饱和; CSIC/OBJG/LQA 若也失败 → loss 监督轴穷尽,
    需范式级新方向 (记为 question)。本设计在 loss 监督轴之外独立下注: 扩展
    已证明有效的 orth 轴, 与 loss 轴正交, 不浪费任何一个正在检验的方向。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M145-CTF-HCG-CSORT-ALL: 在 champion (ctf_hcg_csort, seed 1999) 上把
    cross-scale orthogonality loss 从**相邻尺度对**扩展到**全尺度对** (含 8↔256
    非相邻对, 通过子簇映射组合构造 256→8 映射)。零新增参数, csort_weight=0.01
    沿用 champion。
  - 因果假设: 相邻尺度已去相关, 但 8 全局 token 与 256 细 token 之间仍有冗余
    (8-token 聚合了大片细特征, 天然与其 256 子孙高相关) → 全尺度去相关后每尺度
    携带完全互补的 context → 多尺度 readback 信息容量最大化 → 定位更准 → 破 0.5020。
    一句话: "让所有尺度对的 context 都互补 → 回写信息更富 → 定位更准"。
  - 与 CSORT 的区别: 单变量 — 只扩大 orth 惩罚的尺度对范围, 其余完全一致。
  - 与 banned[]/constraints 校验:
    - 非 gate系/非语言路由系/非 residual 系; 非 N² attention (仍是 token 级 pairwise)。
    - 非调参: 新 loss term (新尺度对 = 新计算图路径), 非数值配置改动; weight 沿用
      0.01; 结构首筛 seed 1999 ✓; 禁改 schedule ✓。
    - FLOPs/显存: 仅增加 (8×256) 对级 abs-cosine, 可忽略 → ≤10G 约束满足。
    - 与"分支停止: 提升<0.002"约束: 若 M145 增益 <0.002 → orth 扩展轴停止,
      作为 CSORT 边界消融证据记录。
  - 为何仍值得赌: 结构变换、组合、多层、判别 loss 四轴全灭, 唯一被证明有效且
    尚有扩展空间的机制就是 champion 的 cross-scale orth。直接在获胜机制上扩展
    是当前最高概率的破平台方向; 即使不破 0.51, 失败本身也界定了 CSORT 的
    作用边界 (消融证据)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260827-171716.md
================================================================================
