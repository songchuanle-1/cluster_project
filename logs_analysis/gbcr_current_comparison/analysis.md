# GBCR 最新结果与下一步优化（2026-07-13）

## 1. 运行状态

本页按日志当前快照统计，不把部分训练误写成完整结果。

| 模型 | 已验证轮数 | 状态 | Best mIoU | Best Epoch | 当前/最后 mIoU |
|---|---:|---|---:|---:|---:|
| `model_base1` | 30 | 已结束 | 0.489449 | 15 | 0.473846 |
| `gbcr_balanced_l1` | 38 | 已结束 | 0.495160 | 20 | 0.482246 |
| `gbcr_local_l1` | 33 | 已结束 | 0.494311 | 19 | 0.483982 |
| `gbcr_pointgate_l1` | 12 | 提前停止 | 0.484118 | 11 | 0.482211 |
| `gbcr_adaptive_l1` | 22 | Epoch 23 中断，完整验证到 22 | **0.496102** | 17 | **0.486771** |

Adaptive 当前 best 相对 baseline 为 `+0.006653`，相对 Balanced 为 `+0.000942`。这是目前最高单次结果，但 Adaptive 尚未跑完，不能用其 22 轮均值和其他模型完整均值直接排名。

## 2. 公平轮次比较

### 前 12 轮（五个模型共同区间）

| 模型 | 均值 | 区间 Best | Epoch 11 | Epoch 12 |
|---|---:|---:|---:|---:|
| Baseline | 0.441595 | 0.483739 | 0.479602 | 0.483739 |
| Balanced | 0.442070 | 0.486013 | 0.483688 | **0.486013** |
| Local | **0.445094** | **0.487784** | **0.487784** | 0.482348 |
| PointGate | 0.438043 | 0.484118 | 0.484118 | 0.482211 |
| Adaptive | 0.444652 | 0.484432 | 0.484432 | 0.481830 |

PointGate 没有表现出早期优势，并且它的线性 gate 使用随机初始化，训练开始时会无依据地改变不同点的更新幅度。该运行只到 12 轮，既不能证明 PointGate 无效，也没有继续补跑的优先级。

### Epoch 14-22（排除未到该区间的 PointGate）

| 模型 | Epoch 14-22 均值 | Epoch 18-22 均值 |
|---|---:|---:|
| Baseline | 0.485543 | 0.485600 |
| Balanced | 0.488972 | 0.488927 |
| Local | 0.489836 | **0.489831** |
| Adaptive | **0.491031** | 0.489306 |

Adaptive 在主要高值区间优于已有版本，不只是第 17 轮单点提升；但第 18-22 轮与 Local 基本持平，并在峰值后回落，因此当前结构的稳定增益约为 `+0.001~0.002`，不是接近 `+0.007` 的持续增益。

## 3. Adaptive 学到了什么

Adaptive best checkpoint 的关键参数：

| 参数 | 学习结果 |
|---|---:|
| 外层 signed LayerScale | `-0.1795` |
| routing temperature `[256,64,8]` | `[0.3677, 0.4856, 0.5612]` |
| point-scale temperature | `0.3614` |
| scale bias `[256,64,8]` | `[-0.0103, -0.4215, +0.1027]` |
| PointGate bias | `3.9629` |

结论：

1. 外层 gate 再次稳定学成负值。当前 message 是 `LN(context - point)`，实际更新更接近 `point - context` 的细节增强，而不是邻域平滑。
2. 三尺度融合明显压低 64 层、偏向 8 层。bias 不是最终权重，点级 cosine 仍会改变每个点的选择，但中层整体被抑制的趋势很明确。
3. PointGate bias 仍接近 identity 初始化，说明本轮增益更可能来自配额路由、共享低维 Q/K 和点级尺度选择，而不是大幅关闭某些点。
4. Adaptive 的有效路线可概括为：`8 层提供全局参照 -> 64 层负责路由过渡 -> 256 层恢复局部候选 -> 对点特征做对比式增强`。

## 4. 下一步优化方向

### P0：先让 Adaptive 完成

当前 Adaptive 进程已停止在 Epoch 23 中段，最后完整验证为 Epoch 22。若继续该运行，至少观察到 epoch 30，保留 best checkpoint，并重点比较 epoch 14-30 均值、Top-5 均值和最后 5 轮均值。不要同时在同一 GPU 启动新模型干扰吞吐和显存。

### P1：语言条件的粗层路由（下一主版本）

当前 Adaptive 在 cluster 模块中直接丢弃 `lang_feats`，而任务是指代表达分割。建议只在 8-cluster 层加入语言条件，不修改 proposal query，也不增加点对点注意力：

