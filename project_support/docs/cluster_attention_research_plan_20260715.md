# 高效层次 Cluster Context 与有效路由研究计划（2026-07-15）

> 项目：ScanRefer 3D Referring Expression Segmentation  
> 基线：`model_base1`  
> 数据来源：`Checkpoints/server_4` 中 28 个具有有效验证 mIoU 的模型日志，以及 `Cluster/logs_analysis/summary_stats.csv`  
> 核心原则：以收敛平台、计算成本和机制可证性共同筛选模型，不再仅按单次 Best mIoU 排名。

## 1. 当前实验事实

### 1.1 代表结果

| 模型 | Best mIoU | Best Epoch | Final mIoU | FLOPs | 角色 |
|---|---:|---:|---:|---:|---|
| `model_base1` | 0.489449 | 15 | 0.473846 | 约 9.5G | 无 cluster 基线 |
| `c2f_enc_lite_posA` | **0.500940** | 15 | 0.491166 | 9.70G | 当前最高单点 |
| `c2f_enc_lite_l1` | 0.500636 | 21 | 0.488952 | **9.59G** | 当前效率最优候选 |
| `quard2_nomask` | 0.499740 | 16 | **0.496088** | **19.91G** | 稳定但计算昂贵的上限对照 |
| `c2f_enc_lite` | 0.499236 | 13 | 0.487588 | 9.70G | 后两层轻量回写 |
| `c2f_enc_lite_noroute` | 0.497197 | 17 | 0.481237 | 9.70G | 路由消融，但与 L1/PosA 非严格同构 |
| `gbcr_langc2f_scale_l1` | 0.496725 | 16 | 0.487680 | 9.60G | GBCR 当前最高 |
| `gbcr_adaptive_l1` | 0.496102 | 17 | 0.486771 | 9.55G | 纯几何有效路由基准 |
| `gbcr_langroute_l1` | 0.495638 | 15 | 0.486675 | 9.55G | 语言粗路由未提升 |
| `gbcr_langc2f_l1` | 0.495042 | 15 | 0.485513 | 9.55G | 父上下文条件化未提升 |

### 1.2 已经可以支持的结论

1. 在 `model_base1` 上增加后层多尺度 cluster context，能够带来约 `+0.010~+0.0115` mIoU。
2. 最后 1～2 个 encoder layer 注入优于更早、更频繁的注入；3/4 层重复注入开始退化。
3. `Nomask` 的稳定平台说明多尺度 cluster token 本身有效，但其 FLOPs 约为 Lite 的 2 倍，不适合作为最终主模型。
4. `PosA` 和 `Lite-L1` 在约 9.6～9.7G FLOPs 下取得最高指标，是下一阶段的合理起点。
5. GBCR Adaptive 证明了固定预算、local-preserving 的纯几何路由可以低成本获得正收益，但仍落后 PosA 约 0.0048 mIoU。
6. LangRoute、LangC2F 和 Scale 没有形成超过 `+0.002` 的可靠增益，不应继续优先叠加语言路由复杂度。

### 1.3 尚不能支持的结论

旧 C2F Lite 计算了 query-to-cluster top-k 路由，但最终 point message 主要通过 cluster ID 直接读取预聚合 token，路由产生的索引没有严格决定最终写回内容。因此现有结果不能证明：

- proposal-query routing 是性能提升来源；
- coarse-to-fine top-k 比无路由多尺度 context 更好；
- PosA 的提升来自 routing，而不是注入位置和后层 refinement。

## 2. 新阶段研究目标

### 2.1 主目标

在不超过 `10.0G` FLOPs、不过度增加参数和显存的前提下，回答两个问题：

1. **性能问题**：能否稳定达到或超过 `0.501` mIoU？
2. **机制问题**：收益来自多尺度 context、有效 coarse-to-fine routing，还是 detail-preserving residual？

### 2.2 约束

- 主模型 FLOPs 上限：`10.0G`。
- Cluster 模块只更新 `inst_feats`，不直接修改 decoder query。
- 默认只在最后一个 encoder layer 注入；只有通过 L1 筛选后才测试最后两层。
- 新的 routing 必须真实影响最终 point message，不能只计算 top-k 后仍回读全部 cluster token。
- 不新增 `N×Q` 或 `N²` 级注意力。
- 第一阶段不继续增加语言路由、attention pooling、query-conditioned aggregation 或动态剪枝。

## 3. 核心假设

### H1：后层单次多尺度 context 是主要收益来源

`Lite-L1=0.500636` 与 `PosA=0.500940` 非常接近，同时 L3/L4 退化。预期最后一个 encoder layer 的一次 context refinement 已能获得大部分收益。

