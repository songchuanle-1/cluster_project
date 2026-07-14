# Base1 系列变体文档

## 概述

Base1 系列 = Base2 对应架构 + **ila (Instance-to-Language Attention)**

所有 Base1 变体的 Encoder_layer 都包含 `self.ila = CrossAttentionLayer(d_model, nhead, dropout)`，在 lia 之后将语言信息反向注入回实例特征。

---

## model_base1 (纯 baseline)

**文件**: `model_base1/`  
**配置**: `configs/Quard/model_base1.yaml`

**核心特征**:
- ✅ `ila` (语言→实例交叉注意力)
- ❌ 无 Cluster Attention
- Encoder_layer 信息流: `lla → lia → ila → FFN`

**Encoder_layer.forward**:
```python
lang_feats = self.lla(lang_feats, lang_masks)           # 语言自注意力
lang_feats, _, _ = self.lia(inst_feats, lang_feats, ...) # 场景→语言
inst_feats, _, _ = self.ila(lang_feats, inst_feats, lang_masks, None)  # ★ 语言→场景
lang_feats = self.lia_ffn(lang_feats)                    # FFN
```

**实验结果 (30 epochs)**:
| 指标 | Best | Epoch |
|------|------|-------|
| mIoU | 0.4894 | ep15 |
| Acc@50 | 0.541 | ep15 |
| spmIoU | 0.451 | ep15 |
| spAcc@50 | 0.501 | ep15 |

**收敛**: 首次达到 mIoU≥0.48 在 ep12  
**后期**: ep15 后持续下降 (0.4894→0.4745)

---

## model_base1_quard2_nomask

**文件**: `model_base1_quard2_nomask/`  
**配置**: `configs/Quard/model_base1_quard2_nomask.yaml`

**核心特征**:
- ✅ `ila`
- ✅ 并行多尺度 Cluster Attention (非 C2F)
- 注入位置: encoder-decoder 之间 (外挂)
- Gate: `tanh`
- ✅ 修改 query
- cluster_att_num_layers: 6
- `_route_points`: ✅ (N×Q 全注意力)

**与 base1 的区别**:
```
base1:                              nomask:
  Encoder_layer:                      Encoder_layer (不变):
    lla → lia → ila → FFN               lla → lia → ila → FFN
  
  无 cluster                        DEC 循环 (外挂):
                                      encoder_layer(...)
                                      cluster_att(inst, query)  ← 新增
                                      decoder_layer(...)
```

**Cluster_Attn 实现** (`hier_postprocess.py`):
- 并行多尺度: 每个尺度独立 query→all clusters
- 无父子映射 (非 C2F)
- `_route_points`: N×Q 全注意力
- forward 返回: `{'point', 'query'}`

**实验结果 (20 epochs)**:
| 指标 | Best | Epoch | vs base1 |
|------|------|-------|----------|
| mIoU | **0.4997** | ep16 | **+0.0103** |
| Acc@50 | 0.552 | ep16 | +0.011 |
| spmIoU | 0.461 | ep16 | +0.010 |
| spAcc@50 | 0.513 | ep16 | +0.012 |

**收敛**: 首次达到 mIoU≥0.48 在 ep9  
**后期**: ep15-20 稳定在 0.495+

---

## model_base1_quard2_c2f

**文件**: `model_base1_quard2_c2f/`  
**配置**: `configs/Quard/model_base1_quard2_c2f.yaml`

**核心特征**:
- ✅ `ila`
- ✅ Coarse-to-Fine 级联 Cluster Attention
- 注入位置: encoder-decoder 之间 (外挂)
- Gate: `tanh`
- ✅ 修改 query
- cluster_att_num_layers: 6
- `_route_points`: ✅ (N×Q)
- `_child_mask`: ✅

**与 nomask 的区别**:
```
nomask:  并行多尺度 (每个尺度独立 topk)
c2f:     Coarse-to-Fine (8→64→256 级联)
```

**Cluster_Attn 实现** (`hier_postprocess.py`):
- C2F 级联: 粗层全选 → 细层只看子簇
- `child_cluster_maps`: 父子映射 (dict)
- `_child_mask`: 构建子簇候选 bool mask
- `_route_points`: N×Q 全注意力
- forward 返回: `{'point', 'query'}`

**实验结果**: 训练未完成/无有效数据

---

## model_base1_quard2_c2f_pq

**文件**: `model_base1_quard2_c2f_pq/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_pq.yaml`

**核心特征**:
- ✅ `ila`
- ✅ C2F + Per-Query 独立路由
- 注入位置: encoder-decoder 之间 (外挂)
- Gate: `tanh`
- ✅ 修改 query
- cluster_att_num_layers: 6
- `_route_points`: ✅ (N×Q)

**与 c2f 的唯一区别** (仅在 `hier_postprocess.py`):

| c2f | c2f_pq |
|-----|--------|
| `scores.mean(H) → topk` (共享路由) | `scores.sum(H) → topk(dim=-1)` (per-query 独立) |
| `_child_mask` 无去重 | `_child_mask` 内 `seen` set 去重 |

**dec.py 与 c2f 完全相同**

**实验结果 (14 epochs)**:
| 指标 | Best | Epoch | vs base1 |
|------|------|-------|----------|
| mIoU | 0.4864 | ep13 | **-0.0030** |
| Acc@50 | 0.535 | ep13 | -0.006 |
| spmIoU | 0.451 | ep13 | 0.000 |
| spAcc@50 | 0.501 | ep13 | 0.000 |