```text
lang_summary = masked_mean(lang_feats)
q8 = q_proj(f8) + alpha_lang * q_proj(lang_summary)
score8 = cosine(q8, k_proj(f8))
8-level topk -> 64-level quota routing -> 256-level quota routing
final message -> inst_feats
```

复用现有共享 `q_proj`，只新增一个标量 `alpha_lang`；额外计算只发生在 8 个 cluster 上。它最有可能突破当前几何路由的上限，因为粗层 top-k 会从“几何/视觉相似区域”变成“与当前表达相关的区域”。建议模型名：`model_base1_gbcr_langroute_l1`。

### P2：把 64 层改成路由桥，而不是最终值分支

当前 scale bias 强烈抑制 64 层。保留完整 `8 -> 64 -> 256` 多层候选收缩，但最终点级融合只使用 8 与 256：

```text
8 context -> route64 -> route256
point_context = gate(point) * context256 + (1-gate(point)) * context8
```

这样不会破坏多层路由思想，同时去掉疑似噪声较大的中层 value 回写，并略减点级融合计算。此方向排在语言路由之后。

### P3：显式正参数化 detail update

把现在隐式学出的负 LayerScale 改写为：

```text
detail = LN(point - fused_context)
inst_feats = inst_feats + positive_scale * point_gate(detail) * detail
```

`positive_scale` 可用 sigmoid/softplus 约束，并初始化为小正值。它能消除 message 方向和 signed gate 的符号冗余，预期主要改善训练稳定性，不一定单独提高峰值，因此优先级低于 P1。

### 暂不优先

- 不继续扩大 64/256 top-k：现有结果没有显示候选不足，且会增加显存与噪声。
- 不增加 cluster attention 注入层数：旧结果和当前 last-layer 注入均支持单次后期增强。
- 不补跑旧 PointGate：随机 gate 初始化版本的信息价值低，Adaptive 已包含 identity-init PointGate。
- 不先做大规模消融：当前目标是提高指标，应先验证语言条件粗路由这个高收益、低成本方向。

## 5. 推荐执行顺序

```text
1. 视算力决定是否从 last checkpoint 补到 epoch 30；当前结构结论已可用于下一版本
2. 实现并运行 gbcr_langroute_l1
3. 若语言路由有效，在其上测试 64-as-router-only
4. 最优版本改为显式 detail update，比较稳定性
5. 最终候选再做 3 seeds 和必要结构消融
```

## 6. 面向指标提升的进一步结构研究

### 6.1 当前瓶颈定位

当前实现并不是完整的“语义逐层细化”，而是：

```text
8-level feature attention -> 只产生 route8
64-level raw feature attention -> 只产生 route64
256-level raw feature attention -> context256
三个 context 再在点级融合
```

这带来三个限制：

1. **粗层路由与任务表达无关**：cluster 模块直接 `del lang_feats, lang_mask`。同一场景中不同指代表达使用完全相同的粗层候选关系。
2. **父层语义没有进入子层 query**：64/256 层虽然受到父层 top-k 的候选约束，但排序 query 仍然只是原始 `f64/f256`，属于候选集合逐层收缩，而不是表示逐层条件化。
3. **尺度选择只有固定 cosine 规则**：point-context cosine 在 `no_grad` 中计算。三个全局 bias 和温度可以学习，但模型没有专门的低维度量去判断某个点应依赖 8、64 还是 256 层。

另一方面，best 到 last 的参数变化很小：外层 gate `-0.1795 -> -0.1818`，64-level bias `-0.4215 -> -0.4422`。峰值后回落更像验证波动与逐渐偏向粗/细两端，不是参数发散。所有现有对照使用同一 `PolyLR(max_iters=70)`，下一结构实验暂不改变 scheduler，避免混淆结构收益。

### 6.2 V-Next1：Language-Targeted Coarse Routing

推荐名称：`model_base1_gbcr_langroute_l1`。

对每个场景计算有效 token 的 masked mean：

```text
L = masked_mean(lang_feats)
visual_score(i,j) = cos(Q(F8_i), K(F8_j))
lang_relevance(j) = cos(Q(L), K(F8_j))
score8(i,j) = visual_score(i,j) + alpha_lang * lang_relevance(j)
```

然后仍执行当前的：

```text
score8 top-3 -> 64 local4+routed12 -> top-6
             -> 256 local4+routed20 -> top-8
             -> point fusion -> update inst_feats
```

