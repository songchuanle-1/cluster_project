# 模型变体与实验结果总结

本文档根据项目代码、配置、`Cluster/logs_analysis` 汇总表以及 `Cluster_checkpoints` 训练日志整理。当前项目主体是 BQNet 风格的 3D Referring Expression Segmentation，实验数据为 ScanRefer，核心指标使用日志中的验证集 `mIoU`。

## 1. 项目主线

原始 `model_base1` 是当前 base1 基线，包含语言-实例交互、query 解码、iterative prediction、contrastive align loss 等模块，但没有显式的 cluster attention 增强。你的改进主线是在 base1 的 encoder 交互过程中加入层次化点云 cluster token，让点特征在与语言交互前后获得更强的几何上下文。

当前最主要的一条路线是：

```text
model_base1
  -> quard2 / cluster attention
  -> c2f / coarse-to-fine 级联路由
  -> c2f_enc / 嵌入 encoder layer
  -> c2f_enc_lite / 轻量化稳定版本
  -> posA / 调整 cluster attention 注入位置
```

## 2. 核心方法

### 2.1 层次化 cluster token

`PointCloudPartitioner` 使用 FPS 对点云做多层几何划分，默认层级为 `[256, 64, 8]`。每一层记录点或子簇到父簇的映射，并用 `scatter_mean` 聚合当前特征形成 cluster token。

### 2.2 Coarse-to-Fine Cluster Attention

`C2F_ClusterAttn_Lite` 从最粗层开始做 query 到 cluster 的 attention，然后只沿着被选中的父簇展开子簇候选，形成粗到细的路由。最终把不同尺度的 cluster message 回读到 point feature，再用 per-point level gate 融合多尺度消息。

### 2.3 lite 版的关键稳定化

`model_base1_quard2_c2f_enc_lite` 相比早期 `c2f_enc` 做了三点关键改动：

- 去掉 `_route_points` 中的 `N x Q` 全注意力回读，改成基于 `cluster_ids` 的直接 gather，复杂度更接近 `O(N)`。
- cluster attention 只增强 `inst_feats`，不再直接改 `query`，减少和 decoder query 更新路径的冲突。
- 只在 encoder 后若干层启用 cluster attention，默认 `cluster_att_num_layers=2`，并用 sigmoid gate 控制注入强度。

## 3. 主要变体说明

| 变体 | 改动点 | 直观目的 |
|---|---|---|
| `model_base1` | base1 基线，无新增 cluster attention | 对照基线 |
| `model_base1_quard2_nomask` | 并行多尺度 cluster，外挂式增强，无 mask 路由 | 验证 cluster token 是否整体有益 |
| `model_base1_quard2_c2f_enc` | C2F cluster attention 嵌入 encoder，早期较重版本 | 把层次聚类上下文放进语言-实例交互流程 |
| `model_base1_quard2_c2f_pq` | C2F + per-query 独立路由 | 让不同 query 选择不同 cluster 路径 |
| `model_base1_quard2_c2f_enc_lite` | 直接 gather、不改 query、后 2 层启用 | 当前稳定主线 |
| `model_base1_quard2_c2f_enc_lite_l1/l3/l4` | 改变 cluster attention 启用层数 | 消融注入深度 |
| `model_base1_quard2_c2f_enc_lite_init0` | 调整 cluster gate 初始化 | 消融初始注入强度 |
| `model_base1_quard2_c2f_enc_lite_noroute` | 去掉或弱化 C2F routing 约束 | 判断层次路由是否必要 |
| `model_base1_quard2_c2f_enc_lite_posA` | 注入位置从 `lla -> cluster -> lia -> ila` 改为 `lla -> lia -> cluster -> ila` | 先用 inst 信息更新语言，再基于更语言化的 inst feature 做 cluster 增强 |
| `model_base1_quard2_c2f_enc_lite_posB/posC` | 其他注入位置变体 | 消融 cluster attention 放置点 |
| `model_base1_quard2_c2f_enc_lite_cag` | per-layer scalar gate 增强为 per-point content-adaptive gate | 不同点自适应接收不同强度 cluster 信息 |
| `model_base1_quard2_c2f_enc_lite_cfe` | cluster feature/enhancement 相关探索 | 探索额外 cluster feature 交互 |
| `model_base1_quard2_c2f_enc_lite_agg` | lvl0 使用 MLP 学习点权重做自适应加权聚合 | 替代均值聚合，提升 cluster token 表达 |
| `model_base1_quard2_c2f_enc_lite_qcond` | query-conditioned cluster aggregation | 让 cluster token 按 query 语义重新聚合 |
| `model_base1_quard2_c2f_enc_lite_attnpool` | attention pooling 替代 lvl0 `scatter_mean` | 让簇内重要点获得更高权重 |
| `model_base1_quard2_c2f_enc_lite_prune` | 动态 cluster token 剪枝 | 降低 cluster attention 计算量 |