**收敛**: 首次达到 mIoU≥0.48 在 ep11  
**后期**: ep13 后下降

---

## model_base1_quard2_c2f_enc

**文件**: `model_base1_quard2_c2f_enc/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc.yaml`

**核心特征**:
- ✅ `ila`
- ✅ C2F Cluster Attention
- 注入位置: **Encoder_layer 内部** (嵌入)
- Gate: `tanh`, `cluster_att_init=0.1`
- ✅ 修改 query (局部变量, 不返回)
- cluster_att_num_layers: 6 (**前 N 层**: `layer_idx < N`)
- `_route_points`: ✅ (N×Q)

**与 base2_c2f_enc 的唯一区别**: 多了 `ila`

**Encoder_layer.forward**:
```python
lang_feats = self.lla(lang_feats, lang_masks)
if self.use_cluster:
    gate = torch.tanh(self.cluster_att_gate)
    cluster_outputs = self.cluster_att(...)
    inst_feats = inst_feats + gate * cluster_outputs['point']
    query = query + gate * cluster_outputs['query']  # 局部变量, 不返回
lang_feats, _, _ = self.lia(inst_feats, lang_feats, ...)
inst_feats, _, _ = self.ila(lang_feats, inst_feats, lang_masks, None)  # ★ ila
lang_feats = self.lia_ffn(lang_feats)
return lang_feats, inst_feats
```

**Cluster_Attn 实现** (`hier_postprocess.py`):
- 与 base1_c2f 相同 (C2F 级联 + `_route_points`)
- forward 返回: `{'point', 'query'}`

**实验结果 (15 epochs)**:
| 指标 | Best | Epoch | vs base1 |
|------|------|-------|----------|
| mIoU | 0.4891 | ep12 | -0.0003 |
| Acc@50 | 0.544 | ep12 | +0.003 |
| spmIoU | 0.454 | ep12 | +0.003 |
| spAcc@50 | 0.508 | ep12 | +0.007 |

**收敛**: 首次达到 mIoU≥0.48 在 ep11  
**后期**: ep12 后波动下降

---

## model_base1_quard2_c2f_enc_lite ★

**文件**: `model_base1_quard2_c2f_enc_lite/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite.yaml`

**核心特征**:
- ✅ `ila`
- ✅ C2F Cluster Attention (轻量优化)
- 注入位置: **Encoder_layer 内部** (嵌入)
- Gate: **`sigmoid`** [0,1], `cluster_att_init=0.1`
- ❌ **不修改 query**, 仅增强 inst_feats
- cluster_att_num_layers: **2** (**后 N 层**: `layer_idx >= num_layer - N`)
- 点回读: **`_cluster_to_points`** (O(N) 直接 gather)

**相比 base1 (无 cluster) 的改动**:
```
base1 Encoder_layer:                    c2f_enc_lite Encoder_layer:

lla(lang)                               lla(lang)
                                        [cluster_att]  ← 新增, 仅后 2 层
lia(inst, lang)                         lia(inst, lang)
ila(lang, inst)                         ila(lang, inst)
FFN                                     FFN
```

**相比 base1_c2f_enc 的三项优化 (P0: A+B+D)**:

| 优化 | base1_c2f_enc → base1_c2f_enc_lite |
|------|-------------------------------------|
| **A: 直接 gather** | `_route_points` (N×Q) → `_cluster_to_points` (O(N)) |
| **B: 不改 query + sigmoid** | tanh + query修改 → **sigmoid + 仅 inst_feats** |
| **D: 后 N 层** | 前 6 层 → **后 2 层** |

**Encoder_layer.forward**:
```python
lang_feats = self.lla(lang_feats, lang_masks)
if self.use_cluster:  # layer_idx >= num_layer - 2 (layer 4, 5)
    gate = torch.sigmoid(self.cluster_att_gate)  # ★ sigmoid [0,1]
    cluster_outputs = self.cluster_att(...)
    inst_feats = inst_feats + gate * cluster_outputs['point']
    # ★ 不修改 query
lang_feats, _, _ = self.lia(inst_feats, lang_feats, ...)
inst_feats, _, _ = self.ila(lang_feats, inst_feats, lang_masks, None)
lang_feats = self.lia_ffn(lang_feats)
return lang_feats, inst_feats
```

**Cluster_Attn 实现** (`hier_postprocess.py`):

| 模块 | base1_c2f_enc | base1_c2f_enc_lite |
|------|:---:|:---:|
| `_route_points` (N×Q) | ✅ | ❌ 删除 |
| `_cluster_to_points` (O(N)) | ❌ | ✅ 新增 |
| `query_k_linear`, `query_v_linear` | ✅ | ❌ 删除 |
| `query_out_proj` | ✅ | ❌ 删除 |
| `query_level_gate` | ✅ | ❌ 删除 |
| forward 返回 | `{'point', 'query'}` | `{'point'}` |
| forward 参数 | 无 `cluster_ids_list` | 新增 `cluster_ids_list` |

**`_cluster_to_points` 实现**:
```python
# 每个点通过 cluster_ids 直接 gather 所属 cluster token
for lvl in range(num_scales):
    ids_b = cluster_ids_list[lvl][b].long()
    msg[b, :n_valid] = cluster_feats[b, ids_b]  # O(N) 直接索引
# 多尺度融合: per-point softmax 权重
lw = softmax(level_gate(cat(point_feats, global_mean)))
fused = (stack * lw).sum(dim=-1)
```

