# 超点 → 体素化 → Backbone 处理流程

## 概述

本文档描述 ScanNet 点云数据从**超点分割**到**体素化**再到**Backbone 特征提取**的完整处理链路。整个流程的目标是：将原始 3D 点云转化为具有几何和语义信息的**超点级特征表示**，供下游解码器（DEC）使用。

**数据流总览：**

```
原始点云 (N 个点)
    │
    ▼  mesh 分割 (Felzenszwalb)
超点 (S 个超点, 每个超点包含若干点)
    │
    ▼  坐标缩放 + 网格对齐
体素 (V 个非空体素)
    │
    ▼  稀疏卷积 U-Net
体素特征 (V 个, 32 维)
    │
    ▼  体素→点 还原 + 超点均值池化
超点特征 (S 个, 32 维)
```

---

## 1. 超点（Superpoint）

### 1.1 超点生成

超点在数据预处理阶段通过 **Felzenszwalb 图分割算法** 对 mesh 进行分割生成。

**核心思路：** 将 mesh 面片视为图的节点，根据面片之间的法线夹角和凸凹性计算边权重，自适应合并相似面片。

```
Mesh (vertices, faces)
    │
    ▼  计算面片法线 & 顶点法线
    │
    ▼  计算边权重: w = (1 - n₁·n₂)²  (凸边惩罚更小)
    │
    ▼  Felzenszwalb 自适应合并
    │   阈值: τ(C) = last_weight + k / |C|
    │
    ▼  合并小片段 (< 20 个顶点)
    │
    ▼  每个顶点获得超点 ID
superpoint: (N,) 整数, 范围 [0, S-1]
```

**关键参数：**
- `kThresh = 0.01`：合并敏感度
- `segMinVerts = 20`：最小片段顶点数

**源文件：** `data/scannetv2/prepare_data_refer.py`

### 1.2 Dataset 中的超点处理

加载 `.pth` 文件后，在 `transform_train` / `transform_test` 中对超点进行重编号：

```
原始 superpoint: (N,) 超点 ID (可能不连续)
    │
    ▼  随机采样 (最多 max_npoint 个点)
    │
    ▼  np.unique(超点[采样索引], return_inverse=True)
    │
    ├─ unique:  存活超点的原始 ID (用于索引 CLIP 特征)
    └─ superpoint: 重新编号为连续 [0, S'-1]
```

**为什么需要重编号？** 采样后某些超点可能没有剩余点，原始 ID 不连续。重编号确保后续 `scatter_mean` 等操作正确工作。

**超点标签生成：** 通过多数投票为每个超点分配实例标签：

```python
# 对每个实例, 计算每个超点中属于该实例的点比例
gt_spmask = scatter_mean(ref_lbl.float(), superpoint, dim=-1)
gt_spmask = gt_spmask > 0.5  # 超过半数即归属该实例
```

**源文件：** `Cluster/framework/dataset/scannetv2.py` 第 201-222 行, 第 335-347 行

### 1.3 Collate 中的批处理

多个 scene 组成 batch 时，需要让不同 scene 的超点 ID 互不重叠：

```
Scene 0: superpoint = [0, 1, 2, ..., S₀-1]
Scene 1: superpoint = [0, 1, 2, ..., S₁-1]  + S₀  (偏移)
Scene 2: superpoint = [0, 1, 2, ..., S₂-1]  + S₀+S₁  (偏移)
    ...

拼接后: superpoints = (B*N,) 全局唯一 ID [0, ΣS-1]
```

**源文件：** `Cluster/framework/dataset/scannetv2.py` 第 467-468 行

---

## 2. 体素化（Voxelization）

### 2.1 坐标准备

点云坐标经过缩放转换为整数体素坐标：

```
原始坐标 xyz_middle: (N, 3) float, 单位: 米
    │
    ▼  × scale (50)
缩放坐标 xyz: (N, 3) float, 单位: 2cm
    │
    ▼  - min(0)  (平移到非负)
    │
    ▼  torch.from_numpy(xyz).long()
整数坐标 coord: (N, 3) long
    │
    ▼  添加 batch index 列
体素坐标 coords: (N, 4) long  [batch_idx, x, y, z]
```

**关键参数：**
- `scale = 50`：1 个体素单位 = 0.02 米 = 2 厘米
- `max_npoint = 2,500,000`：每个 scene 最大点数
- `spatial_shape = [128, 512]`：体素网格最小/最大范围

### 2.2 体素化索引

调用 `pointgroup_ops.voxelization_idx` 建立点与体素的双向映射：

