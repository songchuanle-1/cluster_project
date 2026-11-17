# 当前模型变体、实验结果与跨设备研究交接

> 快照时间：2026-07-15 07:39 CST  
> 项目：ScanRefer 3D Referring Expression Segmentation  
> 当前工作区：`/data/songcl/3dres/Cluster_project2`  
> 说明：本文中的“轮数”是日志中已经完成验证并产生 mIoU 的轮数。很多实验在下一轮训练中途停止，不能视为完整 50 epoch 实验。

## 1. 当前结论

1. 当前全项目最高单次验证结果是 `model_base1_quard2_c2f_enc_lite_posA`：`0.500940 @ epoch 15`。
2. `c2f_enc_lite_l1` 达到 `0.500636`；`quard2_nomask` 达到 `0.499740`，且最后 5 轮均值最高，为 `0.496754`。
3. 当前 GBCR 几何路由主线最高是正在运行的 `gbcr_langc2f_scale_l1`：`0.496725 @ epoch 16`，仍未超过 PosA。
4. GBCR 中，Adaptive 与 Scale 的高值区间比较稳定；单纯加入语言粗路由和父上下文 query 没有继续提高 best：

```text
Adaptive   0.496102
LangRoute  0.495638
LangC2F    0.495042
Scale      0.496725（运行中快照）
```

5. 当前证据支持两条不同路线：

```text
C2F Enc Lite：decoder/query 引导 cluster 路由，cluster message 更新 inst feature
GBCR：不使用 proposal query，cluster-to-cluster 几何路由后直接增强 inst feature
```

两条路线不能混为同一种结构。当前最高指标来自 C2F Enc Lite PosA；GBCR 更符合最初“通过几何层次 cluster attention 更新 inst feature”的方法动机。

## 2. 统一基线与训练协议

### 2.1 Baseline

`model_base1` 的主要流程：

```text
Sparse 3D U-Net
 -> superpoint feature
 -> instance feature [B,N,256]

RoBERTa
 -> language feature [B,L,256]

SamplingModule
 -> proposal query [B,128,256]

6 x (Encoder language-instance interaction
     + Decoder query refinement
     + iterative prediction)
```

Baseline 没有显式 hierarchical cluster attention。

### 2.2 共同配置

| 项目 | 当前设置 |
|---|---|
| 数据集 | ScanRefer / ScanNetV2 |
| 随机种子 | 1999 |
| 训练 epoch | 50（多数运行未跑满） |
| train batch size | 2 |
| val batch size | 1 |
| 优化器 | AdamW |
| 主学习率 | `1e-4` |
| weight decay | `5e-4` |
| scheduler | PolyLR, `max_iters=70`, `power=4.0` |
| 统一维度 | 256 |
| encoder/decoder 层数 | 6 |
| cluster 层次 | `N -> 256 -> 64 -> 8` |
| text encoder | frozen RoBERTa |

注意：`train.epochs=50` 与 `lr_scheduler.max_iters=70` 不一致，但现有主要结果都使用该协议。正式重跑时先保持一致，避免把 scheduler 变化与结构收益混淆。

## 3. 方法主线 A：C2F Encoder Lite

### 3.1 基本层次结构

```text
N superpoints
 -> FPS + nearest assignment -> 256 fine clusters
 -> FPS + nearest assignment -> 64 middle clusters
 -> FPS + nearest assignment -> 8 coarse clusters
```

cluster token 使用级联均值聚合：

```text
C256 = scatter_mean(inst_feats, point_to_256)
C64  = scatter_mean(C256, child256_to_64)
C8   = scatter_mean(C64, child64_to_8)
```

C2F Lite 从粗到细执行 query-cluster routing，沿父层 top-k 展开子层候选。最终使用几何映射把 cluster message 回写到 point/instance feature。Lite 版移除了高显存的 `N x Q` 点级全注意力回读。

### 3.2 已运行变体结构