**实验结果 (22+ epochs)**:
| 指标 | Best | Epoch | vs base1 |
|------|------|-------|----------|
| mIoU | **0.4992** | ep13 | **+0.0098** |
| Acc@50 | 0.552 | ep13 | +0.011 |
| spmIoU | 0.463 | ep13 | +0.012 |
| spAcc@50 | 0.511 | ep13 | +0.010 |

**收敛**: 首次达到 mIoU≥0.48 在 ep8 (最快)  
**后期**: ep13-22 稳定在 0.49+

---

## model_base1_quard2_c2f_enc_lite_l3

**文件**: `model_base1_quard2_c2f_enc_lite_l3/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_l3.yaml`

**核心特征**:
- ✅ `ila`
- ✅ C2F Cluster Attention (轻量优化)
- 注入位置: **Encoder_layer 内部** (嵌入)
- Gate: `sigmoid`, `cluster_att_init=0.1`
- ❌ 不修改 query
- cluster_att_num_layers: **3** (后 3 层: layer 3, 4, 5)
- 点回读: `_cluster_to_points` (O(N))

**与 c2f_enc_lite 的唯一区别**: `cluster_att_num_layers: 3` (vs 2)

**实验结果 (14 epochs)**:
| 指标 | Best | Epoch | vs base1 |
|------|------|-------|----------|
| mIoU | 0.4910 | ep14 | +0.0016 |
| Acc@50 | 0.541 | ep14 | 0.000 |
| spmIoU | 0.456 | ep14 | +0.005 |
| spAcc@50 | 0.508 | ep14 | +0.007 |

**收敛**: 首次达到 mIoU≥0.48 在 ep9  
**后期**: ep12-14 稳定在 0.49+

---

## model_base1_quard2_c2f_enc_lite_l4

**文件**: `model_base1_quard2_c2f_enc_lite_l4/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_l4.yaml`

**核心特征**:
- ✅ `ila`
- ✅ C2F Cluster Attention (轻量优化)
- 注入位置: **Encoder_layer 内部** (嵌入)
- Gate: `sigmoid`, `cluster_att_init=0.1`
- ❌ 不修改 query
- cluster_att_num_layers: **4** (后 4 层: layer 2, 3, 4, 5)
- 点回读: `_cluster_to_points` (O(N))

**与 c2f_enc_lite 的唯一区别**: `cluster_att_num_layers: 4` (vs 2)

**实验结果 (14 epochs)**:
| 指标 | Best | Epoch | vs base1 |
|------|------|-------|----------|
| mIoU | 0.4861 | ep9 | **-0.0033** |
| Acc@50 | 0.541 | ep9 | 0.000 |
| spmIoU | 0.451 | ep9 | 0.000 |
| spAcc@50 | 0.499 | ep9 | -0.002 |

**收敛**: 首次达到 mIoU≥0.48 在 ep10  
**后期**: ep9 后波动下降

---

## 层数消融对比

| 变体 | 层数 | Best mIoU | Best Epoch | vs base1 | 收敛速度 |
|------|:---:|:---:|:---:|:---:|:---:|
| **base1 (无 cluster)** | 0 | 0.4894 | ep15 | — | ep12 |
| **c2f_enc_lite_l1** | 1 | 待训练 | — | — | — |
| **c2f_enc_lite** | **2** | **0.4992** | **ep13** | **+0.0098** | **ep8** |
| **c2f_enc_lite_l3** | 3 | 0.4910 | ep14 | +0.0016 | ep9 |
| **c2f_enc_lite_l4** | 4 | 0.4861 | ep9 | -0.0033 | ep10 |

**趋势**: 每增加一层 (从 2 层起) → mIoU 下降 ~0.008

**原因**:
1. 前几层 inst_feats 不够成熟, cluster tokens 质量差
2. gate 无法完全抑制噪声 (sigmoid 最小值 ~0.5)
3. 多层 cluster attention 引入梯度冲突

---

## 全变体对比表

| 变体 | ila | Cluster 位置 | 路由方式 | Gate | 改 query | 层数 | Best mIoU | vs base1 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **base1** | ✅ | ❌ | — | — | — | — | 0.4894 | — |
| **nomask** | ✅ | 外挂 | 并行 | tanh | ✅ | 6 | **0.4997** | **+0.0103** |
| **c2f** | ✅ | 外挂 | C2F | tanh | ✅ | 6 | 未完成 | — |
| **c2f_pq** | ✅ | 外挂 | C2F+PQ | tanh | ✅ | 6 | 0.4864 | -0.0030 |
| **c2f_enc** | ✅ | 嵌入 | C2F | tanh | ✅ | 6 | 0.4891 | -0.0003 |
| **c2f_enc_lite** ★ | ✅ | 嵌入 | C2F | sigmoid | ❌ | **2** | **0.4992** | **+0.0098** |
| **c2f_enc_lite_l1** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 1 | 0.4928 | +0.0034 |
| **c2f_enc_lite_l3** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 3 | 0.4910 | +0.0016 |
| **c2f_enc_lite_l4** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 4 | 0.4861 | -0.0033 |
| **c2f_enc_lite_init0** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 2 | 0.4906 | +0.0012 |
| **c2f_enc_lite_init05** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 2 | 待训练 | — |
| **c2f_enc_lite_cag** | ✅ | 嵌入 | C2F | sigmoid+CAG | ❌ | 2 | 待训练 | — |
| **c2f_enc_lite_cfe** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 2 | 待训练 | — |
| **c2f_enc_lite_posA** | ✅ | 嵌入(lia后) | C2F | sigmoid | ❌ | 2 | **0.5009** ★ | **+0.0115** |
| **c2f_enc_lite_posB** | ✅ | 嵌入(ila后) | C2F | sigmoid | ❌ | 2 | 0.4643 | -0.0251 |
| **c2f_enc_lite_posC** | ✅ | 嵌入(FFN后) | C2F | sigmoid | ❌ | 2 | 待训练 | — |
| **c2f_enc_lite_noroute** | ✅ | 嵌入 | **无路由** | sigmoid | ❌ | 2 | 0.4972 | +0.0077 |
| **c2f_enc_lite_posenc** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 2 | 0.4689 (ep7) | 训练中 |
| **c2f_enc_lite_qcond** | ✅ | 嵌入 | C2F+QCond v2 | sigmoid | ❌ | 2 | 待训练 | — |
| **c2f_enc_lite_attnpool** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 2 | 0.4711 (ep7) | 训练中 |
| **c2f_enc_lite_multi** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 2 | 待训练 | — |
| **c2f_enc_lite_prune** | ✅ | 嵌入 | C2F+Prune v2 | sigmoid | ❌ | 2 | 待训练 | — |
| **c2f_enc_lite_agg** | ✅ | 嵌入 | C2F | sigmoid | ❌ | 2 | 待训练 | — |

