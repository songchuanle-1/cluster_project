# 基于 model_base1 的轻量层次 Cluster Attention 研究计划（重新研究版）

> 文献依据与新设计详见：[`cluster_attention_literature_research.md`](cluster_attention_literature_research.md)。相关论文 PDF 已保存到 `docs/papers/cluster_attention/`。

## 1. 研究目标

本研究以 `Cluster/framework/model/Quard_model/model_base1` 为唯一 baseline，目标是在尽量不增加参数量和计算量的前提下，通过几何 cluster 上下文增强 `inst_feats`，提高 3D referring segmentation 性能。

核心约束：

1. Cluster 模块只更新 `inst_feats`，不更新 decoder proposal query。
2. 多层结构真实执行 `N -> 256 -> 64 -> 8` 聚合和 `8 -> 64 -> 256 -> N` 回传。
3. 主实验不依赖语言或 proposal query，先证明纯点云层次上下文有效。
4. 优先使用无投影、标量或逐通道参数，避免标准 Q/K/V 的 `O(C^2)` 参数。
5. 严格区分 pooling、hierarchical propagation 和 attention 的贡献。

研究假设：几何 cluster 能为 superpoint 提供稳定区域上下文；粗到细传播能把场景级结构逐级注入局部区域；基于内容相似度的轻量 cluster attention 能抑制无关信息，减少均值回写造成的过平滑。

## 2. Baseline 与更新对象

`model_base1` 的 encoder layer 为：

```text
lang = LLA(lang)
lang = LIA(source=inst, query=lang)
inst = ILA(source=lang, query=inst)
lang = FFN(lang)
```

- `LIA` 更新 `lang_feats`。
- `ILA` 更新 `inst_feats`。
- decoder proposal query 走独立 decoder 路径。
- Cluster 分支输出 `[B,N,C]`，通过残差只写回 `inst_feats`。

推荐注入最后一个 encoder layer 的 LIA 与 ILA 之间：

```text
lang = LLA(lang)
lang = LIA(inst, lang)
inst = inst + gamma * ClusterModule(inst, xyz)
inst = ILA(lang, inst)
lang = FFN(lang)
```

ClusterModule 不读取 `lang`。该位置的准确含义是：本层 LIA 读取原始 inst，增强后的 inst 再进入 ILA；不能描述为“Cluster 模块使用了语言特征”。

| 模型 | Best mIoU | Best epoch | Final mIoU | 已训练 epoch |
|---|---:|---:|---:|---:|
| `model_base1` | 0.489449 | 15 | 0.473846 | 30 |

该结果未跑满统一协议，只作为先验证据。

## 3. 对旧 C2F Lite 的重新判定

旧 `model_base1_quard2_c2f_enc_lite_posA` 使用 proposal query 对 8、64、256 层 cluster 计算 top-k 路由，但最终 `_cluster_to_points` 直接根据 cluster id 回读全部预聚合 token，未使用路由产生的 `prev_indices`。

因此：

- 旧结果能支持“多尺度 cluster context 回写有潜力”。
- 旧结果不能证明 proposal-query routing 有效。
- 旧结果不能证明真正的 coarse-to-fine attention 有效。
- `posA` 和 `lite_l1` 的高分是后层少量 inst refinement 的先验证据。
- 旧 `noroute` 与 lite 的差异不能直接归因为 routing，必须在修正实现后重跑。

| 变体 | Best mIoU | 可支持的结论 |
|---|---:|---|
| `model_base1_quard2_c2f_enc_lite_posA` | 0.500940 | P1 位置的多尺度 cluster 回写有潜力 |
| `model_base1_quard2_c2f_enc_lite_l1` | 0.500636 | 最后少量 encoder 层注入较合适 |
| `model_base1_quard2_c2f_enc_lite` | 0.499236 | cluster context 可能有效 |
| `model_base1_quard2_c2f_enc_lite_l3` | 0.498062 | 多层重复注入可能开始过平滑 |
| `model_base1_quard2_c2f_enc_lite_l4` | 0.493136 | 过多层注入不利 |