| 变体 | 结构差异 | 研究目的 |
|---|---|---|
| `model_base1_quard2_nomask` | 并行多尺度 cluster context，无 C2F mask 路由 | 验证 cluster token 本身是否有效 |
| `model_base1_quard2_c2f_enc` | 较早、较重的 encoder 内 C2F cluster attention | 验证层次上下文注入 encoder |
| `model_base1_quard2_c2f_pq` | per-query 独立路由 | 不同 query 选择不同 cluster 路径 |
| `model_base1_quard2_c2f_enc_lite` | 直接几何 gather 回写，只增强 inst feature，后两层注入 | 轻量稳定主线 |
| `..._lite_l1/l3/l4` | cluster 注入 1/3/4 个后层 | 检查注入深度 |
| `..._lite_init0` | 修改 residual gate 初始化 | 检查初始注入强度 |
| `..._lite_noroute` | 去掉或弱化 C2F route mask | 判断层次路由的独立贡献 |
| `..._lite_posA` | `LLA -> LIA -> Cluster -> ILA` | 调整 cluster 在 encoder 内的位置 |
| `..._lite_posB/posC` | 其他 cluster 注入位置 | 位置消融 |
| `..._lite_cag` | per-point content-adaptive gate | 点级控制 cluster 更新强度 |
| `..._lite_cfe` | cluster feature enhancement 探索 | 增强 cluster 表示交互 |
| `..._lite_agg` | 学习式点权聚合 | 替代 lvl0 scatter mean |
| `..._lite_qcond` | query-conditioned aggregation | 用 query 语义重聚合 cluster |
| `..._lite_attnpool` | attention pooling | 学习簇内点权重 |
| `..._lite_prune` | 动态 token 剪枝 | 降低 cluster attention 成本 |

### 3.3 PosA 结构

PosA 是当前最高指标版本：

```text
T1 = LanguageSelfAttention(T)
T2 = LanguageReadsInstance(query=T1, key/value=I)
M  = C2FClusterAttention(I, decoder_query, cluster_bank)
I1 = I + sigmoid(gate) * M
I2 = InstanceReadsLanguage(query=I1, key/value=T2)
T3 = FFN(T2)
```

重要边界：PosA 中 decoder query 参与 cluster attention 的路由或消息构建，但最终更新对象是 `inst_feats`。

实现：`Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA/`  
配置：`Cluster/configs/Quard/model_base1_quard2_c2f_enc_lite_posA.yaml`

## 4. 方法主线 B：GBCR Inst-Feature Routing

GBCR 的目标与原始动机一致：只根据点云几何层次和 cluster feature 建立粗到细关系，最终更新 `inst_feats`，不使用 proposal query。

### 4.1 共同结构

```text
geometry hierarchy: N -> 256 -> 64 -> 8

8-level coarse attention
 -> top-k coarse regions
 -> 64-level local/routed candidate budget
 -> top-k route
 -> 256-level local/routed candidate budget
 -> multi-scale context mapped to N points
 -> residual update inst_feats
```

当前推荐 top-k 顺序按 `[256,64,8]` 记录为 `[8,6,3]`：实际执行顺序是 `8 top-3 -> 64 top-6 -> 256 top-8`。

### 4.2 已运行 GBCR 及前置变体

| 变体 | 结构 | 状态/作用 |
|---|---|---|
| `cluster_fixed_ctx_l1` | 固定 cluster mean context 回写 | 早期平滑基线 |
| `cluster_fixed_ctx_l1_ls` | fixed context + LayerScale | 稳定残差基线 |
| `cluster_hier_add_l1` | scalar top-down hierarchy | 只运行 3 个验证轮次 |
| `cluster_hier_content_l1` | cosine content gate 控制 parent 传播 | 只运行 2 个验证轮次 |
| `hca_coarse_l1` | 8 层 attention，向下 parent broadcast | 未产生有效验证 mIoU |
| `hca_c2f_parent_l1` | 8 attention + parent/self C2F | 未产生有效验证 mIoU |
| `topk_c2f_cosine_l1` | 原始 top-k C2F cosine 路由 | 因显存问题未形成有效结果 |
| `topk_c2f_bottleneck_l1` | 低维 bottleneck 路由 | 9 个验证轮次 |
| `gbcr_balanced_l1` | 固定候选预算，几何粗到细路由 | 第一个稳定正收益 GBCR |
| `gbcr_local_l1` | 强制保留 own/local candidates | 提高高值区间稳定性 |
| `gbcr_pointgate_l1` | 随机初始化 point gate | 12 轮提前停止，不建议继续 |
| `gbcr_adaptive_l1` | local/routed 独立配额 + shared 32D Q/K + point-scale fusion + identity-init PointGate | 当前几何 GBCR 基准 |
| `gbcr_langroute_l1` | Adaptive + language-targeted 8-level score | 语言只引导粗层目的区域 |
| `gbcr_langc2f_l1` | LangRoute + parent context 条件化 Q64/Q256 | 更完整的语义 C2F ranking |
| `gbcr_langc2f_scale_l1` | LangC2F + learnable 32D point-scale metric | 当前正在运行 |