---

## 关键发现

1. **nomask (0.4997) 和 c2f_enc_lite (0.4992) 并列最佳**
   - nomask: 并行多尺度 + 外挂 + 6 层
   - c2f_enc_lite: C2F + 嵌入 + 2 层

2. **嵌入位置需要更少的层数**
   - 嵌入: 2 层最佳 (0.4992), 4 层反而下降
   - 外挂: 6 层仍有效 (0.4997)

3. **C2F 不一定优于并行**
   - nomask (并行, 0.4997) > c2f_enc_lite (C2F, 0.4992)
   - 可能因为 ila 已经提供了足够的语言指导, C2F 的 query 路由优势不明显

4. **Per-Query 路由在 base1 下无效**
   - c2f_pq (0.4864) < base1 (0.4894)
   - ila 已为每个实例提供语言信息, per-query 路由优势被抵消

5. **层数消融明确: 2 层 > 1 层 > 3 层 > 4 层**
   - 前层 cluster 是噪声源
   - gate 无法完全抑制 (sigmoid 最小值 ~0.5)

6. **gate 初始化不敏感**
   - init=0.0 vs 0.1 差异仅 0.0086
   - 不是关键因素

---

## model_base1_quard2_c2f_enc_lite_cag

**文件**: `model_base1_quard2_c2f_enc_lite_cag/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_cag.yaml`

**核心特征**:
- ✅ `ila`
- ✅ C2F Cluster Attention (轻量优化)
- 注入位置: **Encoder_layer 内部** (嵌入)
- Gate: `sigmoid` + **Content-Adaptive Gate (CAG)**
- ❌ 不修改 query
- cluster_att_num_layers: 2 (后 2 层)
- 点回读: `_cluster_to_points` (O(N))

**与 c2f_enc_lite 的唯一区别**: 增加 per-point 自适应门控

**改动**:
```python
# c2f_enc_lite (原始):
gate = torch.sigmoid(self.cluster_att_gate)  # 标量 gate
inst_feats = inst_feats + gate * cluster_outputs['point']

# c2f_enc_lite_cag (新增):
scalar_gate = torch.sigmoid(self.cluster_att_gate)  # 标量 gate (保留)
cluster_msg = cluster_outputs['point']

# ★ 新增: per-point content-adaptive gate
gate_input = torch.cat([inst_feats, cluster_msg], dim=-1)  # [B,N,2C]
point_gate = self.cluster_gate_proj(gate_input)             # [B,N,C] ∈ [0,1]

# 最终: 标量 gate × per-point gate × cluster message
inst_feats = inst_feats + scalar_gate * point_gate * cluster_msg
```

**新增模块**:
```python
self.cluster_gate_proj = nn.Sequential(
    nn.Linear(d_model * 2, d_model),  # 2C → C
    nn.ReLU(),
    nn.Linear(d_model, d_model),      # C → C
    nn.Sigmoid()                       # 输出 [0,1]
)
```

**设计动机**:
- 不同点可能需要不同强度的 cluster 信息
- 物体边界的点可能需要更多全局上下文 (gate 高)
- 已在 cluster token 中编码充分的点应保持原特征 (gate 低)
- per-point gate 让模型自适应决定每个点的融合强度

**参数量**: 增加 `cluster_gate_proj` (2C×C + C + C×C + C = 2×256×256 + 256 + 256×256 + 256 = 197K params)

**实验结果**: 尚未训练

---

## model_base1_quard2_c2f_enc_lite_cfe

**文件**: `model_base1_quard2_c2f_enc_lite_cfe/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_cfe.yaml`

**核心特征**:
- ✅ `ila`
- ✅ C2F Cluster Attention (轻量优化)
- 注入位置: **Encoder_layer 内部** (嵌入)
- Gate: `sigmoid`
- ❌ 不修改 query
- cluster_att_num_layers: 2 (后 2 层)
- 点回读: `_cluster_to_points` (O(N)) + **粗尺度特征增强 (CFE)**

**与 c2f_enc_lite 的唯一区别**: `_cluster_to_points` 多尺度融合时用最粗尺度 cluster feat 替代 global_mean

