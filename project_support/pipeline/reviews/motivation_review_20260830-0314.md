================================================================================
  Motivation Review — cluster_project
  2026-08-30 03:14
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-30 03:07:40: Phase 1 NOT YET
  - 活跃保留 (Phase 0.5 双闸门): goal.json constraints 无"活跃保留"条款;
    近 24h decisions 无保留型 route_change/question (最近为 skip_design/
    early_stop/queue_push/next_batch/code_sync) → 自主设计允许
  - 触发原因: M149 推送后 waiting=4 < 容量4+1=5 (server-4 2槽 + server-6 GPU7
    max_tasks_per_gpu=2 = 4 槽位, 阈值 5) → 自主补设计 1 个

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | A1=0.5012 vs A0=0.4894 (γ=+0.0118) | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 | 关闭 |
  | 结构变换 (FFN/交互/池化/融合) | 全灭 | C2C/CCP/CSF/FLM/pool | 关闭 |
  | loss 监督轴 | 5连败(关闭) | M140-144 | 关闭 |
  | **多尺度 context 深度是核心收益** | **确认 (M86)** | 2层 legacy=0.5010 vs 1层 ctf_hcg=0.5012 (持平) | 深度已 2 层, 尺度数量未变 |
  | CSORT 跨 seed 稳定性 | 脆弱 | s1999=0.5020 / mean~0.495 | M149-SG 待验 |
  | CSORT 尺度范围 | M145-ALL 证伪扩展 | ALL=0.4920 | M152-F1 待验 |
  | CSORT × decoder-access | **本tick M148 证伪** | DCM=0.4990, 两父均 0.50+ | 关闭 |
  | CSORT × MFP 双机制正交 | 未测 | 各自独立 0.5020 | M153 在队 |
  | **全局场景尺度 (K=1)** | **未测** | 3 尺度 [256,64,8] 无场景级 token | **M154 (本设计)** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | M95-CTF-HCG-CSORT (champion) | 0.5020 | 跨尺度 token 去相关 | 唯一破 0.5012 机制之一 |
  | M86-MLAY (2层 legacy) | 0.5010 | 多尺度 context 深度 | 隔离出深度是核心收益来源 |
  | M119-CTF-HCG-MFP | 0.5020 | masked 重建 (token 完整性) | 与 CSORT 平级独立 0.5020 |
  | **M148-CSORT-DCM (本tick 终态)** | 0.4990 | CSORT×decoder-access | 证伪 decoder-access×CSORT 组合 |
  | M145-CSORT-ALL | 0.4920 | 全尺度对去相关 | 证伪"多对更好" |
  | M124-CTF-HCG-DCM | 0.5010 | decoder-access 单轴 | 平台饱和, 与 CSORT 无协同 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); **多尺度 context 深度是核心收益 (M86)**;
    组合线 (architecture×loss / loss×decoder-access) 多例不叠加 (M146/M148 再证)。
  - 未验证: 当前 context 的**尺度范围**是 [256,64,8] — 最粗只有 8 个区域 token,
    没有任何**场景级全局 token**。level_gate 融合的输入只用 point 位置统计
    (global_mean=point_feats 均值), 全局信息只影响权重, 不进 message 本身。
    因此 readback context 是"局部一致但全局无锚"的。
  - 矛盾/疑问: 全局尺度会否与局部尺度冗余 (全局 token = 8 区域 token 的均值,
    信息量是否已隐含)? 若全局 message 与 level_gate 的 global_mean 作用重叠 →
    收益有限; 若为 readback 提供场景先验 → 补全"深度×尺度" 最后一个未检格。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体 M154-CTF-HCG-CSORT-GSC: champion (ctf_hcg_csort) 基础上把 cluster 尺度
    扩展为 [256,64,8,1] — 第 4 尺度是单个全局 token (级联聚合 8 个区域 token 的
    均值, 经 CTF FFN 精炼后随 HCG composed gather 广播给所有点, 参与 level_gate
    融合回写)。CSORT 保持局部相邻对 (256↔64, 64↔8) 不变, 归一化 /2 同 champion;
    全局对 (8↔1) 排除, 避免 M145-ALL 证伪的扩展陷阱。
  - 因果假设: "多尺度 context 深度是核心收益 (M86) — 深度 = 有更多尺度的信息
    供 readback 融合。当前最粗只有 8 区域, 无场景级参考; 补一个全局 token 让
    每个点在融合时既有局部尺度 message 又有场景先验 message → context 更完整
    → 破 0.5020 平台"。单变量 vs champion: 仅新增全局 context 尺度。
  - 若 > 0.5020: "深度×尺度"双杠杆确认, 平台突破候选; 若 ≈0.5020: 全局 token
    冗余 (信息已隐含在 level_gate global_mean / 局部尺度融合中); 若 < 0.5020:
    全局 message 稀释局部 context (与 M145-ALL 同类的"多尺度反而有害")。
  - 与 banned[]/constraints: 非 gate系/语言路由/attnpool/qcond/agg/multi/
    true_route/prune/nomask; 非 3/4/6 层重复注入 (cluster_att_num_layers=1 不变,
    尺度数量≠注入层数); 非大型 QKV; 非 residual 系 (写回结构不变, 仅 message
    内容多一个尺度); 非 loss 监督轴 (CSORT 保持, 无新增 loss); FLOPs/显存近零
    新增 (1 个 token 的聚合+FFN); seed 1999 首筛。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260830-0314.md
================================================================================