### 4.3 Adaptive

```text
8 full attention, route top-3
64 local4 + routed12, route top-6
256 local4 + routed20, route top-8
shared Linear(256,32) Q/K
raw 256D cosine chooses context256/context64/context8 per point
PointGate: Linear(256,1), weight=0, bias=4
message = LayerNorm(fused_context - point)
inst = inst + signed_layerscale * message
```

Adaptive best checkpoint 的已知参数：

```text
signed LayerScale = -0.1795
routing temperature [256,64,8] = [0.3677,0.4856,0.5612]
scale bias [256,64,8] = [-0.0103,-0.4215,+0.1027]
```

负 LayerScale 表明实际更新更接近 `point - context` 的 detail sharpening。64 层被明显压低，更像路由桥。

### 4.4 LangRoute

```text
L = masked_mean(lang_feats)
visual(i,j) = cos(Q(F8_i), K(F8_j))
lang_relevance(j) = cos(Q(L), K(F8_j))
score8(i,j) = visual(i,j) + alpha_lang * lang_relevance(j)
```

随后仍执行 `8 -> 64 -> 256` 几何配额路由，只更新 inst feature。新增约 1 个参数。

实现：`Cluster/framework/model/Quard_model/model_base1_gbcr_langroute_l1/`

### 4.5 LangC2F

在 LangRoute 上增加：

```text
query64  = f64  + beta64  * context8[parent8]
query256 = f256 + beta256 * context64[parent64]
```

父 context 只条件化 query，candidate value 仍是原始 `f64/f256`。新增参数累计约 3 个。

实现：`Cluster/framework/model/Quard_model/model_base1_gbcr_langc2f_l1/`

### 4.6 LangC2FScale

在 LangC2F 上将固定 raw cosine 尺度选择改成可学习 32D 度量：

```text
point_route = normalize(Q(point.detach()))
context_route_l = normalize(scale_affine_l(K(context_l.detach())))
scale_weight = softmax(dot(point_route,context_route_l)/tau + bias)
fused = sum(scale_weight_l * context_l)
```

cluster 模块参数量约 17,419。12k 点合成模块前反向峰值显存约 175.54 MB；同口径 Adaptive 为 150.24 MB。

实现：`Cluster/framework/model/Quard_model/model_base1_gbcr_langc2f_scale_l1/`  
配置：`Cluster/configs/Quard/model_base1_gbcr_langc2f_scale_l1.yaml`

## 5. Base1 主要结果总表

