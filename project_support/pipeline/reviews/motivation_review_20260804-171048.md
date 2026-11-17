================================================================================
  Motivation Review — cluster_project
  2026-08-04 17:10:48
================================================================================

## 1. Goal
  - Target: mIoU >= 0.5100 | Champion: posA_l1 (Lite/DRP) 0.5012 | Gap: +0.0088 | Phase: 1 (NOT YET)
  - goal.json description: cluster: 多尺度 cluster context 机制 — cluster bank 聚合点云特征→
    cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类路由'假设已被
    证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51。
  - Phase 0.5 活跃保留检查: goal.json constraints[] 无"活跃保留"字样条款; decisions/_index.md
    最近 10 条全为 skip_design/queue_push/next_batch/terminal (无 route_change/question) →
    双源无保留, 自主设计允许。
  - check_goal.py: Phase 1 NOT YET (champion=0.5012, target=0.5100, gap=+0.0088)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位 | confirmed | champion 0.5012 vs baseline 0.4894 (γ=+0.0118) | 距 target +0.0088 |
  | C2F routing 贡献 | refuted | A3 true_route=0.4468; A4 shuffle=0.4941 < champion; DRP(去路由)=0.5012 | — |
  | 读回形式 (additive) 最优 | closing | BIL/NLR/FILM/FLM/CTF 全 < champion; M50-DGC 在跑 | DGC 待验 |
  | 聚合池化 mean 最优 | partial | max/weighted 差于 mean; dual=M51-DCA 在跑; var=M53-VAC 待验 | DCA/VAC |
  | 级联精炼 | untested | — | M52-CCR 待验 |
  | cluster token 表示富化 | untested | — | M53-VAC + M54-SAC 待验 |
  | 尺度数 | closed | 2-scale [256,64]=0.4933, [256,8]=0.4944 < 3-scale 0.5012 | — |
  | 组合 (ORT+detail 等) | refuted | M24-ORT-D=0.4955, M26-ORT-HYB=0.4998, E4=0.4944 | — |
  | **融合机制 = 瓶颈 (CTF 分析)** | **partial** | CTF(0.4995) 结论: "瓶颈不在 token 质量而在 readback/融合机制" | XCA/CSF/SWI 全 < 0.5012, 但均非 point-level 内容自适应 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | champion/DRP | 0.5012 | 多尺度 context 回写 | 核心假设确认 ✓ |
  | M17-ORT | 0.5005 | token 正交正则 | token 多样性有帮助但非瓶颈 |
  | M41-CTF | 0.4995 | cluster token FFN 精炼 | token 质量提升不足以破 ceiling; 结论指向 readback/融合 |
  | M45-NCR | 0.4980 | soft readback (attention assignment) | soft 稀释信息, 不如 hard gather |
  | M44-CSF | 0.4958 | 相邻尺度 token 交叉注意力 | token 级跨尺度交互无益 |
  | M22-XCA | 0.4954 | 全部 token self-attention (328×328) | N² 跨尺度交互无益 |
  | M50-DGC | running | difference-gated readback | readback 门控维度 |
  | M51-DCA | running | dual mean+max 聚合 | 聚合信息量维度 |
  | M52-CCR | waiting | 级联精炼 | 级联噪声维度 |
  | M53-VAC | waiting | mean+variance 二阶统计 | token 表示离散度 |
  | M54-SAC | waiting | 空间嵌入聚合 | token 表示空间信号 |

  关键规律 (30+ 变体): 读回形式/融合/选择/交互/调制/尺度数/组合全部收敛 ≤ 0.5012。
  CTF 分析明确把剩余瓶颈假设指向 "readback/融合机制" —— 但已试的融合变体 (XCA token级
  self-attention, CSF token级跨尺度, SWI sigmoid-vs-softmax) 均为 **token 级或 gate 形式级**,
  从无 **point-level 内容自适应** 的尺度融合: 当前 champion 的尺度权重只由静态 MLP
  (输入 point_feats+global_mean) 产生, 完全不感知各尺度 cluster token 的内容。

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回读有效 (+0.0118); routing 无用; 读回形式/交互/调制/尺度数/组合非瓶颈;
    token 质量 (CTF) 非瓶颈。
  - 未验证:
    (a) **point-level 内容自适应的多尺度融合** — 尺度权重由内容 QK 匹配决定, 而非静态 gate。
        XCA/CSF 都只在 token 层做跨尺度, 未在 readback 的 per-point 尺度融合层做内容自适应。
        这是 CTF 结论指向但从未精确探过的子维度。→ **M55-SCF**
    (b) 聚合池化 (DCA 在跑 / VAC 待验)、级联 (CCR 待验)、空间信号 (SAC 待验) — 已在队列。
  - 矛盾: 30+ 变体 ≤ 0.5012, 但没有任何变体让 readback 的尺度权重 "看见" 各尺度 context
    的实际内容。静态 gate (softmax(MLP[point, global_mean])) 无法区分 "这个细尺度 token
    与点语义匹配" vs "该 token 被噪声污染", 是融合机制里唯一未被探的空白。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  ### M55-SCF (Scale-Content Fusion)
  - 填补缺口 (a): 用 per-point 内容注意力替代静态尺度 gate。
    点特征作 query, 其自身 3 个尺度 cluster message 作 key/value, 注意力权重依各尺度
    context 与点的内容匹配度而定 → 内容自适应的 scale selection。
  - 结构: 3 个 Linear (scf_q/k/v, 各 256→256) + 3-token attention, O(N·3) 线性, 非 N²。
  - 因果: "当某尺度 token 与点特征语义不匹配 (边界点被细尺度噪声污染 / 粗尺度 token 稀释
    局部细节) 时, 静态 gate 无法据此调整; 内容注意力让尺度权重直接反映 context 与点的
    匹配质量, 是 CTF 分析 'readback/融合机制瓶颈' 的精确探针。"
  - 预期: >0.5012 → 内容自适应尺度选择是瓶颈; ≈0.5012 → 融合机制假设进一步证伪
    (与 XCA/CSF 一起排除该方向)。

  ### 为何不设计第二个变体
  - M50-DGC / M51-DCA 结果即将产出 (no_impr 4-5/10), 它们将判定 readback 门控与聚合
    池化两个剩余假设; 在设计 M55-SCF 之外再推新变体会绕过这些即时证据, 降低批次质量。
  - 队列 (M52/M53/M54 + M55-SCF) 深度达到可用卡数3+1=4 的下限, 满足自主设计硬性要求。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260804-171048.md
================================================================================