## 4. 有效 mIoU 结果

下面结果来自 `Cluster_checkpoints/*/*.log` 中可解析到验证 `mIoU` 的日志。部分实验没有跑满 50 epoch，因此同时列出实际 epoch 数。

| 排名 | 模型 | Run | Best mIoU | Best Epoch | Final mIoU | Epochs |
|---:|---|---|---:|---:|---:|---:|
| 1 | `model_base1_quard2_c2f_enc_lite_posA` | `20260708_180536` | **0.500940** | 15 | 0.491166 | 24 |
| 2 | `model_base1_quard2_c2f_enc_lite_l1` | `20260706_075740` | 0.500636 | 21 | 0.488952 | 26 |
| 3 | `model_base1_quard2_nomask` | `20260704_130243` | 0.499740 | 16 | **0.496088** | 20 |
| 4 | `model_base1_quard2_c2f_enc_lite` | `20260703_150030` | 0.499236 | 13 | 0.487588 | 22 |
| 5 | `model_base1_quard2_c2f_enc_lite_l3` | `20260705_021243` | 0.498062 | 18 | 0.491637 | 24 |
| 6 | `model_base1_quard2_c2f_enc_lite_noroute` | `20260708_115011` | 0.497197 | 17 | 0.481237 | 27 |
| 7 | `model_base1_quard2_c2f_enc_lite_cag` | `20260707_072811` | 0.496191 | 13 | 0.495356 | 18 |
| 8 | `model_base1_quard2_c2f_enc_lite_posB` | `20260708_221940` | 0.495317 | 13 | 0.488426 | 21 |
| 9 | `model_base1_quard2_c2f_enc_lite_posC` | `20260709_073810` | 0.495154 | 13 | 0.493695 | 16 |
| 10 | `model_base1_quard2_c2f_enc_lite_init0` | `20260706_083447` | 0.494883 | 19 | 0.489002 | 23 |
| 11 | `model_base1_quard2_c2f_enc_lite_l4` | `20260705_023517` | 0.493136 | 20 | 0.488858 | 25 |
| 12 | `model_base1` | `20260627_174353` | 0.489449 | 15 | 0.473846 | 30 |
| 13 | `model_base1_quard2_c2f_enc` | `20260703_094308` | 0.489093 | 12 | 0.481167 | 15 |
| 14 | `model_base1_quard2_c2f_pq` | `20260704_103140` | 0.486376 | 13 | 0.480524 | 14 |

## 5. 关键对比结论

### 5.1 cluster 主线确实有效

`model_base1` 的 best mIoU 是 `0.489449`。`c2f_enc_lite` 达到 `0.499236`，提升约 `+0.00979`。这说明在 base1 上加入层次 cluster context 是有收益的。

### 5.2 posA 是当前最优方向

`posA` 的 best mIoU 为 `0.500940`，比 `c2f_enc_lite` 再提升约 `+0.00170`，比 base1 提升约 `+0.01149`。它的核心变化不是增加参数，而是调整注入顺序：