| 排名 | 模型 | 验证轮数 | Best mIoU | Best Epoch | 最后 mIoU | 状态 |
|---:|---|---:|---:|---:|---:|---|
| 1 | `c2f_enc_lite_posA` | 24 | **0.500940** | 15 | 0.491166 | Epoch 25 中断 |
| 2 | `c2f_enc_lite_l1` | 26 | 0.500636 | 21 | 0.488952 | Epoch 27 中断 |
| 3 | `quard2_nomask` | 20 | 0.499740 | 16 | **0.496088** | Epoch 21 中断 |
| 4 | `c2f_enc_lite` | 22 | 0.499236 | 13 | 0.487588 | 旧有效 run；新 run 仅初始化 |
| 5 | `c2f_enc_lite_l3` | 24 | 0.498062 | 18 | 0.491637 | Epoch 25 中断 |
| 6 | `c2f_enc_lite_noroute` | 27 | 0.497197 | 17 | 0.481237 | Epoch 28 中断 |
| 7 | `gbcr_langc2f_scale_l1` | 29 | 0.496725 | 16 | 0.487149 | **仍在 Epoch 30 训练** |
| 8 | `c2f_enc_lite_cag` | 18 | 0.496191 | 13 | 0.495356 | Epoch 19 中断 |
| 9 | `gbcr_adaptive_l1` | 22 | 0.496102 | 17 | 0.486771 | Epoch 23 中断 |
| 10 | `gbcr_langroute_l1` | 21 | 0.495638 | 15 | 0.486675 | Epoch 22 中断 |
| 11 | `c2f_enc_lite_posB` | 21 | 0.495317 | 13 | 0.488426 | Epoch 22 中断 |
| 12 | `gbcr_balanced_l1` | 38 | 0.495160 | 20 | 0.482246 | Epoch 39 中断 |
| 13 | `c2f_enc_lite_posC` | 16 | 0.495154 | 13 | 0.493695 | Epoch 17 中断 |
| 14 | `gbcr_langc2f_l1` | 18 | 0.495042 | 15 | 0.485513 | Epoch 19 中断 |
| 15 | `c2f_enc_lite_init0` | 23 | 0.494883 | 19 | 0.489002 | Epoch 24 中断 |
| 16 | `gbcr_local_l1` | 33 | 0.494311 | 19 | 0.483982 | Epoch 34 中断 |
| 17 | `c2f_enc_lite_l4` | 25 | 0.493136 | 20 | 0.488858 | Epoch 26 中断 |
| 18 | `c2f_enc_lite_cfe` | 15 | 0.490138 | 13 | 0.485398 | Epoch 16 中断 |
| 19 | `model_base1` | 30 | 0.489449 | 15 | 0.473846 | Epoch 31 中断 |
| 20 | `quard2_c2f_enc` | 15 | 0.489093 | 12 | 0.481167 | Epoch 16 中断 |
| 21 | `quard2_c2f_pq` | 14 | 0.486376 | 13 | 0.480524 | Epoch 15 中断 |
| 22 | `gbcr_pointgate_l1` | 12 | 0.484118 | 11 | 0.482211 | Epoch 13 中断 |
| 23 | `topk_c2f_bottleneck_l1` | 9 | 0.479378 | 8 | 0.478777 | Epoch 10 中断 |
| 24 | `cluster_fixed_ctx_l1_ls` | 10 | 0.478954 | 10 | 0.478954 | Epoch 11 中断 |
| 25 | `cluster_fixed_ctx_l1` | 12 | 0.476040 | 12 | 0.476040 | Epoch 13 中断 |
| 26 | `c2f_enc_lite_attnpool` | 7 | 0.471145 | 7 | 0.471145 | 早期停止 |
| 27 | `cluster_hier_add_l1` | 3 | 0.404109 | 3 | 0.404109 | 结果不足 |
| 28 | `cluster_hier_content_l1` | 2 | 0.365931 | 2 | 0.365931 | 结果不足 |

未产生可比较验证 mIoU：`hca_coarse_l1`、`hca_c2f_parent_l1`、`topk_c2f_cosine_l1`、`lite_agg`、`lite_qcond`、`lite_prune` 以及多次 profile/启动失败日志。

## 6. 高值区间与公平比较

### 6.1 代表模型统计

| 模型 | Best | Top-5 均值 | Last-5 均值 | Epoch 14-18 均值 |
|---|---:|---:|---:|---:|
| Baseline | 0.489449 | 0.487143 | 0.474802 | 0.485234 |
| C2F Lite | 0.499236 | 0.496442 | 0.493145 | 0.492499 |
| PosA | **0.500940** | 0.493933 | 0.490955 | 0.492590 |
| Lite-L1 | 0.500636 | 0.495556 | 0.491864 | 0.490267 |
| Nomask | 0.499740 | **0.497062** | **0.496754** | **0.494022** |
| GBCR Adaptive | 0.496102 | 0.493286 | 0.489306 | 0.491758 |
| GBCR LangRoute | 0.495638 | 0.490483 | 0.485984 | 0.489064 |
| GBCR LangC2F | 0.495042 | 0.488477 | 0.486474 | 0.486474 |
| GBCR Scale | 0.496725 | 0.493241 | 0.488481 | 0.491884 |

### 6.2 结果解释

- PosA 给出最高单点，但 Nomask 的高值平台最稳定。后续正式主模型筛选不能只看 best。
- Lite 与 PosA 都比 baseline 提高约 `+0.010~0.0115`，说明早期 C2F Encoder Lite 路线仍是当前最强路线。
- Adaptive/Scale 比 baseline 稳定提高约 `+0.0067~0.0073`，证明纯 inst-feature GBCR 有效，但暂未达到 C2F Lite。
- LangRoute 相比 Adaptive best 下降 `0.000464`；LangC2F 下降 `0.001060`。目前没有证据表明语言条件化路由提高整体指标。
- Scale 相比 Adaptive best 提高 `0.000623`，低于预先设定的 `+0.002` 有效改进阈值。应等待完整训练后再决定是否保留。
- 所有结果当前均为 seed 1999 的单次运行，不能报告统计显著性。

