================================================================================
  Motivation Review — cluster_project
  2026-07-23 02:03:01
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100 | Champion: model_base1_quard2_c2f_enc_lite_posA_l1 = 0.5012 | Gap: +0.0088 | Phase: 1 (NOT YET)
  - Description: 多尺度 cluster context 机制 — cluster bank 聚合点云特征 → cluster_attn 把多尺度 context 回写更新 inst_feats → 提升定位精度

## 2. Story Status（故事线状态）
  | 假设 | 状态 | 证据 | 缺口 |
  |------|------|------|------|
  | 多尺度 context 有效 | confirmed | champion 0.5012 vs base 0.4894 (γ=+0.0118) | 聚合函数缺消融 |
  | 三个尺度均必要 | confirmed | M18(fine+medium)=0.4933, M19(fine+coarse)=0.4944 < champion 0.5012 | — |
  | detail 独立有效 | confirmed | D1-detail=0.5003, γ=+0.0109 vs baseline | rerun M20-DET 确认 |
  | routing 有害 | confirmed | A3=true_route 0.4468, A4-shuffle 0.4941 | — |
  | context+detail 互补 | testing | M21-HYB waiting | 待实验结果 |
  | cross-scale attn 有效 | testing | M22-XCA waiting | 待实验结果 |
  | orthogonality 正则有效 | testing | M17-ORT running (ep4, 0.3982) | 待收敛 |
  | refine/CSR/QGC/QSF 有效 | 证伪 | 均 < baseline | — |
  | 聚合函数影响 context 质量 | unknown | 未测试 | **本次设计** |

## 3. Experiment Assessment（已有实验的动机视角评估）
  | Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
  |------------|------|-------------|-------------|
  | posA_l1 (champion) | 0.5012 | context-only, 3-scale cluster bank | 核心假设验证 ✓ |
  | D1-detail | 0.5003 | detail message, 偏离 cluster 的信息 | 第二有效信号 ✓ |
  | M18-S2FM | 0.4933 | fine+medium 2-scale | 证明 coarse 必要 ✓ |
  | M19-S2FC | 0.4944 | fine+coarse 2-scale | 证明 medium 必要 ✓ |
  | M1-QGC | 0.4939 | query-gated context | 证伪 query gate ✗ |
  | A4-shuffle | 0.4941 | shuffle routing control | 证伪结构注入 ✗ |
  | M16-CSR | 0.4875 | cluster self-refine | 证伪 refine ✗ |
  | M6-QSF | 0.4866 | query-selective fusion | 证伪 query fusion ✗ |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: 多尺度 context 有效, 3-scale 均必要, detail 独立有效
  - 未验证: 
    1. cluster bank 聚合函数 (mean vs max) 对 context 质量的影响 ← **本次填补**
    2. context+detail 能否互补 (M21-HYB 测试中)
    3. cross-scale 交互能否提升 (M22-XCA 测试中)
    4. orthogonality 正则效果 (M17-ORT 训练中)
  - 矛盾/疑问: champion 0.5012 和 detail 0.5003 接近但未超越, 需要新机制突破

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M23-CMX (max-pool cluster aggregation):
    * 填补缺口: cluster bank 当前使用 mean pooling 聚合簇内特征, max pooling 可能保留更显著的特征信号
    * 预期: 若 max > mean, 则新的聚合函数可结合 context/detail 机制
    * 风险: max pooling 对噪声敏感, 可能不如 mean 稳健
    * 配置驱动: 仅新增 cluster_pool_type 参数, 无需新 model 包

## 6. Next Batch
  → 见 pipeline/designs/exp_design_20260723-020301.md
================================================================================