### H2：PosA 位置与 L1 深度可以组合

当前 PosA 使用后两层，L1 使用原 Lite 注入位置。两项最佳因素尚未做严格交叉实验。预期 `PosA + last-1` 能保持或提高精度，并减少重复注入造成的过平滑。

### H3：旧路由的独立贡献有限

Nomask 和 Noroute 仍取得较高结果，说明 cluster context 比路由本身更确定。只有在同位置、同层数、同融合方式下，真实路由版本超过无路由版本，才能证明 routing 有效。

### H4：Detail-preserving update 可能优于直接 context 相加

GBCR Adaptive 学到负 LayerScale，提示模型倾向于 `point-context` 的 detail sharpening。将这一更新形式迁移到高性能 Lite-L1/PosA 路线，可能兼顾多尺度上下文与边界细节。

## 4. 实验阶段

## 4.1 阶段 A：建立严格、低成本的机制对照

所有模型统一为：PosA 注入位置、最后 1 层、相同 cluster bank、相同 gate 初始化、相同训练协议。

| 编号 | 建议模型名 | 结构 | 回答的问题 |
|---|---|---|---|
| A0 | `model_base1` | 无 cluster | 基线 |
| A1 | `model_base1_cluster_context_posA_l1` | 256/64/8 mean context，直接按 ID 回写，无 routing | 单次多尺度 context 是否足够 |
| A2 | `model_base1_cluster_context_single_posA_l1` | 只使用 256、64、8 中的单一尺度 | 哪个尺度贡献最大 |
| A3 | `model_base1_cluster_route_posA_l1` | 真实 8→64→256 top-k 路由，路由索引决定最终候选和值 | routing 是否有独立收益 |
| A4 | `model_base1_cluster_route_shuffle_posA_l1` | 保持候选数量但随机/打乱 route | 收益来自内容路由还是稀疏正则化 |

A3 必须满足：

```text
coarse top-k
 -> 展开对应 middle children
 -> middle top-k
 -> 展开对应 fine children
 -> fine attention context
 -> 仅将被路由的 context 写回相应 point
```

若最终 message 与 route index 无关，则该实验无效。

### 阶段 A 的判定

- `A1 - A0 >= 0.005`：确认低成本多尺度 context 有效。
- `A3 - A1 >= 0.002`：routing 可进入主模型。
- `A3` 与 `A1` 差异小于 `0.002`：主模型保留更简单的 A1。
- `A4 ≈ A3`：说明内容路由没有工作，不能声称 semantic routing。

## 4.2 阶段 B：性能主线

第一优先新变体：

```text
model_base1_quard2_c2f_enc_lite_posA_l1
```

它只组合已经分别验证有效的两个因素：

```text
PosA: LLA -> LIA -> Cluster -> ILA -> FFN
+
L1: 仅最后一个 encoder layer 注入
```

不增加新 attention、聚合器或语言路由，目标 FLOPs 不超过 `9.7G`。

后续仅在阶段 A 最优结构上测试：

| 编号 | 建议模型名 | 唯一改动 | 目的 |
|---|---|---|---|
| B1 | `..._posA_l1` | PosA + last-1 | 当前首选性能模型 |
| B2 | `..._posA_l1_layerscale` | sigmoid gate 改为小值 signed LayerScale | 允许模型学习增强或抑制 context |
| B3 | `..._posA_l1_detail` | message=`LN(point-context)` | 验证 detail sharpening |
| B4 | `..._posA_l1_adaptive_scale` | 低维尺度选择，只融合 256/64/8 context | 点级选择尺度是否有效 |

一次只引入一个变化，不把 signed scale、detail message 和 adaptive scale 同时加入。

### 阶段 B 的停止规则

- Best 提升小于 `0.002` 且收敛平台没有提高：停止该分支。
- FLOPs 超过 `10.0G`：不进入主模型候选。
- 峰值显存增加超过 Lite-L1 的 15%：必须证明至少 `+0.003` mIoU 才保留。
- 仅单个 epoch 高、Top-5/收敛窗口不提高：视为不稳定，不继续扩展。

## 4.3 阶段 C：稳定性验证

只选择阶段 A/B 中最多两个候选，与 Baseline 一起进行多 seed：

```text
seed = 1999, 2026, 3407
```

建议最终对照：

```text
model_base1
model_base1_quard2_c2f_enc_lite_l1
model_base1_quard2_c2f_enc_lite_posA_l1
阶段 A/B 最优的真实 routing 或 detail 版本
```