这些实验训练长度不同，且 best 与 final 差距明显，不能作为最终论文对照。

## 4. 正确的多层几何结构

```text
superpoints F0 [N,C]
  -- id0: point -> 256 --> F256 [K0,C]
  -- id1: 256 -> 64    --> F64  [K1,C]
  -- id2: 64 -> 8      --> F8   [K2,C]
```

层级索引必须复合：

```text
point_to_256 = id0
point_to_64  = id1[id0]
point_to_8   = id2[id1[id0]]
child256_to_parent64 = id1
child64_to_parent8   = id2
```

第一轮固定 mean pooling：

```text
F_parent(k) = mean({F_child(i) | parent(i)=k})
```

必须区分三种机制：

| 类别 | 计算 | 作用 | 是否为 attention |
|---|---|---|---|
| Cluster Pooling | cluster mean 直接 gather 回点 | 区域平滑/上下文 | 否 |
| Hierarchical Propagation | parent token 按父子 id 广播给 child | 粗到细消息传递 | 否 |
| Hierarchical Cluster Attention | child 在 parent/兄弟候选中计算内容权重 | 选择性上下文聚合 | 是 |

当前 `model_base1_cluster_hier_*` 使用标量、逐通道或 cosine gate 传播唯一 parent token，没有在多个 key 上归一化 attention 权重。因此它们是重要消融，但不应直接作为最终 Cluster Attention 主模型。

## 5. 低成本主方法：Parameter-Free Hierarchical Cluster Attention

标准多头 attention 每层引入 Q/K/V/O 投影，约 `4C^2` 参数；`C=256` 时单层约 26 万参数。本方案用原特征的归一化点积计算权重，不增加 Q/K/V 矩阵。

### 5.1 Coarse：8 个 scene-region token

```text
S8(i,j) = cosine(LN(F8_i), LN(F8_j)) / tau8
A8      = softmax(S8)
M8      = A8 F8
R8      = F8 + alpha8 * M8
```

只计算 `8 x 8` attention。

### 5.2 Middle：64 个 token

每个 child 只查看 refined parent 和同一 parent 下的 siblings：

```text
candidate64(i) = {R8[parent(i)]} union {F64 siblings}
A64(i,:) = softmax(cosine(F64_i, candidate64(i)) / tau64)
M64_i    = weighted_sum(candidate64(i), A64(i,:))
R64_i    = F64_i + alpha64 * M64_i
```

平均每个 8-level parent 约含 8 个 child，远小于全局 `64 x 64` attention。

### 5.3 Fine：256 个 token

```text
candidate256(i) = {R64[parent(i)]} union {F256 siblings}
A256(i,:) = softmax(cosine(F256_i, candidate256(i)) / tau256)
M256_i    = weighted_sum(candidate256(i), A256(i,:))
R256_i    = F256_i + alpha256 * M256_i
```

平均每个 64-level parent 约含 4 个 child，fine attention 仍然很小。

### 5.4 回写 inst feature

```text
context_i = R256[point_to_256(i)]
delta_i   = LN(context_i - inst_i)
inst'_i   = inst_i + gamma * delta_i
```

`context - inst` 表达区域上下文对当前点的修正，比直接叠加 cluster mean 更不易造成整体漂移。

### 5.5 参数和复杂度

主版本新增 3 个温度、3 个层级残差系数、1 个最终 LayerScale，以及 LayerNorm 仿射参数。除 LayerNorm 外仅 7 个标量。

```text
Attention cost ~= O((8*8 + 64*9 + 256*5) * C)
```

它远小于 point-level `O(N^2 C)`，也避免 Q/K/V 的 `O(C^2)` 投影参数。

### 5.6 已实现的三个 HCA 版本

三个版本共享相同的 bottom-up 几何聚类、coarse-to-fine 层级和 inst feature 回写方式：

