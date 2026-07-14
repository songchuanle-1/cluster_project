# Quard Model Variants 演进文档

## 总览

所有变体共享同一个基础架构：**SparseConv3D U-Net backbone → FPS 采样 → 迭代 Transformer Encoder-Decoder → 匈牙利匹配损失**。

变体之间的差异集中在两个维度：
1. **基础架构（base1 vs base2）**：Encoder 层是否包含 `ila`（language→instance 交叉注意力）
2. **Cluster Attention 设计**：层级聚类注意力的路由方式、注入位置、轻量化策略

```
基础架构分叉:
  base2 (无 ila)                    base1 (有 ila)
  ├── quard → quard0 → quard1       ├── nomask (并行多尺度)
  │              └── quard2          ├── c2f (coarse-to-fine)
  │                  ├── l1          │   └── c2f_pq (per-query)
  │                  ├── l1_nomask   └── c2f_enc (嵌入Encoder)
  │                  ├── nomask          └── c2f_enc_lite ★ 轻量优化
  │                  ├── c2f
  │                  └── c2f_pq
  ├── quard_bottleneck
  └── c2f_enc → gm1
               └── lite
```

---

## 基础架构：base1 vs base2

### 核心差异：`ila` (Instance-to-Language Attention)

| | base1 | base2 |
|---|:---:|:---:|
| `self.ila` | ✅ `CrossAttentionLayer` | ❌ 注释掉 |
| Encoder_layer 信息流 | `lla → [cluster] → lia → ila → FFN` | `lla → [cluster] → lia → FFN` |

**ila 的作用**：在 `lia`（inst→lang 交叉注意力）之后，`ila` 反向将语言信息注入回实例特征：

```python
# base1 Encoder_layer.forward:
lang_feats = self.lla(lang_feats, lang_masks)           # 语言自注意力
# [可选: cluster attention]
lang_feats, _, _ = self.lia(inst_feats, lang_feats, ...) # 场景→语言
inst_feats, _, _ = self.ila(lang_feats, inst_feats, lang_masks, None)  # ★ 语言→场景
lang_feats = self.lia_ffn(lang_feats)
```

base2 缺少 `ila`，语言信息只能通过 `lia` 单向流向语言特征，再通过 decoder 的 `qia` 间接影响实例。

---

## Cluster Attention 注入位置

变体间第二个核心差异是 Cluster Attention 在整体架构中的**位置**：

### 位置 A：外挂式（encoder-decoder 之间）

```
Encoder_layer:              DEC 循环:
  lla(lang)                   for each layer:
  lia(inst,lang)                encoder_layer(...)
  [ila (base1)]                 cluster_att(inst, query)  ← 外挂
  FFN                           decoder_layer(...)
```

使用此位置的变体：`nomask`, `c2f`, `c2f_pq`

### 位置 B：嵌入式（Encoder_layer 内部）

```
Encoder_layer:
  lla(lang)
  [cluster_att]  ← 嵌入
  lia(inst,lang)
  [ila (base1)]
  FFN
```

使用此位置的变体：`c2f_enc`, `c2f_enc_gm1`, `c2f_enc_lite`, `bottleneck`

### 位置 C：Encoder 循环之前（早期）

```
cluster_att(inst, query)  ← 循环前执行一次
for each layer:
  encoder_layer(...)
```

使用此位置的变体：`model_base2` (CUDA gather-attn), `quard`

---

## base2 系列变体

### model_base2 (Baseline)

**文件**: `model_base2/`

- **无 ila**，Encoder_layer 仅含 `lla → lia → FFN`
- Cluster Attention 使用 CUDA 扩展 (`score_computation_cuda` + `value_aggregation_cuda`)
- 在 encoder 循环**之前**执行**一次** cluster attention
- 仅更新 `inst_feats`（不碰 `query`）
- 层级配置：`cluster_layer_nums=[256, 64, 8]`

**局限**：cluster 信息只注入一次，后续 encoder 层无增量；O(N²) 稠密布尔 mask 构建

---

### model_base2_quard

**文件**: `model_base2_quard/`

