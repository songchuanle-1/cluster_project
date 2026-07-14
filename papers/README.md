# 相关文献索引

## 与 4 个优化方向的映射

### 方向 1: lite_posenc（位置编码）

| 论文 | 会议 | 关键思想 |
|------|------|---------|
| **Any2Point** (2404.07989) | ECCV 2024 | 3D→1D/2D 位置编码虚拟投影，FPS 选中心点 + k-NN 聚合 |
| **PPT** (2408.11567) | arXiv 2024 | 多尺度位置编码 + 全局中心点锚定，仅训练 1.05% 参数 |
| **FPE Transformer** (2302.08903) | IEEE TPAMI 2024 | 完整点位编码 + 形状感知下采样 |
| **PointCT** (2310.14256) | WACV 2024 | 中心点注意力 + 邻域双向一致性 |

**你的 posenc 贡献**: 将 cluster 中心坐标 (3D) 编码为可学习位置编码，加到 cluster token 上

---

### 方向 2: lite_qcond（Query-Conditioned Aggregation）

| 论文 | 会议 | 关键思想 |
|------|------|---------|
| **PerLA** (2411.19774) | CVPR 2025 | 语言查询并行关注局部高分辨率 + 全局上下文 |
| **CFA-3DVG** (2406.03157) | Neurocomputing 2024 | 上下文感知特征聚合，补偿下采样信息损失 |
| **LIBA** (2412.14502) | AAAI 2025 | 语言感知的跨尺度目标调节 (LCOM) |
| **DFW-3DVG** (2411.05241) | ICVRV 2025 | 动态特征加权，LLM 解析查询语义分配权重 |

**你的 qcond 贡献**: C2F 路由选 topk clusters，用 query 做 cross-attention 重新聚合簇内点

---

### 方向 3: lite_attnpool（Attention Pooling）

| 论文 | 会议 | 关键思想 |
|------|------|---------|
| **GitMerge3D** (2511.05449) | NeurIPS 2025 | 90-95% token 冗余，图引导 token 合并，自适应能量评分 |
| **CPM** (IEEE 2024) | IEEE 2024 | 特征域聚类 + cluster 内 token 合并 |
| **3DLST** | IJAG 2026 | 可学习超 token 聚类，动态超 token 优化，cross-attention 上采样 |

**你的 attnpool 贡献**: scatter_mean → 可学习 attention query attend 簇内点

---

### 方向 4: lite_multi（多 Token）

| 论文 | 会议 | 关键思想 |
|------|------|---------|
| **RG-SAN** (2410.13472) | NeurIPS 2024 Oral | 规则引导空间感知，依赖树规则引导空间推理 |
| **M3DBench** (2312.10763) | ECCV 2024 | 统一 3D 多模态指令，区域级 + 场景级任务 |
| **DDPA-3DVG** | IJCAI 2025 | 双解耦 + 渐进对齐，语言/视觉多粒度解耦 |

**你的 multi 贡献**: 每簇 2 个可学习 query 生成 2 个 token，投影回 1 个

---

## 论文清单

| # | 文件 | 会议 | 大小 |
|---|------|------|------|
| 1 | `gitmerge3d_token_merging_neurips2025.pdf` | NeurIPS 2025 | 17M |
| 2 | `PerLA_cvpr2025.pdf` | CVPR 2025 | 18M |
| 3 | `RG_SAN_neurips2024_oral.pdf` | NeurIPS 2024 Oral | 3.2M |
| 4 | `M3DBench_eccv2024.pdf` | ECCV 2024 | 5.3M |
| 5 | `Any2Point_position_encoding_eccv2024.pdf` | ECCV 2024 | 2.2M |
| 6 | `LIBA_AAAI2025.pdf` | AAAI 2025 | 2.1M |
| 7 | `PPT_position_prompt_tuning_2024.pdf` | arXiv 2024 | 2.1M |
| 8 | `CPM_cluster_merging_2024.pdf` | IEEE 2024 | 8.3M |
| 9 | `PointCT_wacv2024.pdf` | WACV 2024 | 2.2M |
| 10 | `FPE_transformer_tpami2024.pdf` | IEEE TPAMI 2024 | 0.5M |
| 11 | `CFA_3DVG_context_aggregation_2024.pdf` | Neurocomputing 2024 | 0.5M |
| 12 | `DFW_3DVG_dynamic_weighting_2024.pdf` | ICVRV 2025 | 0.2M |

---

## 最值得精读的 4 篇

1. **GitMerge3D** — 直接回答"点云 transformer 需要多少 token"，与你的 attnpool/multi 方向直接相关
2. **PerLA** — 语言查询条件化的特征聚合，与实践版 qcond 最接近
3. **Any2Point** — 位置编码设计的最佳实践，与 posenc 直接相关
4. **RG-SAN** — NeurIPS Oral, 3D RES 任务的一流方法，了解领域前沿
