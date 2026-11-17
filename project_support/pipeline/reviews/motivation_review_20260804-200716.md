================================================================================
  Motivation Review — cluster_project
  2026-08-04 20:07:16
================================================================================

## 1. Goal
  - goal.json description: cluster 多尺度 cluster context 机制 — cluster bank 聚合点云
    特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。注: 原'聚类
    路由'假设已被证伪(routing 生效反降点), 收益来自 context 而非 routing。目标 mIoU ≥ 0.51。
  - Target: mIoU ≥ 0.5100 | Champion: posA_l1 (DRP) 0.5012 | Gap: +0.0088 | Phase 1 (NOT YET)

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 回写有效 | confirmed | DRP 0.5012 vs base 0.4894 (γ=+0.0118) | 需消融哪些设计必要 |
  | routing 生效反降点 | confirmed(证伪原假设) | TrueRoute 0.4468 vs DRP 0.5012 (γ=-0.0544) | — |
  | readback expressiveness 不是瓶颈 | confirmed | BIL 0.4919 / NLR 0.4948 / FILM 0.4936 / FLM 0.4865 全 < champion | — |
  | token 质量不是瓶颈 | confirmed | CTF 0.4995 → 结论指向 readback/融合机制 | — |
  | token 多样性(正交正则)有帮助 | 未验证(被 bug 污染) | M17-ORT 0.5005 因 ORT 梯度断流无效; M56/M57 同 | **需修复后重测** |
  | 融合机制顺序依赖(粗→细) | 待测 | M61-SCT 已入队 waiting | running 队列消化中 |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | DRP (champion) | 0.5012 | 直接验证 context 回写 | 确认核心假设 ✓ |
  | M17-ORT | 0.5005 | 验证 token 正交正则 | **无效**: orth 梯度断流, 假说未经验证 |
  | M56-DOT | 无 mIoU | DRP+ORT 组合 | 无效: dec.py 不收集 drp_ort + 梯度断流 + GPU7 过载进程消失 |
  | M57-DET-ORT | 无 mIoU | ORT+detail 组合 | 无效: 同上 |
  | M50-DGC | 0.4913 (running) | diff-gated context | running, no_impr 9/10 近早停, 低于 champion |
  | M51-DCA | 0.4893 (running) | dual pooling | running, no_impr 7/10, 低于 champion |
  | M52/M53/M54 | running ep1 | CCR/VAC/SAC | 刚启动, 无数据 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context 回写有效、routing 有害、expressiveness 非瓶颈、token 质量非瓶颈。
  - 未验证: **token 多样性(正交正则)到底有没有独立收益** — 这是唯一一个"设计过、声称有效、
    但因实现 bug 从未真正生效"的假设。M17-ORT 的 0.5005 只能证明 ORT 类结构本身不比 DRP
    差, 不能证明正交正则有效。
  - 矛盾/疑问: M17-ORT(0.5005) vs DRP(0.5012) 差 0.0007, 若 ORT 正则真无效, 说明 ort 类
    结构与 drp 类行为等价; 若有效, 需真梯度重测才能判断方向。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M62-ORTG = DRP + 真梯度 ORT:
    - 填补缺口: 修复 ORT 梯度断流 bug (hier_postprocess 中 .detach().item() 断开图 +
      dec.py 不收集 drp_ort 模式), 使 orth 正则真正对模型施加梯度。
    - 变体角色: 验证假设 "cluster token 正交正则 → 减少 token 冗余 → context 回写信息
      多样性更高 → 定位更准"。
    - 对照基线: DRP champion 0.5012。M62-ORTG 若 > 0.5012 → token 多样性有独立收益;
      若 ≈ 0.5012 → 正则无益, 排除该方向。
    - 预期结果对故事线推进: 无论结果如何, "token 多样性" 假说从"未验证"变为"确认/证伪",
      故事线的 token 质量/多样性轴闭合。

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260804-200716.md (M62-ORTG 单变体)
================================================================================