## 7. Legacy Model-Base2 结果

这些版本属于较早的 model_base2/query 路线，指标整体低于 base1 主线，保留用于历史参考：

| 模型 | 验证轮数 | Best mIoU | Best Epoch | 最后 mIoU |
|---|---:|---:|---:|---:|
| `model_base2_quard2_c2f` | 46 | 0.468977 | 15 | 0.451080 |
| `model_base2_quard2_c2f_enc` | 20 | 0.466396 | 12 | 0.462193 |
| `model_base2_quard2_l1` | 34 | 0.465535 | 14 | 0.452341 |
| `model_base2_quard2_c2f_enc_gm1` | 16 | 0.465241 | 13 | 0.451330 |
| `model_base2_quard2_c2f_pq` | 50 | 0.464638 | 12 | 0.446106 |
| `model_base2` | 24 | 0.464082 | 17 | 0.457963 |
| `model_base2_quard2_nomask` | 30 | 0.463323 | 21 | 0.455478 |

后续新设备研究不建议优先恢复 model_base2 分支。

## 8. 精确日志与 Checkpoint 索引

### 8.1 当前关键日志

```text
Baseline:
Cluster_checkpoints/model_base1/20260627_174353/20260627_174353.log

C2F Lite:
Cluster_checkpoints/model_base1_quard2_c2f_enc_lite/20260703_150030/20260703_150030.log

PosA:
Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA/20260708_180536/20260708_180536.log

Lite-L1:
Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_l1/20260706_075740/20260706_075740.log

Nomask:
Cluster_checkpoints/model_base1_quard2_nomask/20260704_130243/20260704_130243.log

GBCR Adaptive:
Cluster_checkpoints/model_base1_gbcr_adaptive_l1/20260713_075411/20260713_075411.log

GBCR LangRoute:
Cluster_checkpoints/model_base1_gbcr_langroute_l1/20260713_210702/20260713_210702.log

GBCR LangC2F:
Cluster_checkpoints/model_base1_gbcr_langc2f_l1/20260714_072105/20260714_072105.log
```

### 8.2 Scale 当前实际路径

Scale 训练进程工作目录：

```text
/home/songcl/project
```

但日志与 checkpoint 实际写入：

```text
/data/songcl/Cluster_project/Cluster_checkpoints/
  model_base1_gbcr_langc2f_scale_l1/20260714_174119/
```

关键文件：

```text
best.pth
last.pth
20260714_174119.log
model_base1_gbcr_langc2f_scale_l1.yaml
```

这套结果不在当前 `Cluster_project2/Cluster_checkpoints` 内。迁移前必须单独复制，不能只打包当前工作区。

## 9. 跨设备迁移清单

### 9.1 必须复制

```text
Cluster/framework/model/Quard_model/
Cluster/configs/Quard/
Cluster/tools/
Cluster/dataset/
Cluster/logs_analysis/
docs/
Cluster_checkpoints/ 中保留的 best.pth、last.pth 和日志
/data/songcl/Cluster_project/.../gbcr_langc2f_scale_l1/ 当前 Scale 运行目录
```

下载的相关论文位于：

```text
docs/papers/cluster_attention/
```

### 9.2 当前环境

```text
Conda env: cluster
Python: 3.10.20
PyTorch: 2.8.0+cu128
CUDA build: 12.8
GPU: NVIDIA GeForce RTX 5090
NumPy: 1.26.4
SciPy: 1.15.3
PyYAML: 6.0.3
```

还需要项目已有的 CUDA/稀疏点云依赖：`spconv`、`pointnet2`、`pointgroup_ops`、`torch_scatter`、`gorilla`、`transformers` 等。迁移时建议在原设备导出完整环境：

```bash
conda env export -n cluster > cluster_environment.yml
conda list -n cluster --explicit > cluster_explicit.txt
```

### 9.3 必须修改的硬编码路径

所有 YAML 至少检查：

```yaml
work_dir: /new/path/Cluster_checkpoints
train:
  pretrain: /new/data/path/sp_unet_backbone.pth
data:
  train:
    data_root: /new/data/path/
  val:
    data_root: /new/data/path/
model:
  data_root: /new/data/path/
```

