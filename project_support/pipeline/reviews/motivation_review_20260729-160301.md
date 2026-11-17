================================================================================
  Motivation Review — cluster_project
  2026-07-29 16:03:01
================================================================================

## 1. Goal
  - pipeline/goal.json: Target mIoU ≥ 0.5100 on ScanRefer
  - Description: "多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度"
  - Champion: model_base1_quard2_c2f_enc_lite_posA_l1 = 0.5012 (γ=+0.0118 vs baseline 0.4894)
  - Gap to target: +0.0088
  - Constraints: Phase 1 禁止调参, 只允许结构性机制变更; FLOPs ≤ 10.0G; 分支停止 if Δ<0.002+plateau

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 cluster context 提升定位精度 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | — |
  | C2F routing 路由选择提升 context 质量 | **证伪** | DRP 删除路由=0.5012 = champion; A3 true_route=0.4468 | routing 是死代码 |
  | cluster 多样性 (ORT) 提升泛化 | confirmed | M17-ORT 0.5005 vs base (γ=+0.0111) | 与 champion 持平未超越 |
  | detail message_type 等效 context | confirmed | D1-detail 0.5003 | 独立有效但未超越 champion |
  | 机制组合产生协同 | **证伪** | ORT+detail=0.4955, ORT+HYB=0.4998, E4 res+detail=0.4944 | 组合轴饱和 |
  | additive 注入存在天花板 (~0.5005) | partial | 三个独立机制均止步 0.500-0.501 | FLM (multiplicative) 正在测试 |
  | **cluster token 质量影响 readback 效果** | **未验证** | 聚合仅 mean-pool, 无 token refinement | CTF 本次填补 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | 直接验证 context readback | 确认核心假设 ✓ |
  | M32-DRP | 0.5012 | 消融 routing: context readback alone = champion | routing=死代码, context 是唯一有效成分 ✓✓ |
  | M17-ORT | 0.5005 | 验证 cluster 多样性 | ORT 有效但无突破 |
  | D1-detail | 0.5003 | 验证 detail message_type | 等效 context, 无协同 |
  | M26-ORT-HYB | 0.4998 | ORT 提升 HYB 但未超越单机制 | 组合轴证伪 |
  | M24-ORT-D | 0.4955 | ORT+detail 组合 | 组合有害 |
  | M18-S2FM | 0.4933 | 2-scale ablation | 3-scale 必要 |
  | M23-CMX | 0.4910 | max-pool vs mean-pool | mean > max |
  | M34-Q2P | 0.4904 | query-to-point 直接注入 | 直接注入不如 context readback |
  | M25-REF | 0.4892 | refine message 机制 | refine 方向失败 |
  | M16-CSR | 0.4875 | cluster self-refine | refine 方向失败 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context readback 有效 (+0.0118), routing 装饰性, ORT/detail 独立有效, 组合无协同
  - 未验证: 
    1. **Cluster token 质量是否 bottleneck?** 聚合仅 mean-pool, token 无 refinement
    2. Multiplicative injection 是否突破 additive 天花板 (FLM running)
    3. Intra-scale token interaction 是否提升 token 质量 (C2C waiting)
    4. Sigmoid scale fusion 是否优于 softmax (SWI waiting)
  - 矛盾/疑问: 所有机制 ~0.5005 天花板 — bottleneck 在上游 (聚合) 还是下游 (decoder/backbone)?

## 5. Design Rationale（Q2+Q3: 为什么设计 M41-CTF）
  - Q2: 填补 "cluster token quality" 缺口
    - 当前所有实验聚焦 readback 机制 (additive/FLM/SWI/gate fusion)
    - 聚合步骤仅 mean-pool, token 形成后直接用于 readback
    - CTF test: per-token FFN refinement 是否提升 readback 质量
  - Q3: 验证/证伪 "cluster token 质量是 bottleneck" 假设
    - If CTF > 0.5012: token refinement 有效 → 瓶颈在 token 质量, 可继续 CAP/attention-pool 等
    - If CTF ≤ 0.5012: token refinement 无效 → 瓶颈在别处 (decoder/backbone), 重新审视方向
  - CTF 与队列中实验的关系: 
    - FLM: 测试注入范式 (additive vs multiplicative)
    - C2C: 测试 token 交互 (self-attention between tokens)
    - SWI: 测试 scale fusion (softmax vs sigmoid)
    - **CTF: 测试 token refinement (per-token FFN) — 唯一测试 token 自身质量的实验**
  - 基于 DRP 架构 (无 routing) 构建: DRP 已证明 routing=死代码, 是更干净的 baseline

## 6. Next Batch
  → M41-CTF: Cluster Token Feed-Forward — per-scale 2-layer FFN with residual + LayerNorm
  → see pipeline/designs/exp_design_20260729-160301.md
================================================================================