报告：

- Best mIoU 的 mean ± std；
- 收敛后最后 5 次验证均值的 mean ± std；
- Acc@0.25、Acc@0.50、spmIoU；
- 参数量、FLOPs、峰值显存和推理延迟；
- 每个 seed 的完整曲线，不只报告最优 seed。

## 5. 收敛与统计协议

现有实验均已训练到收敛，后续不强制以“必须 50 epoch”作为完成标准。采用统一收敛规则：

```text
最近 5 次验证的均值不再提升超过 0.001
且连续 5 次验证没有刷新 Best
```

为保证公平：

1. 所有对照使用相同 seed、数据增强、batch size、优化器和 scheduler。
2. 首轮结构筛选使用 seed 1999；入选后再跑另外两个 seed。
3. 保存 Best、最后一次验证和收敛窗口均值。
4. `Avg mIoU` 不作为主要指标，因为它混入了早期未收敛阶段。
5. `train.epochs=50` 与 `lr_scheduler.max_iters=70` 的不一致暂时保持一致用于旧结果对照；新一轮统一实验开始前再整体修正，不能只改某个变体。

## 6. 效率测量协议

现有日志延迟受 GPU 并发和输入规模影响较大，后续统一测量：

```text
batch size = 1
固定同一验证场景集合
warmup = 20
repeat = 100
报告 median / P90
测量前确认 GPU 无其他进程
```

同时记录：

- Total/trainable parameters；
- profiler FLOPs；
- `torch.cuda.max_memory_allocated()`；
- 单场景端到端延迟；
- cluster 模块单独延迟。

FLOPs 报告必须注明可能漏计 FPS、`cdist`、scatter、gather 和 Python candidate packing。因此最终效率结论以实测延迟和显存为主，FLOPs 为辅。

## 7. Routing 机制诊断

若 A3/B 系列保留 routing，必须同步记录：

1. 8/64/256 层 routing recall@k；
2. coarse route 被语言或内容分支改变的比例；
3. local 与 routed candidate 的命中率及最终 attention 权重；
4. 各层有效候选数、padding 比例和 attention entropy；
5. 目标点、背景点、边界点的 message norm；
6. refinement 前后 cluster 内/cluster 间 cosine similarity；
7. 小/中/大物体和 spatial-relation 子集指标。

只有 route recall 和最终指标同时改善，才能将贡献表述为 coarse-to-fine cluster routing。

## 8. 暂停方向

当前暂停：

- `Nomask` 继续扩展：19.91G FLOPs，不符合效率目标；
- LangRoute/LangC2F/Scale 继续叠加：尚无可靠增益；
- AttnPool/QCond/Agg/Multi：计算或实现复杂度上升，未产生有效优势；
- Prune：当前 profile 延迟异常，应先单独修复和 benchmark；
- 3/4/6 层 cluster 注入：现有结果已显示重复注入退化；
- 新增大型 Q/K/V/O 投影：与轻量目标冲突。

Nomask 只保留为“高计算量无路由多尺度上限”对照，不作为主模型。

## 9. 推荐执行顺序

```text
Step 1  实现并检查 PosA-L1，确认 FLOPs <= 9.7G
Step 2  建立严格同构的 Context-L1 与 TrueRoute-L1
Step 3  seed 1999 跑 A1/A3，按 +0.002 阈值决定是否保留 routing
Step 4  在胜者上测试 signed LayerScale 与 detail message
Step 5  选最多两个候选跑 2026、3407 两个新 seed
Step 6  统一测量 FLOPs、峰值显存、median/P90 延迟
Step 7  根据证据确定论文表述和最终模型
```

当前下一次最推荐运行的**新变体**是：

```text
model_base1_quard2_c2f_enc_lite_posA_l1
```

原因是它组合当前最高指标的注入位置与当前最高效率的注入深度，结构变化最小、因果关系清晰，并预计保持在约 9.6～9.7G FLOPs。

## 10. 最终论文表述边界

根据实验结果选择准确表述：

- 只有 A1/B1 有效：`late-stage multi-scale cluster context refinement`；
- A3 稳定超过 A1 且 route recall 改善：`geometry-aware coarse-to-fine cluster routing`；
- B3 额外有效：`detail-preserving hierarchical cluster refinement`；
- 语言路由没有稳定收益：不把 language-conditioned routing 写成主要贡献。

最终目标不是继续增加变体数量，而是形成下面这条可验证证据链：

```text
Baseline
 < late single-layer cluster context
 < true routed context（若成立）
 < detail-preserving refinement（若成立）
```

