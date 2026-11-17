# M205-MDC 中层方向卷积实验

本轮使用已获批的 experiment_first 流程；精度收益留待原生训练验证。

假设：M95 的 fine/middle/coarse token 分别经过独立 FFN，中层 token 缺少显式几何邻接交换。仅把 64 个 middle token 的 FFN 替换为固定三维六方向卷积，可在原 HCG 回读前形成空间上下文，有机会改善指代表达定位。该假设尚未经过训练验证。

计算图：沿原 point→fine→middle 成员映射均值聚合中心。每个中层接收 token 按 donor−receiver 的主绝对坐标轴及符号分为 ±x/±y/±z 六扇区，选择各区最近有效中心。主轴并列按 x/y/z；等距按原 token ID。排除自身、零位移、空簇与 padding；缺方向贡献为零。自项与六方向分别乘通道深度卷积权重，求和加 bias，再 C×C pointwise 与 GELU。中层不加新 residual，原 middle FFN 删除；fine/coarse FFN、原 HCG、最后一层 inst_feats 更新、CSORT 辅助项保留。方向边可以跨 coarse parent；模型对 xyz 旋转敏感。

对照：未修改 M95；相同 ScanRefer 数据、seed=1999、50 epochs、max_iters=70、优化器和既有数值配置。独立九文件模型/YAML，未向 champion 导入。不是 nhead/topk/weight/dropout 等超参数搜索；没有新增语言路由、大 QKV、点级 N² 图、门控或额外注入层。

准入计划：同一 YAML 原生初始化与预训练骨干，真实 TRAIN dataloader，原生 train 函数至少两次 finite loss/backward/optimizer step，并观测 MDC 进入实际路径及梯度。资源使用同原生样本、batch1、warmup20/repeat100、原 fvcore 默认计数和未支持算子清单；总计数须不超过 10G，记录 median/P90 与显存，不把未支持算子当作零成本证明。仅通过当前四项工程准入才保存凭据、入队并尝试启动固定 Phase1 训练。

历史边界：M116-CGA 为 feature-cosine top8、多尺度两层大 Q/K/V/O GAT，旧结果 .4930；本结构使用固定几何中层 depthwise 卷积而非该实现。保留所有旧失败，未恢复 RSTR/PCE/FLE/HDS/CPA。新方案训练效益、泛化与对小目标的影响均未知。

当前实现已本地保存版本，尚未完成原生测试。源版本以 version_native.json 的 commit 和九文件哈希为准；后续结果独立留档。
