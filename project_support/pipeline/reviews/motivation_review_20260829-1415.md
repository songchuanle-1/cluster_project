================================================================================
  Motivation Review — cluster_project
  2026-08-29 14:15
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-29 14:07:47: Phase 1 NOT YET
  - 活跃保留 (Phase 0.5 双闸门): goal.json constraints 无"活跃保留"条款;
    近 24h decisions 无保留型 route_change/question (最近为 skip_design/
    early_stop/queue_push/next_batch/code_sync) → 自主设计允许
  - 触发原因: M148 推送后 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7
    max_tasks_per_gpu=2 = 4 槽位, 阈值 5) → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1=0.5012 vs A0=0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 | 关闭 |
  | 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C/CCP/CSF/FLM/pool | 关闭 |
  | loss 监督轴 | 5连败(关闭) | M140-144 (OBJG=0.5000 最佳) | 关闭 |
  | CSORT 跨 seed 稳定性 | 脆弱 | s1999=0.5020 / mean~0.495 | M149-SG 待验 |
  | CSORT 尺度范围 | M145-ALL 证伪扩展 | ALL=0.4920 | M152-F1 待验 |
  | CSORT × message-type | **本tick M146 证伪** | DET=0.4970, γ=-0.0050 vs champion | 关闭 (context 胜) |
  | **CSORT × MFP 双机制正交** | **未测** | 各自独立 0.5020, 从未组合 | **M153 (本设计)** |
  | write-back 正交 (soft/hard) | 未测 | — | M150-OWC / M151-ODW 在队 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 跨尺度 token 去相关 | 唯一破 0.5012 机制之一 |
  | M119-CTF-HCG-MFP | 0.5020 | masked 特征重建 (token 完整性) | 与 CSORT 平级的独立 0.5020 机制 |
  | **M146-CSORT-DET (本tick 终态)** | 0.4970 | CSORT×detail 消息 | 证伪 message-type 组合: detail 与去相关负交互 |
  | M145-CSORT-ALL | 0.4920 | 全尺度对去相关 | 证伪"多对更好" |
  | M147-MLAY-CSORT (running) | — | CSORT×MLay 跨类组合 | 组合格最高性价比补格 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); 交互/注意力全灭; loss 监督轴关闭;
    CSORT 与 MFP 是**两个独立达到 0.5020 的机制**; 组合线 (architecture×loss)
    多例不叠加 (M146-DET 本tick 再证)。
  - 未验证: **两个同为 loss 级、作用于 cluster token 表示、独立达 0.5020 的
    机制 (CSORT 去相关 × MFP 重建) 是否正交**。此前组合失败的均为
    architecture×loss (delivery×delivery 6 次) 或 loss×message-type; 从未有
    loss×loss 且目标互补 (diversity × completeness) 的组合。
  - 矛盾/疑问: 去相关 (推远) 与重建 (保持信息完整) 在 token 表示上是否冲突?
    若冲突 → 组合失败, 结论"两机制冗余/互斥"; 若互补 → 破 0.5020 平台。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M153-CTF-HCG-CSORT-MFP: champion (ctf_hcg_csort) 基础上叠加 MFP
    masked 重建 loss。零新增参数 (复用两边的已有 head), 零新增超参
    (csort_weight=0.01 / mfp_weight=0.1 / mask_ratio=0.15 均沿用验证过的值)。
  - 因果假设: "CSORT 推远跨尺度 token (diversity), MFP 强制单尺度 token
    内部信息完整 (completeness); 两者作用于同一表示的不同维度, 组合后
    readback context 既互补又完整 → 提升定位精度"。这是 story 里
    "多尺度 context 质量" 维度的双杠杆测试。
  - 若组合 > 0.5020: 双机制正交确认, 平台突破候选; 若 ≈0.5020: 机制冗余,
    "去相关已隐含完整性" 或反之; 若 < 0.5020: 机制冲突 (去相关破坏重建目标)。
  - 与 banned[]/constraints: 非 gate系/语言路由/attnpool/qcond/agg/multi/
    true_route/prune/nomask; 非 3/4/6 层注入 (cluster_att_num_layers=1 不变);
    非大型 QKV; 非 residual 系 (不改 message 构造/写回结构); 非 loss 监督轴
    (MFP 是自监督表示 loss, 同 CSORT 属表示质量轴, 非 CLICA/CSIC/OBJG/LQA
    任务监督); FLOPs/显存零新增; seed 1999 首筛。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260829-1415.md
================================================================================