```text
Bottom-up: inst_feats [N,C] -> F256 -> F64 -> F8
Top-down:  F8 -> R8 -> R64 -> R256 -> point context [N,C]
Update:    inst' = inst + gamma * LN(point_context - inst)
Position:  last encoder layer, LIA 后、ILA 前（P1）
```

它们都不读取或修改 decoder proposal query，也不使用 Q/K/V/O 全连接投影。区别只在 `8 -> 64 -> 256` 过程中如何生成每层 message。

#### V1：`model_base1_hca_coarse_l1`

目的：验证“最粗层全局 attention + 多层父级广播”是否已经足够。

```text
F8
  -> 8 x 8 cosine self-attention
  -> R8 = F8 + alpha8 * Attn(F8, F8)

R8 --parent gather--> F64
  -> R64 = F64 + alpha64 * R8[parent64]

R64 --parent gather--> F256
  -> R256 = F256 + alpha256 * R64[parent256]

R256 --point_to_256 gather--> N points
```

- 只有 8 层计算多个 key 上的 softmax attention。
- 64 和 256 层采用确定的 parent message，不计算 sibling attention。
- 虽然名称为 coarse，该版本仍执行完整的 `8 -> 64 -> 256 -> N` 多层传播。
- 它是计算量最低的 HCA 版本，也是后续版本的严格对照。

代码目录：`Cluster/framework/model/Quard_model/model_base1_hca_coarse_l1/`

配置：`Cluster/configs/Quard/model_base1_hca_coarse_l1.yaml`

#### V2：`model_base1_hca_c2f_parent_l1`

目的：验证 child 是否需要根据自身内容，在 local feature 和 refined parent context 之间自适应选择。

```text
R8 = F8 + alpha8 * Attn(F8, F8)

C64(i) = [F64(i), R8[parent(i)]]
R64(i) = F64(i) + alpha64 * Attn(query=F64(i), key/value=C64(i))

C256(i) = [F256(i), R64[parent(i)]]
R256(i) = F256(i) + alpha256 * Attn(query=F256(i), key/value=C256(i))

R256 --point_to_256 gather--> N points
```

- 64 和 256 层的候选数固定为 2：`self + parent`。
- 相比 V1，parent context 不再无条件广播，而由 cosine attention 决定注入比例。
- 该版本直接检验内容自适应 parent propagation 的贡献。

代码目录：`Cluster/framework/model/Quard_model/model_base1_hca_c2f_parent_l1/`

配置：`Cluster/configs/Quard/model_base1_hca_c2f_parent_l1.yaml`

#### V3：`model_base1_hca_c2f_sibling_l1`

目的：在 parent context 之外，引入同一几何区域内部的 sibling cluster 交互。

```text
R8 = F8 + alpha8 * Attn(F8, F8)

C64(i) = [R8[parent(i)], all F64 siblings under the same F8 parent]
R64(i) = F64(i) + alpha64 * Attn(query=F64(i), key/value=C64(i))

C256(i) = [R64[parent(i)], all F256 siblings under the same F64 parent]
R256(i) = F256(i) + alpha256 * Attn(query=F256(i), key/value=C256(i))

R256 --point_to_256 gather--> N points
```

- 8 层建模场景区域之间的全局关系。
- 64 层建模中尺度 sibling 关系，并接收 refined 8-level parent。
- 256 层建模局部 sibling 关系，并接收 refined 64-level parent。
- 这是三个版本中结构最完整的 Hierarchical Cluster Attention 主模型。
- attention 只发生在同父局部候选中，不构造全局 `64 x 64` 或 `256 x 256` 矩阵。

代码目录：`Cluster/framework/model/Quard_model/model_base1_hca_c2f_sibling_l1/`

配置：`Cluster/configs/Quard/model_base1_hca_c2f_sibling_l1.yaml`

#### 三版本对照总结