设计理由：语言只改变“目标候选区域”，value 仍然全部来自点云 cluster；因此不会把 decoder query 更新偷换成 query attention。复用现有 `query_proj/key_proj`，仅新增 `alpha_lang` 一个标量，8x8 计算量几乎可忽略。

预期：主要改善 multiple-object、attribute 和 spatial-relation 样本；若总体 mIoU 没提高，需要首先看这些分组，而不是直接扩大模型。

### 6.3 V-Next2：Language + Parent-Conditioned C2F Routing

推荐名称：`model_base1_gbcr_langc2f_l1`，只在 V-Next1 有正收益后继续。

```text
Q64_i  = Q(F64_i)  + beta64  * Q(context8[parent8(i)])
Q256_i = Q(F256_i) + beta256 * Q(context64[parent64(i)])
```

候选集合、local/routed quota 和 raw value 保持不变。新增 `beta64/beta256` 两个标量，建议小正值初始化。

它与当前结构的关键区别是：当前只有 `coarse route -> fine candidate set`；新版本变成 `coarse route + coarse context -> fine ranking`。这才是更完整的从粗到细语义条件化，同时不构造 64x64、256x256 全局 attention。

风险：粗层选择错误会向下传播。现有 local quota 必须保留，作为防止错误路由完全排除本地区域的安全通道。

### 6.4 V-Next3：Learnable Low-Dimensional Scale Metric

推荐名称：`model_base1_gbcr_langc2f_scale_l1`。

用现有 32D 路由空间替代固定 256D raw cosine：

```text
p = normalize(Q(point.detach()))
c_l = normalize(K(context_l.detach()))
scale_score_l = dot(p, c_l) + bias_l
scale_weight = softmax(scale_score / tau_scale)
fused = sum(scale_weight_l * context_l)
```

输入 feature 可 detach，但 Q/K 参数保留梯度。这样不会保留三份 `[N,256]` normalization graph，只增加 `[N,3,32]` 级别激活；context value 路径仍可正常反向传播。可选增加每尺度 32D affine，额外约 192 参数。

该版本解决“点级尺度选择存在，但度量不可学习”的问题。它排在语言路由之后，因为当前最大的任务错配仍是 coarse routing 完全不知道指代表达。

### 6.5 Endpoint Detail 作为后备分支

若 V-Next2 后 64-level bias 仍持续低于 `-0.4`，再把 64 层固定为 routing bridge：

```text
8 -> 64 -> 256 routing 保留
final fusion 只使用 context8/context256
message = LN(point - fused_context)
positive residual scale
```

这不是删除 64 层，而是删除 64-level value 的最终点级回写。它应作为结果驱动的后备修改，不与 V-Next1 同时改，以免无法判断语言路由是否有效。

### 6.6 成本与运行优先级

| 版本 | 新增参数 | 额外主要激活 | 预期收益来源 | 优先级 |
|---|---:|---:|---|---:|
| LangRoute | 约 1 | 8x8 | 目标相关粗路由 | 1 |
| LangC2F | 约 3（累计） | 64x32 + 256x32 | 父语义参与细层排序 | 2 |
| LearnableScale | 0 或约 192 | N x 3 x 32 | 可学习点级尺度选择 | 3 |
| EndpointDetail | 参数减少 | 略微减少 | 去除被压低的 64 value | 后备 |

推荐判定标准：

```text
第一标准：Best mIoU >= Adaptive best + 0.002
第二标准：Epoch 14-25 均值 >= Adaptive 同区间 + 0.001
第三标准：峰值后 5 轮均值不低于 Local
```

只满足第一标准可能仍是单轮波动；满足前两项才继续叠加下一个结构。当前不建议增加 top-k、不建议增加注入层数，也不建议同时修改 scheduler。

## 7. 后续性能版本已实现

研究中的三个递进版本已经实现：

| 模型 | 核心变化 | Cluster 参数 | 12k 点模块峰值显存 |
|---|---|---:|---:|
| `gbcr_langroute_l1` | 语言目标相关的 8-level 路由 | 17,225 | 150.24 MB |
| `gbcr_langc2f_l1` | 加入 64/256 父上下文条件 query | 17,227 | 150.87 MB |
| `gbcr_langc2f_scale_l1` | 加入可学习 32D 点级尺度度量 | 17,419 | 175.54 MB |

三个模型均为七个本地文件的完整目录，已通过 cluster Conda/CUDA 的独立加载、前反向、语言 padding 不变性和新增参数梯度测试。完整结构与训练命令见 `docs/cluster_attention_research_plan.md` 第 13.2 节。