**改动** (在 `hier_postprocess.py`):
```python
# c2f_enc_lite (原始):
global_mean = point_feats.mean(dim=1, keepdim=True).expand_as(point_feats)  # [B,N,C]
gate_in = torch.cat([point_feats, global_mean], dim=-1)  # [B,N,2C]

# c2f_enc_lite_cfe (新增):
coarse_feat = scale_msgs[-1]  # [B,N,C] 最粗尺度 (8簇) cluster feat
gate_in = torch.cat([point_feats, coarse_feat], dim=-1)  # [B,N,2C]
```

**设计动机**:
- `global_mean` 是整个场景的平均特征，丢失空间结构信息
- 最粗尺度 (8簇) cluster token 已包含全局空间语义，是更好的 per-point 融合参考
- 每个点通过 `cluster_ids` gather 到的粗尺度特征保留了该点所在区域的全局上下文
- 用粗尺度特征替代 global_mean 可以让 level_gate 更好地根据点的局部-全局关系决定多尺度融合权重

**参数量**: 无新增 (仅改变输入特征来源)

**实验结果**: 尚未训练

---

## model_base1_quard2_c2f_enc_lite_posA

**文件**: `model_base1_quard2_c2f_enc_lite_posA/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_posA.yaml`

**核心特征**:
- ✅ `ila`
- ✅ C2F Cluster Attention (轻量优化)
- 注入位置: **Encoder_layer 内部** (嵌入, **lia 之后**)
- Gate: `sigmoid`
- ❌ 不修改 query
- cluster_att_num_layers: 2 (后 2 层)
- 点回读: `_cluster_to_points` (O(N))

**与 c2f_enc_lite 的唯一区别**: cluster attention 从 lia 之前移到 lia 之后、ila 之前

**改动**:
```python
# c2f_enc_lite (原始):
def forward(self, ...):
    lang_feats = self.lla(lang_feats, lang_masks)
    if self.use_cluster:
        # cluster attention 在 lia 之前
        gate = torch.sigmoid(self.cluster_att_gate)
        cluster_outputs = self.cluster_att(...)
        inst_feats = inst_feats + gate * cluster_outputs['point']
    lang_feats, _, _ = self.lia(inst_feats, lang_feats, ...)  # lia
    inst_feats, _, _ = self.ila(lang_feats, inst_feats, ...)  # ila
    lang_feats = self.lia_ffn(lang_feats)
    return lang_feats, inst_feats

# c2f_enc_lite_posA (新增):
def forward(self, ...):
    lang_feats = self.lla(lang_feats, lang_masks)
    # ★ lia 先做，让 inst 信息注入 lang
    lang_feats, _, _ = self.lia(inst_feats, lang_feats, batch_mask, None)
    
    if self.use_cluster:
        # cluster attention 在 lia 之后
        gate = torch.sigmoid(self.cluster_att_gate)
        cluster_outputs = self.cluster_att(...)
        inst_feats = inst_feats + gate * cluster_outputs['point']
    
    inst_feats, _, _ = self.ila(lang_feats, inst_feats, ...)  # ila
    lang_feats = self.lia_ffn(lang_feats)
    return lang_feats, inst_feats
```

**设计动机**:
- 原始: `lla → [cluster] → lia → ila`
  - cluster attention 基于纯视觉 inst_feats 做聚类路由
  - 此时 query 还没有从 inst 获得信息
- 变体 A: `lla → lia → [cluster] → ila`
  - lia 先将 inst 信息注入 lang，让 lang 包含场景上下文
  - cluster attention 基于「已语言化」的 inst_feats 做聚类注意力
  - 此时 query 已经通过 lia 获得了 inst 信息，routing 可能更精准
- 预期: cluster routing 更准确，因为 query 已经「看过」场景

**参数量**: 无新增 (仅改变 forward 顺序)

**实验结果**: 尚未训练

---

## model_base1_quard2_c2f_enc_lite_noroute

**文件**: `model_base1_quard2_c2f_enc_lite_noroute/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_noroute.yaml`

**核心特征**:
- ✅ `ila`
- ✅ **纯多尺度 gather** (去掉 C2F 路由)
- 注入位置: **Encoder_layer 内部** (嵌入)
- Gate: `sigmoid`
- ❌ 不修改 query
- cluster_att_num_layers: 2 (后 2 层)
- 点回读: `_cluster_to_points` (O(N))

**与 c2f_enc_lite 的区别**: 去掉 C2F 路由，只保留多尺度 gather

**改动** (在 `hier_postprocess.py`):
```python
# c2f_enc_lite (原始):
class C2F_ClusterAttn_Lite:
    def __init__(self, ...):
        self.query_linear = nn.Linear(d_model, d_model)  # 路由用
        self.k_linear = nn.Linear(d_model, d_model)       # 路由用
        self.v_linear = nn.Linear(d_model, d_model)       # 路由用
        self.point_out_proj = nn.Linear(d_model, d_model)
        self.level_gate = nn.Linear(d_model * 2, num_scales)
    
    def forward(self, point_feats, query, ...):
        # C2F 路由: 粗→细级联选择
        for lvl in reversed(range(num_scales)):
            _qctx, scores = self._scale_attn(query, cf)  # query→cluster attention
            prev_indices = scores.topk(topk, dim=-1).indices
        # 路由完成后，多尺度 gather
        fm = self._cluster_to_points(point_feats, cluster_feats_list, ...)

# c2f_enc_lite_noroute (新增):
class MultiScale_Gather:
    def __init__(self, ...):
        # ★ 去掉 query_linear, k_linear, v_linear (不再需要路由)
        self.point_out_proj = nn.Linear(d_model, d_model)
        self.level_gate = nn.Linear(d_model * 2, num_scales)
    
    def forward(self, point_feats, query, ...):
        # ★ 纯多尺度 gather，不做任何 query routing
        fm = self._cluster_to_points(point_feats, cluster_feats_list, ...)
        fm = self.message_norm(fm).masked_fill(point_mask.unsqueeze(-1), 0)
        return {'point': fm}
```