```text
lite: lla -> cluster -> lia -> ila -> FFN
posA: lla -> lia -> cluster -> ila -> FFN
```

这支持一个判断：cluster attention 更适合放在语言信息已经参与 inst/lang 交互之后，而不是过早对较原始的 `inst_feats` 做聚类增强。

### 5.3 注入层数不是越多越好

`lite_l1` 也达到 `0.500636`，非常接近 posA；`lite_l3` 为 `0.498062`，`lite_l4` 为 `0.493136`。这说明 cluster context 适合在后层、少量、受 gate 控制地注入。过多层使用可能带来噪声或干扰 decoder 原本的 query refinement。

### 5.4 routing 有帮助，但收益不绝对

`noroute` 最好为 `0.497197`，低于 `lite` 的 `0.499236` 和 `posA` 的 `0.500940`。这说明 C2F routing 不是唯一收益来源，cluster token 本身已经有用，但层次路由能进一步提升精度和稳定性。

### 5.5 更复杂的聚合目前成本偏高

`qcond`、`agg`、`attnpool` 这类变体的动机都合理，但从现有日志看成本明显上升。`attnpool` 已有 7 epoch 验证，best mIoU 为 `0.471145`，尚未体现收益；`qcond` 和 `agg` 最新日志只有 profile 和训练片段，未解析到验证 mIoU，不能和完整实验直接比较。

## 6. 成本与速度

| 模型 | Total Params | Trainable Params | FLOPs | Inference Time |
|---|---:|---:|---:|---:|
| `c2f_enc_lite` | 155.91 M | 31.26 M | 9.70 G | 122.8 ms |
| `posA` | 155.91 M | 31.26 M | 9.70 G | 80.2 ms |
| `noroute` | 155.71 M | 31.06 M | 9.70 G | 90.1 ms |
| `agg` | 156.00 M | 31.36 M | 10.02 G | 222.7 ms |
| `qcond` | 156.10 M | 31.46 M | 11.04 G | 285.9 ms |
| `attnpool` | 156.50 M | 31.85 M | 9.98 G | 235.4 ms |

注：profile 速度来自对应日志中的单次环境统计，不应视为严格 benchmark，但足以说明复杂聚合变体带来了显著延迟。

## 7. 当前推荐结论

当前最值得保留为主模型的是 `model_base1_quard2_c2f_enc_lite_posA`。它不增加额外参数量和 FLOPs，却取得了目前最高 best mIoU。若需要一个更稳的备选，可以同时保留 `lite_l1`，因为它 best mIoU 很接近 posA，说明“后层少量注入”是稳健信号。

下一步建议优先围绕 posA 做小范围消融：

- 固定 posA 注入位置，重新跑完整 50 epoch，确认 best mIoU 是否稳定超过 `0.500`。
- 对 posA 做 `cluster_att_num_layers=1/2/3` 的严格对照，判断 `lite_l1` 的高分是否来自更少注入层。
- 暂缓 `qcond/agg/attnpool` 这类高成本聚合，除非它们完整训练后能明显超过 posA。
- 如果目标是论文式叙述，可以把主贡献表述为“语言引导后的层次 cluster context refinement”，而不是单纯“加了 cluster attention”。

## 8. 文件索引

- 主线配置：`Cluster/configs/Quard/model_base1_quard2_c2f_enc_lite.yaml`
- 当前最佳配置：`Cluster/configs/Quard/model_base1_quard2_c2f_enc_lite_posA.yaml`
- 主线实现：`Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite/`
- 当前最佳实现：`Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA/`
- 日志汇总：`Cluster/logs_analysis/summary_stats.csv`
- 逐 epoch 汇总：`Cluster/logs_analysis/epoch_results.csv`
- 最佳模型日志：`Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA/20260708_180536/20260708_180536.log`