| 改动 | 说明 |
|------|------|
| 循环内多层执行 | cluster attention 在前 N 层每层执行（`cluster_att_num_layers=2`） |
| 门控机制 | 每层可学习 gate：`gate = tanh(cluster_att_gates[layer_i])`，初始化为 0 |
| 稀疏候选构建 | `build_candidate_indices()` 替代 O(N²) 稠密布尔 mask，O(N) |
| Bug 修复 | `layer_nums` 原地修改、`cluster_ids` 类型错误、`topk > tensor_size` 越界等 |

**注入位置**：encoder 层之前（先 cluster → 再 encoder → 再 decoder）

---

### model_base2_quard0

**文件**: `model_base2_quard0/`

**核心创新：query-conditioned cluster routing**

完全重写 `Cluster_Attn`，从 CUDA gather-attention 切换为**纯 PyTorch Einsum** 实现。

```
query → select top-k cluster → attend cluster → query context
                                                      ↓
point ←────── route query context to points ──────────┘
```

| 改动 | 说明 |
|------|------|
| query 参与路由 | 每个 query 独立选择最相关的 top-k 簇 |
| cluster → query 注意力 | query 在选中的簇 token 上做多头注意力 |
| query → point 回读 | 点通过已被簇更新过的 query 路由读回信息 |
| 双输出 | `{'point': ..., 'query': ...}` |
| 去除 CUDA 扩展依赖 | 纯 PyTorch 实现 |

---

### model_base2_quard1

**文件**: `model_base2_quard1/`

| 改动 | quard0 → quard1 |
|------|-----------------|
| SharedClusterBank | 几何划分只算一次，各层复用 |
| cluster_att_num_layers | 1 → **6**（铺满所有层） |
| per_layer_topk_list | `[4,4,4,4]` → `[32,16,8]` |
| per-layer 独立参数 | 6 套独立 Cluster_Attn 实例 |
| matching_masks (P2) | `einsum('bqd,bnd->bqn')` 生成 cluster-guided mask logits |
| mask 融合 | `pred_masks += softplus(cluster_mask_fuse_logits) * matching_masks` |
| 注入位置 | 改为 decoder 之后 |

**冗余问题**（→ quard2 优化动机）：6 套独立参数、select/attend 重复投影、matching_masks 与 decoder pred_masks 高度同构

---

### model_base2_quard2

**文件**: `model_base2_quard2/`

三项核心优化：

| 优化 | quard1 → quard2 |
|------|-----------------|
| **P0: 共享参数** | 6 个独立 Cluster_Attn → **1 个共享单实例** |
| **P1: 合并 select+attend** | 两个方法各自投影 → **合并为一个方法，共享投影** |
| **P2: matching_masks 差异化** | 纯内积 → **投影后 Einsum（互补偏移）** |

**注入位置**：decoder 之后

---

### model_base2_quard2_l1

**文件**: `model_base2_quard2_l1/`

与 quard2 的唯一区别：cluster attention 仅在**第 1 层**执行（其余 5 层跳过）。保留 P2 matching_masks。

**设计意图**：测试 cluster attention 是否必须铺满 6 层。

---

### model_base2_quard2_l1_nomask

**文件**: `model_base2_quard2_l1_nomask/`

在 quard2_l1 基础上去掉 P2 matching_masks 全部组件。纯消融：单层 + 无 P2。

---

### model_base2_quard2_nomask

**文件**: `model_base2_quard2_nomask/`

与 quard2 的区别：完全移除 P2。与 quard2_l1_nomask 的区别：6 层而非 1 层。

**消融矩阵**：

| 变体 | 层数 | P2 matching_masks |
|------|:---:|:---:|
| quard2 | 6 | ✅ |
| quard2_l1 | 1 | ✅ |
| quard2_l1_nomask | 1 | ❌ |
| quard2_nomask | 6 | ❌ |

---

### model_base2_quard_bottleneck

**文件**: `model_base2_quard_bottleneck/`

另一条演进路线（不走 query 路由）：

| 改动 | 说明 |
|------|------|
| 瓶颈投影 | Linear(d_model→64) → LayerNorm → ReLU，在低维空间执行 cluster attention |
| 独立注意力头 | `cluster_att_nhead=4` |
| 嵌入式 | 作为 Encoder_layer 的结构性子模块，在语言注意力之前执行 |
| 减少簇数 | `cluster_layer_nums=[64,16]` |