| 版本 | 8 层 | 64 层 | 256 层 | 多层传播 | 主要验证问题 |
|---|---|---|---|---|---|
| HCA-Coarse | 全局 self-attention | parent broadcast | parent broadcast | 是 | 粗层 attention 是否足够 |
| HCA-Parent | 全局 self-attention | self/parent attention | self/parent attention | 是 | 是否需要内容自适应 parent 注入 |
| HCA-Sibling | 全局 self-attention | parent+sibling attention | parent+sibling attention | 是 | 局部 sibling 交互是否进一步有效 |

三个模块在 `C=256` 时自身参数量约为 `518`（LayerNorm 512 + 3 个温度 + 3 个层级 scale）；加 encoder 外部 LayerScale `gamma` 后约为 `519` 个参数。

推荐严格按以下顺序训练：

```text
HCA-Coarse -> HCA-Parent -> HCA-Sibling
```

判读方式：

- `Parent > Coarse`：内容自适应父子传播有效。
- `Sibling > Parent`：同父 cluster 的局部关系建模有效。
- `Coarse` 最优：主要收益来自粗层全局上下文，细层 attention 可能引入噪声。
- 三者接近：优先选择 HCA-Coarse，保留最低实际延迟。

## 6. 现有新变体的准确角色

当前代码实际位于 `Cluster/framework/model/model_base2/`，配置位于 `Cluster/configs/modelbase2/`。模型名虽以 `model_base1_cluster_*` 开头，但目录位置容易造成误解，实验前必须确认框架实际加载了对应目录。

| 模型 | 实际结构 | 研究角色 | 预计新增参数 |
|---|---|---|---:|
| `light_s256_l1` | 256 mean 回写 | 单尺度/平滑基线 | 约 513 |
| `light_s64_l1` | 64 mean 回写 | 中尺度基线 | 约 513 |
| `light_s8_l1` | 8 mean 回写 | 全局尺度基线 | 约 513 |
| `light_parallel_fixed_l1` | 三尺度固定平均 | multi-scale 基线 | 约 513 |
| `light_parallel_learned_l1` | 三尺度全局 softmax 权重 | learned fusion | 约 516 |
| `light_diff_l1` | 多尺度融合减 point | 差分回写 | 约 516 |
| `light_c2f_l1` | scalar parent broadcast + 多尺度差分 | C2F 消融 | 约 518 |
| `hier_add_l1` | scalar top-down，回读 finest | 传播基线 | 约 515 |
| `hier_diff_l1` | `hier_add` + point difference | 推荐传播基线 | 约 515 |
| `hier_fusion_l1` | top-down + 三尺度 learned fusion | 多尺度传播 | 约 518 |
| `hier_channel_l1` | per-channel parent scale | 高容量传播 | 约 1025 |
| `hier_content_l1` | cosine scalar gate 控制 parent broadcast | 内容门控传播 | 约 517 |

这些模型都没有真正的“多个候选 key 上的 attention softmax”，应作为新主方法的低成本对照。

## 7. 必做实验矩阵

### 7.1 阶段 A：确认收益不是简单平滑

| 顺序 | 编号 | 模型 | 唯一问题 |
|---:|---|---|---|
| 1 | A0 | `model_base1` | 同协议 baseline |
| 2 | A1 | identity，`gamma=0` | 接线是否严格等价 baseline |
| 3 | A2 | `light_s256_l1` | 细粒度 cluster mean 是否已足够 |
| 4 | A3 | `light_s64_l1` | 中尺度是否更有效 |
| 5 | A4 | `light_s8_l1` | 全局 cluster mean 是否过粗 |

若 A2 已获得大部分增益，首先证明的是 cluster smoothing，而不是 hierarchy。

### 7.2 阶段 B：证明 multi-scale 与 hierarchy

| 顺序 | 编号 | 模型 | 比较对象 |
|---:|---|---|---|
| 6 | B1 | `light_parallel_fixed_l1` | 对比最佳单尺度 |
| 7 | B2 | `light_diff_l1` | 对比直接多尺度回写 |
| 8 | B3 | `hier_add_l1` | 对比 B1，验证 top-down propagation |
| 9 | B4 | `hier_diff_l1` | 对比 B3，验证差分回写 |
| 10 | B5 | `hier_content_l1` | 对比 B4，验证内容门控 |