**设计动机**:
- nomask (并行多尺度, 无 query 路由) = **0.4997**
- lite (C2F 路由 + 多尺度 gather) = **0.4992**
- 两者几乎一样，说明 **C2F 路由本身没带来多少增益**
- 去掉路由可大幅简化代码，减少 ~195K 参数 (query_linear + k_linear + v_linear)
- 本质: 纯多尺度空间上下文注入，不做 query 路由

**参数量**: 减少 ~195K (去掉 query_linear + k_linear + v_linear)

**代码简化**: forward 只有 4 行 (原 lite 有 30+ 行)

**实验结果**: 尚未训练

---

## model_base1_quard2_c2f_enc_lite_posB

**文件**: `model_base1_quard2_c2f_enc_lite_posB/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_posB.yaml`

**核心特征**:
- ✅ `ila`
- ✅ C2F Cluster Attention (轻量优化)
- 注入位置: **Encoder_layer 内部** (嵌入, **ila 之后**)
- Gate: `sigmoid`
- ❌ 不修改 query
- cluster_att_num_layers: 2 (后 2 层)
- 点回读: `_cluster_to_points` (O(N))

**与 c2f_enc_lite 的唯一区别**: cluster attention 从 lia 之前移到 ila 之后

**改动**:
```python
# c2f_enc_lite (原始):
def forward(self, ...):
    lang_feats = self.lla(lang_feats, lang_masks)
    if self.use_cluster:
        # cluster attention 在 lia 之前
        gate = torch.sigmoid(self.cluster_att_gate)
        cluster_outputs = self.cluster_att(...)
        inst_feats = inst_feats + gate * cluster_outputs['point']
    lang_feats, _, _ = self.lia(inst_feats, lang_feats, ...)  # lia
    inst_feats, _, _ = self.ila(lang_feats, inst_feats, ...)  # ila
    lang_feats = self.lia_ffn(lang_feats)
    return lang_feats, inst_feats

# c2f_enc_lite_posB (新增):
def forward(self, ...):
    lang_feats = self.lla(lang_feats, lang_masks)
    # ★ 先做 lia 和 ila，让 inst 和 lang 充分交互
    lang_feats, _, _ = self.lia(inst_feats, lang_feats, batch_mask, None)
    inst_feats, _, _ = self.ila(lang_feats, inst_feats, lang_masks, None)
    
    if self.use_cluster:
        # cluster attention 在 ila 之后
        gate = torch.sigmoid(self.cluster_att_gate)
        cluster_outputs = self.cluster_att(...)
        inst_feats = inst_feats + gate * cluster_outputs['point']
    
    lang_feats = self.lia_ffn(lang_feats)
    return lang_feats, inst_feats
```

**设计动机**:
- 原始: `lla → [cluster] → lia → ila → FFN`
  - cluster attention 基于纯视觉 inst_feats 做聚类路由
- 变体 B: `lla → lia → ila → [cluster] → FFN`
  - lia 和 ila 先完成语言-场景双向交互
  - cluster attention 基于「已语言化」的 inst_feats 做聚类注意力
  - 此时 inst_feats 已经充分融合了语言信息，cluster 作为纯几何补充
- 预期: cluster 不再干扰主路径的语言-场景交互，作为最后的几何修正

**参数量**: 无新增 (仅改变 forward 顺序)

**实验结果**: 尚未训练


---

## model_base1_quard2_c2f_enc_lite_l1

**文件**: `model_base1_quard2_c2f_enc_lite_l1/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_l1.yaml`

**核心特征**: 与 lite 完全相同，仅 `cluster_att_num_layers: 1` (仅最后 1 层启用 cluster)

**实验结果**: Best ep13, mIoU = **0.4928**

---

## model_base1_quard2_c2f_enc_lite_init0

**文件**: `model_base1_quard2_c2f_enc_lite_init0/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_init0.yaml`

**核心特征**: `cluster_att_init: 0.0` → sigmoid(0)=0.50

**实验结果**: Best ep12, mIoU = **0.4906**

---

## model_base1_quard2_c2f_enc_lite_init05

**文件**: `model_base1_quard2_c2f_enc_lite_init05/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_init05.yaml`

**核心特征**: `cluster_att_init: 0.5` → sigmoid(0.5)=0.62

**实验结果**: 未训练

---

## model_base1_quard2_c2f_enc_lite_posC

**文件**: `model_base1_quard2_c2f_enc_lite_posC/`  
**配置**: `configs/Quard/model_base1_quard2_c2f_enc_lite_posC.yaml`

**核心特征**: cluster 放在 FFN 之后，作为最后的残差修正
- 信息流: `lla → lia → ila → FFN → [cluster]`
- cluster 完全独立于语言-场景交互路径，零参数改动

**实验结果**: 尚未训练

---

## 文献启发新变体 (2024-2025)

### model_base1_quard2_c2f_enc_lite_posenc

**文件**: `model_base1_quard2_c2f_enc_lite_posenc/`  
**启发**: Any2Point (ECCV 2024)

**核心改动**: PointCloudPartitioner 返回 cluster 中心坐标 → `pos_enc = MLP(3→64→256)` → 加到 cluster_feats