当前旧路径主要是：

```text
/data/songcl/3dres/Cluster_project2/Cluster_checkpoints
/home/songcl/data/data/
/home/songcl/data/data/sp_unet_backbone.pth
```

### 9.4 模型加载约定

`framework.resolve_network()` 根据 YAML 文件 basename 加载模型：

```text
configs/Quard/<model_name>.yaml
 -> framework.model.Quard_model.<model_name>.Network
```

因此配置文件名必须与模型目录名完全一致。每个新变体目录保留完整文件，不依赖其他模型目录。

Gorilla 的 `Criterion` registry 在同一个 Python 进程连续 import 多个完整模型时可能重复注册报错。实际训练每个配置使用独立 Python 进程即可。

## 10. 新设备运行命令

进入 `Cluster` 目录：

```bash
cd /new/path/Cluster_project2/Cluster
```

运行 PosA：

```bash
conda run -n cluster python tools/train.py \
  configs/Quard/model_base1_quard2_c2f_enc_lite_posA.yaml \
  --gpu_ids 0 --num_gpus 1
```

运行 GBCR Adaptive：

```bash
conda run -n cluster python tools/train.py \
  configs/Quard/model_base1_gbcr_adaptive_l1.yaml \
  --gpu_ids 0 --num_gpus 1
```

运行 GBCR Scale：

```bash
conda run -n cluster python tools/train.py \
  configs/Quard/model_base1_gbcr_langc2f_scale_l1.yaml \
  --gpu_ids 0 --num_gpus 1
```

从 checkpoint 恢复：

```bash
conda run -n cluster python tools/train.py \
  configs/Quard/model_base1_gbcr_langc2f_scale_l1.yaml \
  --resume /new/path/to/last.pth \
  --gpu_ids 0 --num_gpus 1
```

## 11. 日志分析

现有分析脚本：

```text
Cluster/logs_analysis/analyze_logs.py
```

运行示例：

```bash
conda run -n cluster python Cluster/logs_analysis/analyze_logs.py \
  --log_list Cluster/logs_analysis/gbcr_current_comparison/log_list.txt \
  --output_dir Cluster/logs_analysis/gbcr_current_comparison
```

输出包括：

```text
epoch_results.csv
summary_stats.csv
comparison_plot.png
comparison_first20.png
```

Scale 当前日志位于另一个项目路径，迁移或重新分析时需要手动加入 `log_list.txt`。

## 12. 后续研究优先级

### 第一优先级：完成当前 Scale 运行

记录 50 epoch 的最终结果、Top-5、Last-5，并复制外部路径中的 `best.pth/last.pth/log`。如果最终 best 仍小于 `0.498`，不再继续叠加更复杂的语言/父层路由。

### 第二优先级：统一重跑最强候选

使用同一设备和完全相同协议运行：

```text
model_base1
c2f_enc_lite_posA
quard2_nomask
GBCR Adaptive 或 Scale（二选一）
```

至少跑满 30 epoch，保留 best。最终候选做 3 seeds，报告 `mean +/- std`。

### 第三优先级：融合两条主线前先做诊断

当前不能直接认定“语言路由更好”。建议记录：

```text
8/64/256 attention entropy
语言 relevance 对 coarse top-k 的改变比例
local/routed candidate 命中率
point-scale 平均权重与类别/物体大小关系
signed LayerScale、temperature、scale bias 轨迹
```

若语言只改变极少 route，增大语言分支才有意义；若改变很多但指标下降，应保留纯几何 Adaptive。

### 当前建议主模型

```text
追求最高指标：C2F Enc Lite PosA / Nomask
坚持纯 inst-feature 几何方法：GBCR Adaptive，等待 Scale 最终结果
暂不优先：LangRoute、LangC2F、复杂 attention pooling/aggregation
```

## 13. 相关文档

```text
docs/model_variants_results_summary.md
docs/model_base1_quard2_c2f_enc_lite_posA_structure.md
docs/cluster_attention_research_plan.md
docs/cluster_attention_literature_research.md
Cluster/logs_analysis/gbcr_current_comparison/analysis.md
```

本文档是截至快照时间的独立交接版本。后续设备应在 Scale 运行结束后更新第 5、6、8、12 节。