只有 `B3/B4 > B1/B2`，才能声称父子层次传播有独立收益。

### 7.3 阶段 C：证明真正的 Cluster Attention

| 编号 | 新模型 | Attention 范围 | 研究问题 |
|---|---|---|---|
| C1 | `hca_coarse_l1` | 仅 8x8 | 场景区域 attention 是否有效 |
| C2 | `hca_c2f_parent_l1` | 8 attention + parent/child | 逐级条件传播是否有效 |
| C3 | `hca_c2f_sibling_l1` | 8 + parent + siblings | 完整轻量层次 attention |

```text
期望证据链：C3 > C2 > C1 > B4 > B2 > best(A2,A3,A4) > A0
```

方法命名必须跟随证据：

- 仅 B1/B2 有效：multi-scale cluster context refinement。
- B3/B4 额外有效：hierarchical cluster propagation。
- C2/C3 额外有效：hierarchical cluster attention。

### 7.4 阶段 D：注入位置与次数

只对阶段 B/C 的最优结构测试：

| 编号 | 设置 | 含义 |
|---|---|---|
| D1 | P0：encoder 前一次 | 纯视觉预增强 |
| D2 | P1：最后一层 LIA 后、ILA 前 | 当前推荐位置 |
| D3 | P2：最后一层 ILA 后 | 已融合语言后的 inst refinement |
| D4 | 最后 2 层 P1 | 重复 refinement |

不优先跑 3/4/6 层，旧结果已提示层数增多会下降。

## 8. 初始化与稳定性

推荐：

```text
gamma = 1e-3
alpha8 = alpha64 = alpha256 = 0.1
tau initial = 0.2, parameterized by softplus
message = LayerNorm(message)
```

当前 `hier_add` 同时有内部 `c2f_scales=0` 和外部 `gamma=1e-3`：初始 top-down 分支为 0，但 finest cluster mean 仍会回写；内部传播的梯度还会乘外部 `gamma`，学习可能很慢。正式实验应避免内部 zero-init 与外部小 LayerScale 双重抑制，保留一个稳定小残差即可。

## 9. 统一训练和统计协议

- 全部实验使用相同数据划分、增强、batch size、优化器、学习率和 scheduler。
- 统一训练 50 epoch，统一验证频率和 checkpoint 规则。
- 第一轮使用同一 seed 筛选，不用不同训练长度的 best mIoU 排名。
- 入选结构至少运行 3 seeds，报告 `mean +/- std`。
- 报告 mIoU、Acc@0.25、Acc@0.5、best、final 和最后 5 epoch 均值。
- 记录 total/trainable params、latency、peak memory；FLOPs 工具常漏算 FPS、`cdist`、scatter 和 Python loop，需单独说明。
- 单 seed 提升小于 `0.003 mIoU` 时，不足以认定稳定收益，应进入多 seed 检验。

当前配置存在 `train.epochs=50`、`lr_scheduler.max_iters=70` 的不一致，正式对照前必须统一 scheduler 定义。

## 10. 必做测试和诊断

### 正确性

1. 验证 `point_to_64=id1[id0]`、`point_to_8=id2[id1[id0]]`。
2. 验证不同 batch 的 cluster id 不串联，padding message 恒为 0。
3. `gamma=0` 时输出与 baseline 完全一致。
4. attention candidate 非空，padding 行不出现 softmax(all `-inf`)。
5. 有效 attention 权重和为 1，`alpha/tau/gamma` backward 后梯度有限。

### 机制诊断

- 每层 message norm、方差和 gate 轨迹。
- cluster 内/cluster 间 cosine similarity。
- 回写前后 point pairwise similarity，监测过平滑。
- 8、64、256 层 attention entropy。
- attention 对 parent、siblings 的平均权重。
- small/medium/large object、unique/multiple、attribute/spatial relation 分组指标。

## 11. 推荐执行顺序