---

### model_base2_quard2_c2f

**文件**: `model_base2_quard2_c2f_enc/../model_base2_quard2_c2f/` (注: base2 系列的 c2f 变体)

**核心创新：Coarse-to-Fine 级联注意力**

与 quard2 的「并行多尺度独立选 topk」不同，c2f 实现了**粗→细的层级路由**：

```
层2 (8 簇, 最粗)
  │  query 对 8 个簇全选 → full attention → 记录 topk 父簇
  ↓
层1 (64 簇)
  │  只看粗层选中父簇下的子簇 → attention → 记录更细 topk
  ↓
层0 (256 簇, 最细)
    只看上一轮选中中间簇下的子簇 → attention → 最终点回读
```

| 组件 | 说明 |
|------|------|
| 父子映射 | `child_cluster_maps`：粗簇中心→细簇中心的归属关系 |
| 级联候选 | `_child_mask()`：从父簇 id 取子簇 id，构建 bool mask |
| 级联聚合 | `build_cluster_feats`：scatter 逐级聚合 256→64→8 |

**计算量**：c2f 级联 ~10,820 vs 并行 ~69,696（约 84% 减少）

**注入位置**：encoder-decoder 之间（外挂）

---

### model_base2_quard2_c2f_pq

**Per-Query 独立路由**：把「所有 query 共享同一组粗层 topk」改为「每个 query 独立选择」：

| c2f (共享路由) | c2f_pq (per-query 路由) |
|---|---|
| `scores.mean(H) → topk` — 所有 query 选同样的簇 | `scores.sum(H) → topk(dim=-1)` — per-query 独立 |

---

### model_base2_quard2_c2f_enc

**文件**: `model_base2_quard2_c2f_enc/`

**核心创新：cluster_att 嵌入 Encoder_layer 内部**

```
旧(c2f 外挂):                 新(c2f_enc 嵌入):

encoder_layer:                encoder_layer:
  lla(lang)                     lla(lang)
  lia(inst,lang)                [cluster_att]  ← 嵌入
  FFN                           lia(inst,lang+cluster)
  ↓                             FFN
decoder_layer                   ↓
  ↓                           decoder_layer
[cluster_att] ← 外挂            ↓
```

| 特性 | 说明 |
|------|------|
| 无 ila | base2 架构 |
| Gate | `tanh`，per-layer 独立参数 |
| 修改 query | ✅ `query += gate * cluster_outputs['query']`（局部变量，不返回） |
| cluster_att_num_layers | 6（前 N 层：`layer_idx < cluster_att_num_layers`） |
| 点回读 | `_route_points`：N×Q 全注意力 |
| forward 返回 | `{'point': fm, 'query': fq}` |

---

### model_base2_quard2_c2f_enc_gm1

**文件**: `model_base2_quard2_c2f_enc_gm1/`

**与 c2f_enc 的唯一差异：gate 初始化值**

| | c2f_enc | c2f_enc_gm1 |
|---|---|---|
| `cluster_att_init` | `0.1` | **`-1.0`** |
| 初始 gate 值 | `tanh(0.1) ≈ 0.10` | **`tanh(-1.0) ≈ -0.76`** |
| 代码 | 完全相同 | 完全相同 |

**设计意图**：测试「负初始化」策略——让 cluster attention 初始为**抑制**状态，需要学习才能变为增强。可能避免早期训练中 cluster 噪声对特征的破坏。

---

### model_base2_quard2_c2f_enc_lite

**文件**: `model_base2_quard2_c2f_enc_lite/`

**在 c2f_enc 基础上的三项轻量化优化 (P0: A+B+D)**：

| 优化 | c2f_enc → c2f_enc_lite |
|------|------------------------|
| **A: 去掉 `_route_points`** | N×Q 全注意力 → **`_cluster_to_points` 直接 gather (O(N))** |
| **B: 不修改 query** | `query += gate * output['query']` → **删除**，仅更新 inst_feats |
| **B: sigmoid gate** | `tanh` [-1,1] → **`sigmoid`** [0,1]，更稳定 |
| **D: 仅后 N 层** | 前 6 层 → **后 2 层**（`layer_idx >= num_layer - N`） |

