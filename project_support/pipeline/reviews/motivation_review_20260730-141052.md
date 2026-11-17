================================================================================
  Motivation Review — cluster_project
  2026-07-30 14:03:00
================================================================================

## 1. Goal
  - Target: mIoU ≥ 0.5100
  - Champion: model_base1_quard2_c2f_enc_lite_posA_l1 (mIoU=0.5012, gap=+0.0088)
  - Tied: M32-DRP=0.5012 (dual residual path, code cleanup — proves routing dead code)
  - Description: "多尺度 cluster context 机制 — cluster bank 聚合点云特征→cluster_attn 把多尺度 context 回写更新 inst_feats→提升定位精度。routing 已被证伪，收益来自 context 而非 routing"

## 2. Story Status（故事线状态）
| 假设 | 状态 | 证据 | 缺口 |
|------|------|------|------|
| 多尺度 cluster context 提升特征表达 | confirmed | Lite+L1=0.5012 vs base=0.4894 (γ=+0.0118) | 天花板 0.5012 未被任何变体突破 |
| Routing 路由有独立收益 | falsified | TrueRoute=0.4468, DRP=0.5012(=routing removed) | 证伪完毕 |
| L1 正则化稳定训练 | confirmed | +L1: 0.5006→0.5012 (γ=+0.0006, small) | 收益微小，可视为稳定器 |
| Cluster token quality 是关键瓶颈 | testing | C2C(within-scale attn), CTF(cluster FFN), CLN(LayerNorm) 正在跑 | 等待结果 |
| Aggregation 质量影响 token quality | testing | WCA(weighted aggregation) 等待中 | 等待结果 |
| Readback/injection 机制影响融合质量 | testing | SWI(sigmoid injection) 正在跑 | 等待结果 |
| Gate/conditioning/modulation 系无效 | falsified | cag=0.4962, cfe=0.4901, layerscale=0.4921, flm=0.4865 | 四连败，方向关闭 |
| Scale 间信息交互能突破 ceiling | untested | C2C 只做 scale 内，未做 scale 间 | 核心缺口 |

## 3. Experiment Assessment（动机视角评估）
| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|------------|------|-------------|-------------|
| Lite+L1 (champion) | 0.5012 | 直接证明 context 有效 | 确立 baseline ✓ |
| M32-DRP | 0.5012 | 证明 routing 代码可安全删除 | 简化架构、消除噪声 ✓ |
| M17-ORT | 0.5005 | 正交约束有微弱正收益 | 可选的辅助 loss |
| D1-detail | 0.5003 | detail loss 接近 champion | 可选的辅助 loss |
| M38-FLM | 0.4865 | 证明 modulation/gate 方向死胡同 | 关闭方向 ✓ |
| M26-ORT-HYB | 0.4998 | ORT hybrid 接近 champion | ORT 方向确认有效 |
| M22-XCA | 0.4954 | cross-scale 之前尝试过但方向不同(attention-based injection) | ⚠ XCA 失败但机制不同，不排除 cross-scale |
| M16-CSR | 0.4875 | cluster self-refine 失败 | self-refine 无效 |

## 4. Gap Analysis（Q1: 故事缺什么）
  - 已验证: context injection 有效 (γ=+0.0118), routing 无效, gate 系无效
  - 未验证: **scale 间信息交互能否打破 0.5012 天花板**
  - 矛盾/疑问: M22-XCA(0.4954, cross-scale attention before readback) 曾失败 — 但 XCA 是把 cross-scale 融合放在 readback 阶段(改了 inject 方式), CSF 是放在 cluster token 预处理阶段(token quality 方向)
  - 关键洞察: 当前 cluster token 在各 scale 独立计算→独立 readback→点级 softmax 融合. Scale 间的互补信息(粗=全局语义, 细=局部几何)从未在 token 级交互, 只在点级线性混合. 这限制了 token 的表达能力

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
  - M44-CSF (Cross-Scale Fusion): 在 cluster token 级别做 scale 间 cross-attention, 让粗/细 tokens 互相补充信息后再 readback
    - 填补缺口: "scale 间信息交互"
    - 与 XCA 的区别: XCA 在 readback 路径上混合 scale 信息(改 inject), CSF 在 token preprocessing 阶段融合(改 token quality). 不同机制
    - 预期: 如果成功(γ>0), 证明 scale 间交互有价值 → 可进一步探索更多 scale 间机制
    - 如果失败(γ≤0): 排除 scale 间 attention 方向 → 聚焦其他突破点

## 6. Next Batch
  → 见 pipeline/designs/exp_design_${ts}.md
================================================================================