```text
Step 1  修正文档路径并检查模型加载
Step 2  补 identity 和层级映射测试
Step 3  A0/A2/A3/A4：确定最佳单尺度
Step 4  B1/B2：验证 multi-scale 与 difference
Step 5  B3/B4/B5：验证 hierarchy 与 content gate
Step 6  实现 C1/C2/C3 parameter-free cluster attention
Step 7  最优模型做 P0/P1/P2、last-1/last-2
Step 8  完整 50 epoch，3 seeds，统计参数/延迟/显存
Step 9  纯 inst 主线稳定后，再研究 language-conditioned gate
```

最小优先队列：

```text
A0 -> A2 -> A3 -> A4 -> B1 -> B4 -> B5 -> C1 -> C3
```

算力有限时暂缓 `parallel_learned`、`hier_fusion`、`hier_channel`，因为它们不能直接回答最核心的机制问题。

## 12. 论文表述边界

若 C3 稳定提升，可表述为 lightweight hierarchical cluster attention：在几何嵌套 cluster 上，从粗到细对 parent 和 sibling 上下文进行内容自适应聚合，并只残差增强 inst feature，不修改 proposal-query 路径。

若只有 B4/B5 有效，应称为 lightweight coarse-to-fine cluster context refinement，而不是 attention。

```text
主线：geometry hierarchy -> cluster context -> inst feature residual refinement
```

## 13. 2026-07-13 最新阶段结果与主线调整

最新统一对比见：`Cluster/logs_analysis/gbcr_current_comparison/analysis.md`。

- `gbcr_adaptive_l1` 在 epoch 23 中段停止，最后完整验证到 epoch 22，best 为 `0.496102@17`，暂时超过 baseline `0.489449`、Balanced `0.495160` 和 Local `0.494311`。
- Epoch 14-22 均值为 `0.491031`，高于 baseline `0.485543`、Balanced `0.488972`、Local `0.489836`；说明提升并非只有单点，但持续优势仍较小。
- `gbcr_pointgate_l1` 只训练 12 轮便停止，best 为 `0.484118`，不能视为完整实验，也不建议优先补跑随机初始化 gate 的旧版本。
- Adaptive best 的外层 LayerScale 为 `-0.1795`，再次支持 detail sharpening；scale bias `[256,64,8]=[-0.0103,-0.4215,+0.1027]`，显示 64 层 value 被整体抑制。

面向提高指标，下一主版本调整为 `gbcr_langroute_l1`：仅在 8-cluster 粗层用 pooled language feature 调制共享低维 Q，随后仍按几何层级执行 `8 -> 64 -> 256` top-k/配额收缩，最终只更新 `inst_feats`。该设计复用现有 Q 投影，新增参数约一个标量，不引入点对点 attention。

后续优先级：

```text
finish adaptive -> language-conditioned coarse routing
                -> keep 64 as routing bridge, fuse endpoint contexts
                -> explicit positive detail update
```

### 13.1 下一阶段性能版本

基于 Adaptive 的代码和 checkpoint 进一步诊断，后续性能主线细化为：

```text
V-Next1  LangRoute:
          language-targeted 8-level score
          -> geometry C2F quota routing
          -> inst detail update

V-Next2  LangC2F:
          LangRoute
          + context8 conditions Q64
          + context64 conditions Q256

V-Next3  LearnableScale:
          LangC2F
          + differentiable 32D point-scale metric
```

三个版本均复用共享低维 Q/K，不增加全局 64x64、256x256 或 point-to-point attention，累计新增参数控制在数百以内。详细公式、成本和运行判定标准见 `Cluster/logs_analysis/gbcr_current_comparison/analysis.md` 第 6 节。

### 13.2 V-Next1/2/3 代码实现（2026-07-13）

三个性能版本已经实现为完整独立目录。每个目录均包含本地的 `__init__.py`、`network.py`、`dec.py`、`hier_postprocess.py`、`backbone.py`、`loss.py` 和 `sample_model.py`，不存在跨变体 import。

