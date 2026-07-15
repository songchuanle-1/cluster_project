# PosA-L1 独立变体设计（2026-07-15）

## 共同实验约束

- 编码顺序固定为 `LLA -> LIA -> Cluster -> ILA -> FFN`。
- Cluster 模块只作用于第 6 个 encoder layer（`cluster_att_num_layers: 1`）。
- 聚类尺度固定为 `[256, 64, 8]`，top-k 固定为 `[32, 16, 8]`。
- 除目标变量外，数据、优化器、损失函数和随机种子均与 PosA-L1 一致。
- 五个模型均有独立 Python 包和完整 YAML，不使用跨模型 import 或 `_base_` 配置继承。

## 五个版本

| 版本 | 唯一主要变化 | 目的 |
|---|---|---|
| PosA-L1 | 保留 legacy C2F，`sigmoid(0.1)` 门控，注入 cluster context | 对照组，复现已有结果 |
| PosA-L1-NoRoute | 删除 query Q/K/V、粗到细 top-k 路由，只保留 cluster-to-point 多尺度 gather | 验证 legacy 路由是否只是无效 FLOPs |
| PosA-L1-LayerScale | 将正值 sigmoid 门控改为可正可负的 LayerScale，初值 `1e-3` | 避免训练开始时以约 0.525 的强度扰动已训练表征 |
| PosA-L1-Detail | 注入 `LayerNorm(point - cluster_context)`，而非直接注入 context | 保留局部细节，减少聚类均值带来的过平滑 |
| PosA-L1-TrueRoute | 将 query context 按最终 fine-level top-k 路由聚合回被选中的细粒度 cluster，再回读到点 | 让路由真实影响输出，并检验语言条件路由的价值 |

## 建议比较顺序

优先并行运行 NoRoute 与 LayerScale。NoRoute 直接回答 FLOPs 是否值得，LayerScale 检验当前门控初始化是否过强。随后运行 Detail；TrueRoute 的行为改动最大，放在最后与 NoRoute、PosA-L1 三方比较。

除精度指标外，需要同时记录单步 FLOPs、峰值显存和 iteration time。若 NoRoute 精度不降且计算量明显下降，应将它作为后续轻量基线；只有 TrueRoute 显著优于 NoRoute，才能证明 coarse-to-fine query routing 本身有效。
