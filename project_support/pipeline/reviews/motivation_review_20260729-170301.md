================================================================================
  Motivation Review — cluster_project
  2026-07-29 17:03:01
================================================================================

## 1. Goal
  - pipeline/goal.json: Target mIoU ≥ 0.5100 on ScanRefer
  - Description: "多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度"
  - Champion: model_base1_quard2_c2f_enc_lite_posA_l1 = 0.5012 (tied by M32-DRP 0.5012)
  - Gap to target: +0.0088
  - Constraints: Phase 1 禁止调参, 只允许结构性机制变更; FLOPs ≤ 10.0G; 分支停止 if Δ<0.002+plateau

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位精度 | confirmed | champion/DRP 0.5012 vs base 0.4894 (γ=+0.0118) | — |
  | C2F routing 路由选择提升 context 质量 | **证伪** | DRP 删除路由=0.5012 = champion | routing 是死代码 |
  | cluster tokens 是必要中间表示 (非绕行) | **confirmed** | M34-Q2P 移除 cluster→0.4904≈baseline | — |
  | additive 注入存在天花板 (~0.5005) | partial | 三个独立机制均止步 0.500-0.501 | FLM (multiplicative) running |
  | cluster token 质量影响 readback | **未验证** | CTF (FFN refinement) waiting | 聚合步骤完全未消融 |
  | cluster 聚合方式影响 token 表达 | **未验证** | 仅 mean/max 测试, max 更差 | 加权聚合未测试 |
  | cluster token 分布稳定性影响 readback | **未验证** | 无 normalization 消融 | LayerNorm 未测试 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | 直接验证 context readback | 确认核心假设 ✓ |
  | M32-DRP | 0.5012 | 消融 routing: context alone = champion | routing=死代码 ✓✓ |
  | M34-Q2P | 0.4904 | 消融 cluster tokens: 移除→baseline | cluster 必要性 ✓✓ |
  | M17-ORT | 0.5005 | 验证 cluster token 多样性 | ORT 有效, additive 天花板 |
  | D1-detail | 0.5003 | 验证 detail message_type | detail 等效 context |
  | M33-DTW | 0.4968 | density-weighted token 回写 | density prior 不改善 |
  | M23-CMX | 0.4910 | max-pool vs mean-pool | mean > max |
  | M38-FLM | running ep2 | multiplicative injection 范式 | **关键: 能否突破 additive 天花板** |
  | M39-C2C | running ep1 | intra-scale cluster self-attention | **token 交互是否必要** |
  | M40-SWI | waiting | sigmoid vs softmax scale fusion | **scale fusion 方法对比** |
  | M41-CTF | waiting | per-token FFN refinement | **token quality 是否瓶颈** |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context readback 有效, routing=死代码, cluster tokens 必要, additive ≤0.5005
  - 未验证:
    1. **Cluster token 聚合质量**: 当前仅 mean-pool (max 更差). Weighted aggregation → 用 learnable 权重替代 uniform mean → 更好的 token 表示
    2. **Cluster token 分布稳定性**: 聚合后 token 无 normalization → 不同 cluster 的 token magnitude 不一致 → 可能干扰 readback
    3. Injection paradigm: FLM running
    4. Token interaction: C2C running
    5. Scale fusion: SWI waiting
    6. Token quality (refinement): CTF waiting
  - 矛盾/疑问: 所有机制 ~0.5005 天花板 — bottleneck 在上游 (聚合) 还是下游 (decoder)?
    M34-Q2P 提供了关键证据: 移除 cluster tokens → 回到 baseline. 说明 cluster tokens 本身是必要环节, 不是 bottleneck.
    → 天花板可能来自 (a) 聚合方式过于粗糙, 或 (b) token 分布不稳定

## 5. Design Rationale（Q2+Q3: 为什么设计 M42-WCA + M43-CLN）
  - Q2: 填补 "cluster token 聚合质量 + 分布稳定性" 缺口
    - 当前所有 running/waiting 实验 (FLM/C2C/SWI/CTF) 操作在 token 形成之后
    - 聚合步骤 (points→cluster tokens via mean-pool) 完全未消融
    - M34-Q2P 证明 cluster tokens 存在是必要的 → 应优化 token 形成质量
    - M42-WCA: 测试 "更好的聚合 → 更好的 token → 突破天花板"
    - M43-CLN: 测试 "稳定的 token 分布 → 更好的 readback → 突破天花板"
  - Q3: 跑完后故事线推进
    - If WCA > 0.5012: 聚合质量是瓶颈 → 可继续 attention-pool / gated-pool 等
    - If CLN > 0.5012: token 分布是瓶颈 → 可进一步 LayerNorm 位置/类型消融
    - If both ≤ 0.5012: 聚合不是瓶颈 → 需要重新审视假设 (decoder/backbone/data)
  - 与队列中实验的关系:
    - FLM: 测试注入范式 (post-aggregation)
    - C2C: 测试 token 交互 (post-aggregation)
    - SWI: 测试 scale fusion (post-aggregation)
    - CTF: 测试 token refinement (post-aggregation)
    - **WCA: 测试聚合方式 (in-aggregation) — 唯一测试此维度的实验**
    - **CLN: 测试 token 分布稳定性 (pre-readback) — 唯一测试此维度的实验**
  - 均基于 DRP 架构 (无 routing 死代码)

## 6. Next Batch
  → M42-WCA: Weighted Cluster Aggregation — per-point learned softmax weights within each cluster
  → M43-CLN: Cluster LayerNorm — per-scale LayerNorm on cluster tokens before readback
  → see pipeline/designs/exp_design_20260729-170301.md
================================================================================
