================================================================================
  Motivation Review — cluster_project
  2026-08-24 07:13:44
================================================================================

## 1. Goal
  - goal.json description: "cluster: 多尺度 cluster context 机制 — cluster bank
    聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。
    注: 原'聚类路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。
    目标 mIoU ≥ 0.51"
  - Target: mIoU ≥ 0.5100 | Champion: M95-CTF-HCG-CSORT = 0.5020 (seed 1999,
    CSORT 轴已关闭, 0.5020 归因 seed-1999 红利)
  - Gap: +0.0080 | Phase: 1 (NOT YET) — 继续自主设计
  - Baseline: model_base1 = 0.4894 (γ champion = +0.0126)
  - check_goal 2026-08-24 07:07:34: Phase 1 NOT YET, continue exploring
  - 活跃保留: goal.json constraints 无"活跃保留"条款 (07-19 已解除);
    最近 24h 无未决 question/route_change → 自主设计允许

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 (context-only) | confirmed | A1=0.5012 vs A0=0.4894, γ=+0.0118 ≥ 0.005 | 无 |
  | 显式 routing 注入 | 证伪 | A3=0.4468 vs A1=0.5012, γ=-0.0544 | 关闭 |
  | decoder 直接访问 cluster tokens (方向①) | partial | DCM=0.5010 (qla 共享通路) > DCA=0.4970 (专用分支) | **qia 视觉通路 DCMV 运行中 (M133); 双通路叠加 DUAL 未测** |
  | 多层注入 (方向②) | partial | MLay 2层=0.5010; 3/4/6层重复注入已证退化 (banned) | MLay×DCA/DCM 组合排队 (M125/M126) |
  | MFP (masked feature prediction) | unconfirmed→疑似伪 | M119=0.5020 tie champion (seed1999); **M129 seed42=0.4869 < baseline 0.4894** | M130 seed123 running, 3-seed 矩阵判定中 |
  | encoder-side token 质量轴 (CCL/CGA/BCF/SRL/MEMBANK) | 证伪 | 0.489-0.493 全灭 | 关闭 |
  | CSORT 跨 scale 去相关 | 证伪 | 3/4 seed 负, 0.5020 归因 seed1999 | 关闭 |
  | decoder-access 2×2 {context/detail}×{DCA/DCM} | 完成 | DCM 最优 0.5010, 其余 ≤0.499 | 矩阵已满格, 无格破顶 |
  | {qla,qia}×{cluster KV} 2×2 | 进行中 | DCM(qla)=0.5010 ✓, DCMV(qia) running, **DUAL(双通路) 未测** | M134-DUAL 补格 |
  | DCM seed 稳健性 | 未验证 | DCM 仅 seed1999=0.5010 | **无 DCM seed 对照 — 本批补 M135-DCM-S42** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|--------------|
  | M119-MFP | 0.5020 | 特征级 mask 重建 aux loss | encoder-side 唯一不伤, 但 M129 seed42=0.4869 证伪倾向, 待 M130 定论 |
  | M124-DCM | 0.5010 | decoder query 经 qla 语言通路共享 KV 读 cluster context | decoder-access 轴最优; **共享通路 > 专用分支 (DCA 0.4970)** |
  | M123-DCA | 0.4970 | decoder query 专用分支 cross-attend cluster | 弱于 DCM, 轴内淘汰 |
  | M86-MLAY | 0.5010 | 2层注入 (方向②) | 多层注入有效但平台饱和 |
  | M128-DET-DCM | 0.4990 | detail message × DCM | detail 对 DCM 无正叠加, 2×2 满格 |
  | M127-DET-DCA | 0.4870 | detail message × DCA | detail×DCA 负交互 |
  | M129-MFP-S42 | 0.4869 | MFP seed42 对照 | **< baseline, MFP 疑似 seed-1999 红利** |
  | M130-MFP-S123 | running 8/50 | MFP seed123 对照 | 3-seed 矩阵第3点, 决定 M131/M132 去留 |
  | M133-DCMV | running 1/50 | qia 视觉通路 cluster KV (DCM 对称版) | 补 {qla,qia} 缺格 |
  | M95-CTF-HCG-CSORT | 0.5020 | 跨 scale 正交化 | seed1999 outlier, 轴已关闭 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效 (+0.0118); decoder-access 轴 DCM 最优 (0.5010, qla
    共享通路 > DCA 专用分支); 2层注入有效 (0.5010); MFP 疑似 seed 红利 (M129 证伪倾向)。
  - 未验证: ① MFP 3-seed 矩阵第3点 (M130 running) — 决定 M131/M132 撤回; ② qia
    视觉通路 DCMV 结果 (M133 running); ③ **{qla,qia}×{cluster KV} 2×2 的最后一个
    缺格 DUAL (双通路同时开启)** — 若 DCMV 的机制是"通路不变 (pathway-invariant)",
    DUAL 直接检验两条通路是否叠加; ④ **DCM 无 seed 对照** — CTF-HCG 跨 seed 已证
    脆弱 (s42=0.4963/s123=0.494), MLay/MFP 均有 seed 对照在跑, DCM 是唯一缺口,
    若 DCM 也 seed 脆弱则 decoder-access 轴的成功同样是 seed-1999 红利。
  - 关键洞察: 所有 writeback/decoder-access 机制收敛于 ~0.501 平台 (seed1999),
    结构真实 mean ~0.498。组合尝试 (detail×DCM=0.4990 无协同) 表明消费端机制
    已饱和同一 cluster token 内容。破平台依赖: (a) 正交组合 (排队中 M125/M126/
    M131/M132), 或 (b) 尚未完成的通路补格 (DUAL)。同时 DCM 的 seed 稳健性是
    decoder-access 轴能否写进论文的硬证据缺口。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - 变体1 M134-DUAL (DCM+DCMV 双解码通路): decoder query 同时经 qia (视觉/实例)
    与 qla (语言) 两条通路直读多尺度 cluster tokens。
    因果假设: DCM 已验证 qla 通路有效 (0.5010), DCMV (qia) 正在验证。若 decoder-access
    收益是"通路不变且可叠加", 双通路同时开启应产生多于单通路的场景上下文增益;
    若 qla 已捕获 decoder 侧全部可及收益, DUAL ≈ DCM, 则确认平台并关闭 decoder-access 轴。
    这是 {qla,qia}×{cluster KV} 2×2 矩阵最后一个缺格, 结构对称、无新模块、零参数。
  - 变体2 M135-DCM-S42: DCM seed=42 对照。
    因果假设: CTF-HCG 跨 seed 脆弱 (s42=0.4963, s123=0.494), MLay/MFP 的 seed 对照
    在跑; DCM 作为当前 decoder-access 轴最优机制, 若 seed42 亦大幅回退则 0.5010
    同样是 seed-1999 红利, 直接影响该轴是否值得继续投入与论文能否声称。此实验补上
    {DCM}×{seed} 缺失的稳健性证据, 与 M120/M122 (MLay seed) 同型。
  - 与 banned[]/constraints 校验:
    M134-DUAL: 非 gate/非 langroute/非 attnpool/非 residual/非 true_route/非 3-6层注入;
      零新增参数 (复用 qia/qla 已有注意力, 仅 KV concat); 不改变数值分布; 无新超参;
      FLOPs 与 DCM 同量级。M135-DCM-S42: 纯 seed 变更 (继承 M90/M91/M120 等 seed
      对照先例), 非调参。
  - 条件独立性: 两变体均**不依赖 MFP seed 结果** (M131/M132 撤回不影响) 且**不依赖
    DCMV 结果** (DUAL 即使 DCMV 中性也可判定 qla 是否已饱和; DCM-S42 纯对照)。
    保持队列深度, 为 MFP 证伪后的队列收缩提供缓冲。
  - 排除方向: 不设计新 seed 变体以外的新超参扫描 (Phase1 禁止调参); 不设计
    gate 系/新 token 质量机制 (轴证伪); 不设计 encoder-side 新 token 质量
    (CCL/CGA/BCF/SRL/MEMBANK 全灭); 不设计 DCM×DCA (DCA 已淘汰);
    不设计 3/4/6 层注入 (banned)。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260824-071344.md
================================================================================