#### V-Next1：`model_base1_gbcr_langroute_l1`

核心路径：`Cluster/framework/model/Quard_model/model_base1_gbcr_langroute_l1/hier_postprocess.py`

配置：`Cluster/configs/Quard/model_base1_gbcr_langroute_l1.yaml`

```text
masked language mean
    -> language relevance over 8 cluster keys
    -> visual score8 + alpha_lang * language relevance
    -> top-3 coarse route
    -> 64: local4 + routed12, route top-6
    -> 256: local4 + routed20, route top-8
    -> raw-cosine point-adaptive 256/64/8 fusion
    -> LN(context-point) + identity-init PointGate
    -> signed LayerScale update inst_feats
```

- 只影响 cluster routing，不修改 proposal query。
- 复用共享 32D `query_proj/key_proj`。
- `alpha_lang=0.1` 初始化。
- Cluster 模块参数量：`17,225`，比 Adaptive 增加 1。

#### V-Next2：`model_base1_gbcr_langc2f_l1`

核心路径：`Cluster/framework/model/Quard_model/model_base1_gbcr_langc2f_l1/hier_postprocess.py`

配置：`Cluster/configs/Quard/model_base1_gbcr_langc2f_l1.yaml`

在 V-Next1 上增加：

```text
query64  = f64  + beta64  * context8[parent8]
query256 = f256 + beta256 * context64[parent64]
```

- `beta256/beta64=0.1` 初始化。
- parent context 只条件化 query；候选 value 仍是原始 `f64/f256`。
- local quota 保留，避免错误粗路由完全排除本地候选。
- Cluster 模块参数量：`17,227`，比 Adaptive 增加 3。

#### V-Next3：`model_base1_gbcr_langc2f_scale_l1`

核心路径：`Cluster/framework/model/Quard_model/model_base1_gbcr_langc2f_scale_l1/hier_postprocess.py`

配置：`Cluster/configs/Quard/model_base1_gbcr_langc2f_scale_l1.yaml`

在 V-Next2 上将点级尺度度量改为：

```text
point_route = normalize(Q(point.detach()))
context_route_l = normalize(scale_affine_l(K(context_l.detach())))
scale_weight = softmax(dot(point_route, context_route_l) / tau + bias)
fused = sum(scale_weight_l * context_l)
```

- Q/K 和每层 32D affine 可学习，输入 feature 在尺度打分支 detach。
- context value 主路径仍然可微。
- 新增每层 32D weight/bias，共 192 个参数。
- Cluster 模块参数量：`17,419`，比 Adaptive 增加 195。

#### 验证结果

| 模型 | CUDA 前反向 | padding mask | 新参数梯度 | 12k 点模块峰值显存 |
|---|---|---|---|---:|
| Adaptive（同测试口径） | 通过 | - | 通过 | 150.24 MB |
| LangRoute | 通过 | 通过 | 通过 | 150.24 MB |
| LangC2F | 通过 | 通过 | 通过 | 150.87 MB |
| LangC2FScale | 通过 | 通过 | 通过 | 175.54 MB |

显存数字是 cluster 模块的合成前反向测试，不等于完整训练峰值；它适合比较三个结构的相对增量。

#### 训练命令

```bash
cd /data/songcl/3dres/Cluster_project2/Cluster

conda run -n cluster python tools/train.py \
  configs/Quard/model_base1_gbcr_langroute_l1.yaml --gpu_id 0

conda run -n cluster python tools/train.py \
  configs/Quard/model_base1_gbcr_langc2f_l1.yaml --gpu_id 0

conda run -n cluster python tools/train.py \
  configs/Quard/model_base1_gbcr_langc2f_scale_l1.yaml --gpu_id 0
```

面向指标提升的推荐运行顺序仍为：

```text
LangRoute -> LangC2F -> LangC2FScale
```

先运行 LangRoute。只有当其高值区间均值优于 Adaptive，再运行 LangC2F；Scale 版本计算图略大，排在最后。