```
输入: coords (B*N, 4) [batch_idx, x, y, z]  +  mode=4

    ┌─────────────────────────────────────────┐
    │  遍历每个点, 查哈希表:                    │
    │  - 新体素 → 分配 voxel_idx              │
    │  - 已有体素 → 复用 voxel_idx             │
    └─────────────────────────────────────────┘

输出:
    voxel_coords: (V, 4)  非空体素坐标 [batch_idx, vx, vy, vz]
    p2v_map:      (B*N,)  点 → 体素  (每个点属于哪个体素)
    v2p_map:      (V, maxActive+1)  体素 → 点列表
                    [0] = 该体素内的点数
                    [1..count] = 点的索引
```

### 2.3 特征体素化

将逐点特征聚合为体素特征（取均值）：

```
feats: (B*N, 6)  [R, G, B, x_orig, y_orig, z_orig]
    │
    ▼  pointgroup_ops.voxelization(feats, v2p_map)
    │  对每个体素内的所有点特征取均值
    │
voxel_feats: (V, 6)
```

**数学表达：**

```
V_v = (1 / |P_v|) × Σ_{i ∈ P_v} F_i
```

其中 `P_v` 是体素 `v` 包含的点集。

### 2.4 构建稀疏张量

```python
input = SparseConvTensor(voxel_feats, voxel_coords, spatial_shape, batch_size)
```

稀疏张量只存储非空体素，大幅减少计算量。

**源文件：** `Cluster/framework/dataset/scannetv2.py` 第 510-511 行, `Cluster/framework/model/.../network.py` 第 117-118 行

---

## 3. Backbone（稀疏卷积）

### 3.1 整体结构

Backbone 由三部分组成：**输入卷积** + **U-Net** + **输出层**，之后进行体素到点的还原和超点池化。

```
SparseConvTensor (V, 6)
    │
    ▼  input_conv: SubMConv3d(6→32, k=3, p=1)
    │
SparseConvTensor (V, 32)
    │
    ▼  UBlock: 5 层编码器-解码器 + skip connection
    │
SparseConvTensor (V, 32)
    │
    ▼  output_layer: BN(32) + ReLU
    │
SparseConvTensor (V, 32)
    │
    ▼  体素→点 映射 (p2v_map)
    │
Dense Tensor (B*N, 32)
    │
    ▼  超点均值池化 (scatter_mean)
    │
Dense Tensor (B*M, 32)  ← 超点特征 sp_feats
```

**源文件：** `Cluster/framework/model/.../network.py` 第 211-223 行

### 3.2 UBlock 编码器-解码器

UBlock 是递归结构，共 5 层，通道数逐步增加：`32 → 64 → 96 → 128 → 160`。

```
Level 1 (32 ch) ──── blocks ──── identity ─────────────────── cat ── blocks_tail ──→ (32 ch)
                        │                                          ▲
                        ▼                                          │
                    SparseConv3d                               SparseInverseConv3d
                    (32→64, s=2)                               (64→32, k=2)
                        │                                          ▲
Level 2 (64 ch) ──── blocks ──── identity ──────────── cat ── blocks_tail ──→
                        │                                    ▲
                        ▼                                    │
                    SparseConv3d                        SparseInverseConv3d
                    (64→96, s=2)                        (96→64, k=2)
                        │                                    ▲
Level 3 (96 ch) ──── blocks ──── identity ──── cat ── blocks_tail ──→
                        │                            ▲
                        ▼                            │
                    SparseConv3d                SparseInverseConv3d
                    (96→128, s=2)               (128→96, k=2)
                        │                            ▲
Level 4 (128 ch) ─── blocks ── identity ─ cat ─ blocks_tail ──→
                        │                      ▲
                        ▼                      │
                    SparseConv3d          SparseInverseConv3d
                    (128→160, s=2)        (160→128, k=2)
                        │                      ▲
Level 5 (160 ch) ─── blocks ──────────────────┘
                    (Bottleneck)
```

**每层结构：**

| 组件 | 操作 | 说明 |
|------|------|------|
| `blocks` | 2× ResidualBlock | 编码器特征提取 |
| `conv` | SparseConv3d (stride=2) | 下采样, 分辨率减半 |
| `u` | 递归 UBlock | 处理更深层级 |
| `deconv` | SparseInverseConv3d | 上采样, 恢复分辨率 |
| skip connection | `cat(identity, upsampled)` | 编码器-解码器拼接 |
| `blocks_tail` | 2× ResidualBlock | 解码器特征融合 |

