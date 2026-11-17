# Experiment Design - cluster_project

## 1. Motivation
目标原文：面向ScanRefer三维语言定位，回归用户最初的点云特征更新主线，研究不同层级承担不同注意力/信息交互作用的轻量结构机制，目标mIoU>=0.51。完整目标和约束通过scope_goal.json原始字节及哈希引用。
不可变快照2026-10-18 10:09:47上海时间/design，截止11:09:47。active1/target2、candidate_budget1、reserve_budget0、due0。先登记稳定诊断再测试；本轮不将效率核对当新分层机制贡献或训练变体。

## 2. Current Best Results
| ID | 状态 | mIoU | Acc@50 | spmIOU | 轮次 |
|---|---|---|---|---|---|
| M95 | 历史done_earlystop | 0.5020 | 本轮未知 | 本轮未知 | 22/50 |
| M203-FLE | 确认原生步增长 | 早期0.4885315597 | 本轮未知 | 本轮未知 | 20/50 |
M203采集时间10:15:51，步4140至4150/4686，19次原生验证；没有追加VAL或改评估协议。

## 3. Analysis And Direction
细层交换减少参数不等于消除了邻域激活。本轮只量化实际源算子的反向保存storage，不重新执行旧几何/连续性对照、原训练数据预处理或native准备。真实任务收益和非自身内容仍由原冻结训练及原生诊断判断。

## 4. Experiment Plan
| 固定条件 | 有效边/分配槽 | 最大新增浮点storage | 反向保存浮点storage合计 |
|---|---|---|---|
| 单叶N16 | 256/512 | 524288字节 | 557056字节 |
| 单叶N64 | 2048/2048 | 2097152字节 | 2228224字节 |
| 单叶N128 | 4096/4096 | 4194304字节 | 4456448字节 |
| N128，16个8点叶 | 1024/4096 | 4194304字节 | 4456448字节 |
合计12次CPU exchange、8次CPU特征梯度执行。hook/普通/no_grad前向逐位一致，匹配梯度最大差0且有限非零。保存张量按底层storage去重，输入别名单列。最大gather为[N,32,8,32]对应N*K*C*4字节；小叶padding并未减少该分配。

这些是带诊断square-mean读出的CPU保存张量；合计包含该读出的保存值。不是完整训练激活、分配峰值、CUDA显存或新增模型资源PASS。没有实现分块、checkpointing、替代算子或实际显存优化。

## 5. GPU Allocation Plan
| 服务器 | 授权物理卡 | 10:15:51-52状态 | 本轮动作 |
|---|---|---|---|
| server4 | GPU0 | M203原PID1995443及三锁占用 | CPU单线程有限诊断，CUDA隐藏 |
| server3 | GPU1 | 外部PID1453占用 | 只读观察 |
server4GPU1不在授权中；此前用户询问是否有两张空闲，不等于同意扩大使用范围。不使用、驱逐、共享、reset或删除任何卡的锁。

## 6. Implementation Checklist
- 先登记稳定ID，冻结4个条件和字节预测，再实际执行。
- 9个生产源文件和部署配置哈希核对未变。
- 用原build_graph/exchange及无克隆saved_tensors_hooks去重记录；匹配无hook和no_grad控制通过。
- CPU特征梯度不计为原生训练反向；无checkpoint、FPS、native网络或optimizer步。
- 无源码修订、参数搜索、配置/seed/schedule更改、准入、部署或新训练启动。
- 原用户dirty脚本及未跟踪bcca包/配置保留；无git提交/同步。

## 7. Risk Assessment
人工输入规模和叶结构不代表TRAIN真实分布；CPU存储不包含native稀疏backbone/decoder、CUDA临时空间等。参数、FLOPs、延迟与显存必须分别同口径测量；本轮不推断已省显存或达到资源门槛。没有新颖性或训练收益声明。
剩余原生诊断沿原稳定ID等待实际空闲授权卡及新鲜独占租约，目标资产和原1e-6容差不变。四辅助范围保留仅在实际到期后有限核对原解除条件，不因空槽自动重开。以真实external_resource_blocked收尾，不宣称路线耗尽或为了deadline凑变体。finish尚待校验与释放。
