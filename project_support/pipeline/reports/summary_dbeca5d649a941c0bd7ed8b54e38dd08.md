# Research Pipeline Report - cluster_project
快照时间：2026-10-17T16:12:02.691035+00:00；生成报告时快照年龄：2649 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-18 00:12:02
================================================================================
  Target: cluster: 面向 ScanRefer 三维语言定位，回归用户最初的点云特征更新主线，研究不同层级承担不同注意力/信息交互作用的轻量结构机制，目标 mIoU ≥ 0.51。核心路径是分层信息交互真实更新点云/超点 inst_feats，再与 query 特征共同生成 mask；不能把仅修改监督损失、沿用已有层级骨架或无效路由计算称为该主线创新。以多尺度 context-only 和 M95 为既有对照，先诊断层级互补性、局部细节及跨层信息是否真正进入 mask 特征，再依据证据选择一个可推导、可证伪的结构机制。监督与关系绑定仅作辅助诊断/匹配对照，不再取代主线。覆盖机制对照、泛化稳健性和同口径效率验证；已有收益不证明新的分层注意力有效，也不自动重开历史失败或禁止的路线。

## Phase 1: Metric Target
  Target: mIoU ≥ 0.5100
  [✗] Champion: M95-CTF-HCG-CSORT — mIoU=0.5020 (gap to target: +0.0080)
       Epochs: 22/50, State: done_earlystop
  Phase 1: NOT YET — continue exploring ✗

## Baseline
  Baseline: model_base1 — mIoU=0.4894
  Champion vs Baseline: γ = +0.0126

## Phase 2: Story Verification
  (等待 Phase 1 达标后启动)

## Overall
  Phase 1: champion=0.5020, target=0.5100, gap=+0.0080
================================================================================
```

## 1. GPU Overview
- 仅列授权卡；未采集利用率、显存或进程时标为未知，不推断空闲。
| Server | GPU | Util | Memory | Process |
|---|---|---|---|---|
| server-3 | 1 | 未知 | 未知 | 未知 |
| server-4 | 0 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-18 00:11 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1] Best=0.3788 3/50 no_improve=0/10 gpu=0 ? 序列: 0.2966, 0.3788

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=1 withdrawn=6
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M203-FLE | configs/Quard/ctf_hcg_csort_fle_r1/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | running |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 2；准入预算 1。
- 研究储备 4 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 108：complete=12 / rejected=91 / blocked=4 / training=1。
- 否决范围：unclassified=91；实现修订累计 3；收据文件 10（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 本轮 cluster_project 的不可变快照为上海时间2026-10-18 00:12:02，模式design，原截止01:12:02不改；第0-3段保留脚本preflight事实，不假装包含后续变化。当前执行状态为收尾待校验，尚未宣称完成。
- 00:49:42的原生日志确认M203-FLE已到第4/50轮、770/4686步，较00:38第3轮4136步继续增长；前三次VAL mIoU依次0.2966073751、0.3788172901、0.4144061804。只是早期训练，上升不等于已超过历史M95 0.5020或目标0.5100。目标差距仍0.0080。
- 先登记稳定诊断ID fle-self-neighbor-content-separation，再冻结自身项S不变、同叶非自身R逐头范数匹配重排的对照。实际执行8类CPU算子检查全部通过，含精确重构、恒等、置换/并列、零/单点、跨叶隔离、填充、梯度和float32；CUDA从未初始化。科学状态仍为原生诊断未测、收益未知、创新未确立。
- 按事前时间策略冻结首次观察到稳定关闭的last.pth副本，为epoch2，不按best分数选择；原训练checkpoint未改。九源文件、部署配置、标注、数据源与权重指纹固定，八个盲选TRAIN场景32表达、严格CPU权重载入及八个原生CPU整理批均通过。原生runner与清单已准备和静态校验，本轮原生前向/反向/诊断优化步均0。
- 00:49:42两张授权卡均仍占用：server4 GPU0为M203训练且三种锁由其持有，server3 GPU1为外部任务。实际测试忙卡保护在导入Torch/获取锁前拒绝，没有共享、驱逐、reset或删锁。剩余原生同前缀mask回放是真实资源等待，不是假设拒绝。
- 保留首次raw配置SHA失败：CPU测试前即停止，核实仅为既有授权work_dir部署适配后，结构化比较其余配置严格相同再继续；保留本地引用错误，修正显式脚本后忙卡保护通过。Git Bash按实际安装路径执行规范决策留档成功。未计作科学通过或新模型修订。
- 本轮实际产出为一个诊断ID、八类CPU检查、一个冻结早期权重、八个场景32表达的CPU准备、占用保护、审查/设计/决策/记忆和完整报告；新增模型/准入/启动均0。收据用量窗口仅从begin 00:12:02至收据生成，排除更早读取、晚到记录和最终答复；总量在收据生成前未知。缓存属于输入、推理属于输出，不重复相加，不当作账单。

## 5. Decisions Made
- 保持M203-FLE原训练和原终态评估计划，不改点云主线、goal/准入/容差/损失/调度，不新增凑数变体；HDS不重启或做第三修订。
- 将本轮唯一新诊断保留为exclusive_gpu_slot资源等待，required_server=server-4；一小时后重查或资源/证据变化提前唤醒不是承诺下次调度时间。先核实真实空闲、指定主机/UUID、当轮租约、三种生命周期锁及冻结指纹，才执行normal/repeat/identity/同范数非自身内容控制与原生mask回放。server3 GPU1仍有授权，但切换前须验证该目标资产和运行时。
- 固定query读出指相同候选索引和捕获的入射query前缀，并不冻结最终query特征；最终query仍按原生后缀计算。未来8场景早期TRAIN差异只是机制局部证据，不能外推泛化或创新。
- 以真实external_resource_blocked收尾，不声称独立路线耗尽，不等待截止或放宽门槛。finish成功并核实释放后才称本轮执行完成；否则保留证据并abort核实释放。四个既有授权/范围挂起候选不因计时或卡容量而重开。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
