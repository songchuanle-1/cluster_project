================================================================================
  Motivation Review — cluster_project
  2026-07-20 13:45:00
================================================================================

## 1. Goal
  Target mIoU ≥ 0.51, champion 0.5012, gap −0.0088.
  机制: 多尺度 cluster context (routing 已证伪). context✓(A1−A0=0.0118).

## 2. Story Status
  | 假设 | 状态 | 证据 |
  |------|------|------|
  | H1 多尺度context是主要收益 | confirmed | A1=0.5012, routing丢弃仍最优 |
  | H3 routing独立贡献有限 | confirmed | A3=0.4468<A1, routing反害 |
  | H4 detail-preserving update | partial | D1-detail=0.5003≈champion, 有效但未超 |
  | query信息能否提升context | 未验证 | M1-QGC waiting |

## 3. Experiment Assessment
  | Exp | mIoU | 对故事贡献 |
  |-----|------|-----------|
  | D1-detail | 0.5003 | detail message ≈ context, 接近champion ✓ |
  | E4-residual+detail | 0.4944(running) | residual对detail有害 ✗ |
  | M1-QGC | waiting | query-gated context, 冲0.5012 |
  | A4-shuffle | running | routing控制组 |

## 4. Gap
  - 已知: context✓, routing✗, detail≈context, residual✗
  - 缺: query信息注入context的效果(M1待跑); 尺度融合是否query-aware; cluster token质量是否瓶颈
  - depth=1(M1) < 可用卡2+1=3 → 触发设计, 补2个

## 5. Design Rationale
  - M6-QSF: champion level_gate 用[point,global_mean]选尺度; 加 query_mean 让尺度融合随query变. 与M1(QGC gate cluster token)互补, 都注入query但位置不同(尺度 vs token).
  - M16-CSR: 各尺度 cluster token 过1层self-attn精炼再回写. 测试 cluster token 质量是否限制 message. (区别于C3-refine: C3在gather/noroute变体上0.4931; M16在champion Lite/context上)
================================================================================