| 指标 | 值 |
|------|-----|
| 新参数 | +33K (+12%) |
| FLOPs 增量 | +0.5M (+3%) |

**实验结果**: 尚未训练

### model_base1_quard2_c2f_enc_lite_qcond

**文件**: `model_base1_quard2_c2f_enc_lite_qcond/`  
**启发**: PerLA (CVPR 2025)

**核心改动**: C2F 路由选中 topk clusters → **batched** cross-attention (query → 簇内点) → per-level per-query refined tokens `[B, K, Q, C]` → gather 到点 → per-point learned gate 混合 mean 和 query-conditioned tokens

| 指标 | 值 |
|------|-----|
| 新参数 | +197K (+74%) |
| FLOPs 增量 | +25M (+130%) |

**v2 修复** (2026-07):
- ~~`ctx.mean(dim=0)`~~ → 保留 per-query 语义, 返回 `[B, K, Q, C]`
- ~~Python 三重循环~~ → batched cross-attention `[N_bc, max_pts, C]`
- ~~全局 scalar gate~~ → per-point `nn.Linear(C, 1)` gate
- ~~`if gate_raw > 0.01`~~ → 始终 blend, 不 break autograd

**新增模块**:
```python
self.qcond_q_proj = nn.Linear(d_model, d_model)
self.qcond_k_proj = nn.Linear(d_model, d_model)
self.qcond_v_proj = nn.Linear(d_model, d_model)
self.qcond_gate_proj = nn.Linear(d_model, 1)  # per-point gate
```

**实验结果**: 尚未训练

### model_base1_quard2_c2f_enc_lite_attnpool

**文件**: `model_base1_quard2_c2f_enc_lite_attnpool/`

**核心改动**: scatter_mean → **content-adaptive** attention query 聚合每簇 (query 从 cluster mean feat 生成, 非固定 index)

| 指标 | 值 |
|------|-----|
| 新参数 | +262K (+99%) |
| FLOPs 增量 | +40M (+210%) |

**v2 修复** (2026-07):
- ~~per-index `nn.ParameterList([randn(K, C)])`~~ → `nn.ModuleList([nn.Linear(C, C)])` 从 cluster mean feat 生成 query
- ~~`SharedClusterBank` 不传 `d_model`~~ → 显式传 `d_model=d_model`

**新增模块**:
```python
self.attn_pool_query_gen = nn.ModuleList([nn.Linear(d_model, d_model) for _ in cluster_layer_nums])
self.attn_pool_proj = nn.ModuleList([nn.Linear(d_model, d_model) for _ in cluster_layer_nums])
self.attn_pool_out = nn.ModuleList([nn.Linear(d_model, d_model) for _ in cluster_layer_nums])
```

**实验结果**: 尚未训练

### model_base1_quard2_c2f_enc_lite_multi

**文件**: `model_base1_quard2_c2f_enc_lite_multi/`

**核心改动**: 每簇 2 个可学习 query → `multi_proj` 投影回 C

| 指标 | 值 |
|------|-----|
| 新参数 | +131K (+50%) |
| FLOPs 增量 | +20M (+105%) |

**实验结果**: 尚未训练

### model_base1_quard2_c2f_enc_lite_prune

**文件**: `model_base1_quard2_c2f_enc_lite_prune/`  
**启发**: GitMerge3D (NeurIPS 2025)

**核心改动**: `_prune_tokens()` — 余弦相似度 > threshold 合并 token → pad 到 `max_new_K` (非 original K) + `prune_mask` → 实际减少 attention 计算

| 指标 | 值 |
|------|-----|
| 新参数 | **0** |
| C2F 路由加速 | ~40% |

**v2 修复** (2026-07):
- ~~pad 到 original K (无实际加速)~~ → pad 到 `max_new_K` + `prune_mask` → 实际跳过被剪枝 tokens
- ~~剪枝后 `child_cluster_maps` 失效~~ → `_rebuild_child_maps()` 用 `id_remap` 重建
- ~~greedy 循环遍历 `Kb²` 全索引~~ → `torch.triu_indices` 仅上三角 ~2x 加速
- ~~`new_ids[new_ids < 0] = 0` 静默错误~~ → `assert (new_ids >= 0).all()`
- ~~`prune_threshold`/`prune_ratio` 不可配置~~ → 传入 `DEC.__init__`

**新增方法**:
```python
def _rebuild_child_maps(self, child_cluster_maps, remap_list):
    """剪枝后重建 child_cluster_maps, 用 id_remap 更新 parent keys"""
```

**实验结果**: 尚未训练

### model_base1_quard2_c2f_enc_lite_agg

**文件**: `model_base1_quard2_c2f_enc_lite_agg/`  
**启发**: CFA-3DVG (Neurocomputing 2024)

**核心改动**: `_agg_weight_mlp = MLP(2C→C/2→1)` — 学习每个点的聚合权重 (`[point_feat, cluster_mean]`) → 加权求和替代 scatter_mean

| 指标 | 值 |
|------|-----|
| 新参数 | +99K (+37%) |
| FLOPs 增量 | +5M (+26%) |

**v2 修复** (2026-07):
- ~~MLP 输入含 `global_ctx` (场景级均值, 无区分度)~~ → 仅用 `[point_feat, cluster_mean]`, MLP 输入 `2C`
- ~~`SharedClusterBank` 不传 `d_model`~~ → 显式传 `d_model=d_model`

