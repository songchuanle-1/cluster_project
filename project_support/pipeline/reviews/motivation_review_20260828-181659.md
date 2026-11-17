================================================================================
  Motivation Review — cluster_project
  2026-08-28 18:16:59
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-28 18:07:31: Phase 1 NOT YET
  - 活跃保留: goal.json constraints 无"活跃保留"条款; 近 24h 无 type=question;
    最近 10 条 decisions 为 queue_push/early_stop/skip_design/next_batch，无保留型
    route_change/question → 自主设计允许 (Phase 0.5 双闸门通过)
  - 触发原因: M145 推送后 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7
    max_tasks_per_gpu=2 = 4 槽位, 阈值 5) → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1=0.5012 vs A0=0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 | 关闭 |
  | 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C=0.4865 / CCP=0.4934 / CSF/FLM/pool | 关闭 |
  | delivery×delivery 组合 | 关闭 | 6 次不叠加 (M125/126/134/136/138/139) | 关闭 |
  | loss 监督轴 (判别/一致/目标) | 4连败 | M140=0.4970 / M141=0.4960 / M142=0.4890 / **M143-OBJG=0.5000 (本tick)** | M144-LQA 待终态 |
  | CSORT 应用位置 | 非关键 | M109=0.5010 ≈ M95 | 关闭 |
  | **CSORT (cross-scale orth)** | **champion** | M95=0.5020 | **跨 seed 脆弱** (mean~0.495) |
  | **write-back 冗余假设** | **未测** | champion 的 residual write-back 未约束与 inst_feats 的互补性 | **本设计 M150** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | cross-scale orth 破平台 | 唯一破 0.5012 机制, 但跨 seed 脆弱 |
  | M143-OBJG (本tick) | 0.5000 | 目标感知 aux loss (on base ctf_hcg) | loss 轴第 4 连败; 最接近 base 但仍 <0.5012 |
  | M39-C2C | 0.4865 | cluster token 自注意力 | **token 交互机制证伪** (注意力交互方向全灭) |
  | M71-CCP | 0.4934 | 粗→细 context 传播 | 交互/传播轴证伪 |
  | M140-CLICA / M141-CSIC / M142-dual | 0.4970/0.4960/0.4890 | loss 监督轴 | loss 组合格闭合 |
  | M81-CTF-HCG (base) | 0.5012 | context 回写核心 | 跨 seed 亦敏感 (s123=0.494) |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效; **交互/注意力机制全灭** (C2C/CCP/CSF/FLM/pool);
    loss 监督轴 4 连败 (OBJG 本 tick 补第 4 败); CSORT 是唯一破平台机制但 seed 脆弱。
  - 未验证: **write-back 与实例特征的互补性**。champion 的 residual write-back
    是 `point_feats + fused_msg` — fused_msg 由 cluster tokens (聚合自 point_feats)
    经 gate 融合而来, 天然与 point_feats 高度相关。若 msg 主要重复 inst_feats 已编码
    的信息, 则回写更新是"冗余再确认"而非"补充新 context"。**没有任何实验约束过
    msg ⊥ point_feats 这一对**。
  - 关键证据: 交互方向 (C2C/CCP/CSIC/CSF/FLM) 全部证伪 — 增加信息交互不能破平台;
    唯一破平台机制 CSORT 是**去相关方向**。故事线的下一步自然延续是"去相关轴"上
    找一个**新操作数**: 从"cluster token 之间" (CSORT) 移到"write-back 与实例特征
    之间" (OWC)。
  - 矛盾/疑问: 若 OWC 证伪 (msg 与 inst_feats 相关是必要的), 则说明回写机制本应
    "reinforce" 而非 "complement", 这是对动机的补充澄清。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M150-CTF-HCG-CSORT-OWC: champion 包 (cluster_mode='ctf_hcg_csort',
    csort_weight=0.01) 基础上, 新增正交回写 context loss (OWC): 在 cluster_attn
    forward 末尾, 对 write-back message fm 与输入 point_feats 做 abs-cosine 惩罚
    → 强制每次回写更新为 inst_feats 补充正交 (互补) 的新 context。
  - 因果假设: "residual write-back 若与 inst_feats 相关则更新冗余 → 强制 msg⊥feats
    → 每次更新添加互补信息 → 实例特征更丰富 → 破 0.5020"。是去相关轴 (唯一有效
    方向) 的新操作数: CSORT 去相关 token 之间, OWC 去相关 write-back 与更新目标。
  - 与 banned[]/constraints 校验:
    - 非 gate系/语言路由系/attnpool/qcond/agg/multi/true_route/prune/nomask;
    - 非 3/4/6 层重复注入 (cluster_att_num_layers=1 不变);
    - 非大型 QKV 投影; 非调参 (无新模块, loss-only, 无新超参扫参);
    - **residual 系辩**: banned 的 residual 系 (B5/E4) 是 message_type=residual
      (残差 message 构造); OWC 不改 message 构造, 是在 write-back 上的 orth loss,
      约束 (fm, point_feats) 关系 — 不同机制, 不同操作对象。
    - FLOPs/显存: loss-only, 无新增, ≤10G 满足。
    - 分支停止: 1999 首筛; 若 1999 峰值 <0.5020 或提升 <0.002 → OWC 证伪, 记录为
      "write-back 相关必要" 证据。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260828-181659.md
================================================================================