**hier_postprocess.py 差异**：

| 模块 | c2f_enc | c2f_enc_lite |
|------|---------|-------------|
| `_route_points` | ✅ | ❌ 删除 |
| `_cluster_to_points` | ❌ | ✅ 新增 |
| `query_k_linear`, `query_v_linear` | ✅ | ❌ 删除 |
| `query_out_proj` | ✅ | ❌ 删除 |
| `query_level_gate` | ✅ | ❌ 删除 |
| forward 返回 | `{'point', 'query'}` | `{'point'}` |
| forward 参数 | 无 `cluster_ids_list` | 新增 `cluster_ids_list` |

**`_cluster_to_points` 实现**：
```python
# 每个点通过 cluster_ids 直接 gather 所属 cluster token
for lvl in range(num_scales):
    ids_b = cluster_ids_list[lvl][b].long()
    msg[b, :n_valid] = cluster_feats[b, ids_b]  # O(N) 直接索引
# 多尺度融合：per-point softmax 权重
lw = softmax(level_gate(cat(point_feats, global_mean)))
fused = (stack * lw).sum(dim=-1)
```

---

## base1 系列变体

base1 系列 = base2 对应架构 + **ila (language→instance 交叉注意力)**

所有 base1 变体的 Encoder_layer 都包含 `self.ila = CrossAttentionLayer(d_model, nhead, dropout)`。

### model_base1 (纯 baseline)

**文件**: `model_base1/`

- **有 ila**，无 Cluster Attention
- Encoder_layer：`lla → lia → ila → FFN`
- 使用 CUDA 扩展的 ClusterAttention（循环前执行一次），但**不参与训练**（仅作为对比参考）

---

### model_base1_quard2_nomask

**文件**: `model_base1_quard2_nomask/`

**base1 + 并行多尺度 Cluster Attention（无 P2）**

| 特性 | 说明 |
|------|------|
| ila | ✅ |
| Cluster Attention 位置 | encoder-decoder 之间（外挂） |
| 路由方式 | 并行：每个尺度独立 query→all clusters（非 C2F） |
| Gate | `tanh` |
| 修改 query | ✅ |
| cluster_att_num_layers | 6 |
| P2 matching_masks | ❌ |
| `_route_points` | ✅ (N×Q) |

---

### model_base1_quard2_c2f

**文件**: `model_base1_quard2_c2f/`

**base1 + Coarse-to-Fine 级联 Cluster Attention（外挂）**

| 特性 | 说明 |
|------|------|
| ila | ✅ |
| Cluster Attention 位置 | encoder-decoder 之间（外挂） |
| 路由方式 | **Coarse-to-Fine**：8→64→256 级联 |
| Gate | `tanh` |
| 修改 query | ✅ |
| cluster_att_num_layers | 6 |
| `_route_points` | ✅ (N×Q) |
| `_child_mask` | ✅ |

---

### model_base1_quard2_c2f_pq

**文件**: `model_base1_quard2_c2f_pq/`

**base1 + C2F + Per-Query 独立路由（外挂）**

与 `base1_quard2_c2f` 的唯一差异在 `hier_postprocess.py`：

| c2f | c2f_pq |
|---|---|
| `scores.mean(H) → topk` — 共享路由 | `scores.sum(H) → topk(dim=-1)` — per-query 独立 |
| `_child_mask` 无去重 | `_child_mask` 内 `seen` set 去重 |

`dec.py` 与 `c2f` 完全相同。

---

### model_base1_quard2_c2f_enc

**文件**: `model_base1_quard2_c2f_enc/`

**base1 + C2F Cluster Attention（嵌入 Encoder_layer）**

| 特性 | 说明 |
|------|------|
| ila | ✅ |
| Cluster Attention 位置 | **Encoder_layer 内部**（嵌入） |
| 路由方式 | Coarse-to-Fine |
| Gate | `tanh`，`cluster_att_init=0.1` |
| 修改 query | ✅（局部变量，不返回） |
| cluster_att_num_layers | 6（**前 N 层**：`layer_idx < N`） |
| `_route_points` | ✅ (N×Q) |
| forward 返回 | `{'point': fm, 'query': fq}` |

**与 base2_quard2_c2f_enc 的唯一差异**：多了 `ila`。