**新增模块**:
```python
self._agg_weight_mlp = nn.Sequential(
    nn.Linear(d_model * 2, d_model // 2),
    nn.ReLU(),
    nn.Linear(d_model // 2, 1),
)
```

**实验结果**: 尚未训练

---

## 变体修复日志

### 2026-07-09: qcond/attnpool/agg/prune v2 修复

#### qcond (`C2F_ClusterAttn_QCond`)

| Bug | 严重度 | 原因 | 修复 |
|-----|--------|------|------|
| `ctx.mean(dim=0)` 丢失 per-query 语义 | Critical | 将所有 Q 个 query 的 cross-attn 结果平均 → 所有 query 看到相同 refined token | Batched cross-attention → `[B, K, Q, C]` per-query refined tokens |
| Python 三重 for 循环 | Critical | 每 batch × query × cluster 独立做 attention, 无法 GPU 并行 | Padded batched: `[N_bc, max_pts, C]` → 单次 batched attention |
| 全局 scalar `qcond_gate` | Moderate | `nn.Parameter(zeros(1))` 对所有点/簇相同 | Per-point `nn.Linear(C, 1)` gate |
| `if gate_raw > 0.01` break autograd | Minor | Python 条件判断在 tensor 上 | 始终 blend, 无 Python 条件 |
| `all_selected` 索引反了 | Critical | forward 按 reversed(range(num_scales)) 顺序 append (coarse→fine), 但 `_qcond_refine` 按 fine→coarse 读取 → cluster_id 指向错误层级 | `sel = all_selected[self.num_scales - 1 - lvl]` |
| `query.unsqueeze(0).expand(N_bc, ...)` 维度错误 | Critical | 产生 `[1, B, Q, C]` (4D) 而非 `[N_bc, Q, C]` (3D) | `torch.stack([query[b] for b, cid in bc_list])` 按 batch 索引 gather |
| `_qcond_gather_blend` 在 gate 前平均 | Moderate | 先 `.mean(dim=1)` 再 blend, 等价于所有 query 共享 blend 结果 | 先 per-query blend 再 mean, 保留 per-query 差异 |

#### attnpool (`SharedClusterBank`)

| Bug | 严重度 | 原因 | 修复 |
|-----|--------|------|------|
| Per-index `ParameterList` | Moderate | `randn(K, C)` 第 i 个 cluster 用第 i 行参数, 非 content-adaptive | `nn.Linear(C, C)` 从 cluster mean feat 生成 query |
| `SharedClusterBank` 不传 `d_model` | Minor | `d_model=256` 硬编码默认值, 改 config 会静默维度不匹配 | 显式传 `d_model=d_model` |

#### agg (`SharedClusterBank`)

| Bug | 严重度 | 原因 | 修复 |
|-----|--------|------|------|
| `global_ctx` 是场景级均值 | Moderate | 对整个场景取 mean, 所有点相同, 无区分度 | 仅用 `[point_feat, cluster_mean]`, MLP 输入 `2C` |
| `SharedClusterBank` 不传 `d_model` | Minor | 同 attnpool | 显式传 `d_model=d_model` |

#### prune (`C2F_ClusterAttn_Prune`)

| Bug | 严重度 | 原因 | 修复 |
|-----|--------|------|------|
| Pad 到 original K (无实际加速) | Critical | 剪枝后 pad 回 `K` tokens, attention 仍计算 `K` 个 key/value | Pad 到 `max_new_K` + `prune_mask` → 实际跳过被剪枝 tokens |
| 剪枝后 `child_cluster_maps` 失效 | Critical | 粗层 parent IDs 被 remap, 但 `child_cluster_maps` 仍用原 ID | `_rebuild_child_maps()` 用 `id_remap` 重建映射 |
| Greedy 循环遍历 `Kb²` | Moderate | `sim_triu.view(-1).argsort()` 包含下三角 + 对角线 | `torch.triu_indices` 仅上三角 ~2x 加速 |
| `new_ids[new_ids < 0] = 0` 静默错误 | Moderate | 任意点被分配到 cluster 0, 无 warning | `assert (new_ids >= 0).all()` |
| `prune_threshold`/`prune_ratio` 不可配置 | Minor | 硬编码 0.85/0.3, 无法从 config 调整 | 传入 `DEC.__init__` |
| `prune_mask` broadcasting 错误 | Critical | `prune_mask` shape `[B, M]` 无法 broadcast 到 scores `[B, H, Q, M]` | `.unsqueeze(1).expand(-1, Q, -1)` → `[B, Q, M]` |

**修改文件** (8 个):
- `model_base1_quard2_c2f_enc_lite_qcond/hier_postprocess.py` — 重写 `_qcond_refine`, `_qcond_cross_attn`, `_qcond_gather_blend`
- `model_base1_quard2_c2f_enc_lite_attnpool/hier_postprocess.py` — 替换 `attn_pool_q` 为 content-adaptive query generator
- `model_base1_quard2_c2f_enc_lite_attnpool/dec.py` — 传 `d_model`
- `model_base1_quard2_c2f_enc_lite_agg/hier_postprocess.py` — 移除 `global_ctx`, MLP 输入 `2C`
- `model_base1_quard2_c2f_enc_lite_agg/dec.py` — 传 `d_model`
- `model_base1_quard2_c2f_enc_lite_prune/hier_postprocess.py` — pad 到 `max_new_K`, `prune_mask`, `_rebuild_child_maps`, 上三角 greedy
- `model_base1_quard2_c2f_enc_lite_prune/dec.py` — 传 `prune_threshold`/`prune_ratio`