**源文件：** `Cluster/framework/model/.../backbone.py` 第 58-171 行

### 3.3 ResidualBlock

每个 ResidualBlock 包含两个子流分支和一个残差连接：

```
输入 (V, C_in)
    │
    ├── conv_branch: BN → ReLU → SubMConv3d(3×3) → BN → ReLU → SubMConv3d(3×3)
    │
    └── i_branch: Identity (通道相同) 或 SubMConv3d(1×1) (通道不同)
    │
    ▼
输出 = conv_branch(输入) + i_branch(输入)
```

**SubMConv3d（子流形稀疏卷积）：** 只在已激活的体素位置上计算卷积，不改变稀疏结构。相比标准稀疏卷积，不会"膨胀"激活区域。

**SparseConv3d vs SparseInverseConv3d：**
- `SparseConv3d(stride=2)`：标准稀疏卷积 + 下采样，体素网格缩小 2 倍
- `SparseInverseConv3d`：转置稀疏卷积，上采样恢复到原始分辨率（需与对应下采样共享 `indice_key`）

**源文件：** `Cluster/framework/model/.../backbone.py` 第 11-55 行

### 3.4 体素→点映射

Backbone 输出是体素级特征，需要还原回点级：

```
x.features: (V, 32)    体素特征
    │
    ▼  x.features[p2v_map.long()]
    │  p2v_map[i] = 点 i 所属的体素索引
    │
point_feats: (B*N, 32) 每个点获得其所在体素的特征
```

### 3.5 超点均值池化

将点级特征聚合为超点级：

```
point_feats: (B*N, 32)
    │
    ▼  scatter_mean(point_feats, superpoints, dim=0)
    │  对同一超点内的所有点特征取均值
    │
sp_feats: (B*M, 32)    每个超点一个 32 维特征向量
```

**数学表达：**

```
f_s = (1 / |P_s|) × Σ_{i ∈ superpoint_s} f_i
```

同时，超点坐标也通过均值池化获得：

```python
sp_coords_float = scatter_mean(coords_float, superpoints, dim=0)  # (B*M, 3)
```

---

## 数据流总结

| 阶段 | 张量 | 形状 | 类型 | 说明 |
|------|------|------|------|------|
| 预处理 | superpoint | (N,) | int | Felzenszwalb 分割 ID |
| Dataset | superpoint (重编号) | (N',) | int | 连续 [0, S'-1] |
| Collate | superpoints | (B\*N,) | long | 全局唯一 [0, ΣS-1] |
| Collate | feats | (B\*N, 6) | float | [R, G, B, x, y, z] |
| Collate | coords | (B\*N, 4) | long | [batch, x_vox, y_vox, z_vox] |
| 体素化 | voxel_coords | (V, 4) | long | 非空体素坐标 |
| 体素化 | p2v_map | (B\*N,) | int | 点→体素 |
| 体素化 | v2p_map | (V, max+1) | int | 体素→点列表 |
| 体素化 | voxel_feats | (V, 6) | float | 体素内点特征均值 |
| input_conv | — | (V, 32) | float | SubMConv3d 6→32 |
| UBlock 下采样 | Level 1→2 | (V/8, 64) | float | SparseConv3d stride=2 |
| UBlock 下采样 | Level 2→3 | (V/64, 96) | float | SparseConv3d stride=2 |
| UBlock 瓶颈 | Level 5 | (V/2⁴, 160) | float | 最深层 |
| UBlock 上采样 | Level 5→4 | (V/8, 128) | float | SparseInverseConv3d |
| UBlock 上采样 | Level 4→1 | (V, 64→32) | float | 恢复原始分辨率 |
| output_layer | BN+ReLU | (V, 32) | float | 最终归一化 |
| 体素→点 | p2v_map 索引 | (B\*N, 32) | float | 点级特征 |
| 超点池化 | scatter_mean | (B\*M, 32) | float | 超点级特征 |

---

## 关键文件索引

| 文件 | 说明 |
|------|------|
| `data/scannetv2/prepare_data_refer.py` | 超点生成、PLY 预处理 |
| `Cluster/framework/dataset/scannetv2.py` | Dataset 加载、transform、collate、体素化调用 |
| `Cluster/framework/model/.../network.py` | Backbone 主网络、extract_feat、expand_and_fps |
| `Cluster/framework/model/.../backbone.py` | ResidualBlock、UBlock 定义 |
| `pointgroup_ops` (C++/CUDA) | 体素化索引、特征体素化 |