---

### model_base1_quard2_c2f_enc_lite ★

**文件**: `model_base1_quard2_c2f_enc_lite/`

**base1 + C2F Cluster Attention（嵌入 + 轻量优化）**

这是 base1 纯 baseline 与轻量 Cluster Attention 的结合体。

| 特性 | 说明 |
|------|------|
| ila | ✅ |
| Cluster Attention 位置 | **Encoder_layer 内部**（嵌入） |
| 路由方式 | Coarse-to-Fine |
| Gate | **`sigmoid`** [0,1]，`cluster_att_init=0.1` |
| 修改 query | ❌ **不修改**，仅增强 inst_feats |
| cluster_att_num_layers | **2**（**后 N 层**：`layer_idx >= num_layer - N`） |
| 点回读 | **`_cluster_to_points`** (O(N) 直接 gather) |
| forward 返回 | `{'point': fm}` |

**相比 base1 (无 cluster) 的改动**：

```
base1 Encoder_layer:                    base1_c2f_enc_lite Encoder_layer:

lla(lang)                               lla(lang)
                                        [cluster_att]  ← 新增，仅后 2 层
lia(inst, lang)                         lia(inst, lang)
ila(lang, inst)                         ila(lang, inst)
FFN                                     FFN
```

**相比 base1_quard2_c2f_enc 的三项优化**：

| 优化 | base1_c2f_enc → base1_c2f_enc_lite |
|------|-------------------------------------|
| **A: 直接 gather** | `_route_points` (N×Q) → `_cluster_to_points` (O(N)) |
| **B: 不改 query + sigmoid** | tanh + query修改 → **sigmoid + 仅 inst_feats** |
| **D: 后 N 层** | 前 6 层 → **后 2 层** |

**实验结果**：

| 指标 | base1 (纯baseline) | base1_c2f_enc_lite | 提升 |
|------|:---:|:---:|:---:|
| mIoU | 0.4894 | **0.4992** | **+0.0098** |
| Acc@50 | 0.541 | **0.552** | **+0.011** |
| spmIoU | 0.451 | **0.463** | **+0.012** |

**结论**：在 base1 基础上加入轻量 Cluster Attention 后，所有指标提升，首次接近 0.50 mIoU。

---

## 全变体对比矩阵

| 变体 | 基础 | ila | Cluster 位置 | 路由方式 | Gate | 改 query | 层数 | 点回读 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **base1** | base1 | ✅ | ❌ | — | — | — | — | — |
| **base2** | base2 | ❌ | 循环前(1次) | CUDA gather | — | ❌ | 1次 | CUDA |
| base2_quard | base2 | ❌ | 循环前(多层) | CUDA gather | tanh | ❌ | 2 | CUDA |
| base2_quard0 | base2 | ❌ | 循环前(1次) | query路由 | — | ✅ | 1 | N×Q |
| base2_quard1 | base2 | ❌ | decoder后 | query路由+P2 | — | ✅ | 6 | N×Q |
| base2_quard2 | base2 | ❌ | decoder后 | query路由+P2' | — | ✅ | 6 | N×Q |
| base2_quard2_l1 | base2 | ❌ | decoder后 | query路由+P2' | — | ✅ | 1 | N×Q |
| base2_quard2_nomask | base2 | ❌ | decoder后 | query路由 | — | ✅ | 6 | N×Q |
| base2_quard_bottleneck | base2 | ❌ | Encoder内(嵌入) | CUDA gather | tanh | ❌ | 6 | CUDA |
| base2_c2f | base2 | ❌ | enc-dec间(外挂) | C2F | tanh | ✅ | 6 | N×Q |
| base2_c2f_pq | base2 | ❌ | enc-dec间(外挂) | C2F+PQ | tanh | ✅ | 6 | N×Q |
| **base2_c2f_enc** | base2 | ❌ | **Encoder内** | C2F | tanh | ✅ | 6 | N×Q |
| base2_c2f_enc_gm1 | base2 | ❌ | Encoder内 | C2F | tanh(init=-1) | ✅ | 6 | N×Q |
| base2_c2f_enc_lite | base2 | ❌ | Encoder内 | C2F | **sigmoid** | **❌** | **后2** | **gather** |
| **base1_nomask** | base1 | ✅ | enc-dec间(外挂) | 并行 | tanh | ✅ | 6 | N×Q |
| **base1_c2f** | base1 | ✅ | enc-dec间(外挂) | C2F | tanh | ✅ | 6 | N×Q |
| **base1_c2f_pq** | base1 | ✅ | enc-dec间(外挂) | C2F+PQ | tanh | ✅ | 6 | N×Q |
| **base1_c2f_enc** | base1 | ✅ | **Encoder内** | C2F | tanh | ✅ | 6 | N×Q |
| **base1_c2f_enc_lite** ★ | base1 | ✅ | **Encoder内** | C2F | **sigmoid** | **❌** | **后2** | **gather** |

---

## 进化路径图

```
=== base2 系列 (无 ila) ===

model_base2                          CUDA gather-attn, 循环前一次
  │
  ├─ quard                           循环内多层 + 门控 + 稀疏候选
  │   │
  │   ├─ quard0                      query 路由范式（纯 PyTorch）
  │   │   │
  │   │   └─ quard1                  SharedClusterBank + 6层 + P2 matching_masks
  │   │       │
  │   │       └─ quard2              P0共享参数 + P1合并投影 + P2互补匹配
  │   │           │
  │   │           ├─ quard2_l1       单层 + P2
  │   │           │   └─ l1_nomask   单层 - P2
  │   │           │
  │   │           ├─ quard2_nomask   6层 - P2
  │   │           │
  │   │           └─ quard2_c2f      C2F 级联 (外挂)
  │   │               │
  │   │               └─ c2f_pq      C2F + per-query (外挂)
  │   │
  │   └─ quard_bottleneck            瓶颈投影 + 嵌入式 per-layer
  │
  └─ c2f_enc                         C2F 嵌入 Encoder_layer (tanh, 6层, N×Q)
      ├─ c2f_enc_gm1                 同上, gate 初始化 = -1.0
      └─ c2f_enc_lite                sigmoid, 后2层, 不改query, 直接gather


=== base1 系列 (有 ila) ===

model_base1                          纯 baseline (lla→lia→ila→FFN)
  │
  ├─ quard2_nomask                   并行多尺度 (外挂, tanh, 6层)
  │
  ├─ quard2_c2f                      C2F 级联 (外挂, tanh, 6层)
  │   └─ c2f_pq                      C2F + per-query (外挂)
  │
  └─ quard2_c2f_enc                  C2F 嵌入 Encoder (tanh, 6层, N×Q)
      └─ c2f_enc_lite ★              sigmoid, 后2层, 不改query, 直接gather
```

---

## 运行命令

所有变体共用工具体系，配置文件在 `configs/Quard/` 下：

```bash
cd /data/songcl/3dres/Cluster_project2/Cluster

# 单卡
/home/songcl/.conda/envs/cluster/bin/python tools/train.py configs/Quard/<model>.yaml --gpu_ids 0

# 双卡
/home/songcl/.conda/envs/cluster/bin/python tools/train.py configs/Quard/<model>.yaml --num_gpus 2
```

框架会根据 yaml 文件名自动解析到对应的 `framework.model.Quard_model.<name>.Network`。

---

## 优化思路总结

### 从 base2 → base1_c2f_enc_lite 的演进逻辑

1. **添加 ila (base1)**：语言→实例双向信息流，弥补单向 lia 的信息瓶颈
2. **C2F 级联路由**：从并行多尺度（O(ΣK²)）到粗→细级联（O(K_coarse² + ...)），减少 84% 计算量
3. **嵌入式注入**：从外挂（encoder-decoder 之间）到嵌入（Encoder_layer 内部），让 cluster 信息在语言注意力之前丰富点云表征
4. **sigmoid gate**：从 tanh [-1,1] 到 sigmoid [0,1]，避免负 gate 导致的特征翻转
5. **不修改 query**：避免与 decoder 的 query 更新路径产生梯度冲突
6. **直接 gather**：用 O(N) 索引查找替代 O(N×Q) 全注意力，消除与 decoder qia 的冗余
7. **仅后 2 层**：前几层特征粗糙时 cluster tokens 质量差，后几层语义成熟后注入更有效
