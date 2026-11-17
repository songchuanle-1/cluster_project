# Research Pipeline Report - cluster_project
快照时间：2026-10-18T22:09:38.510560+00:00；生成报告时快照年龄：3501 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-19 06:09:37
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
================================================== 2026-10-19 06:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  无训练进程

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| 无 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 快照内无运行任务 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 0（运行 0 / 认领 0 / 等待 0）；目标 2；准入预算 2。
- 研究储备 4 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 120：complete=25 / rejected=91 / blocked=4。
- 否决范围：unclassified=91；实现修订累计 4；收据文件 10（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 快照上海时间2026-10-19 06:09:38，design；历史最佳0.5020、目标0.5100、差0.0080。预检无在训/等待；无新mIoU测量。
- 本轮建立同一稳定候选CPA：仅粗层语义到点特征的新信息边，细/中层、原损失和所有数值配置不变。一次预注册key来源连接修订；8文件独立包，无新增投影/门控/可学习参数，不重开FLE/HDS/路由或CSORT。
- 同前向原生mask/损失重建和身份对照通过1e-6；所有条件的实际监督mask/indices/num_boxes一致。八固定TRAIN场景中，正确key相对均值和错配的方向不稳定，诊断及语义准入未通过，不能称训练收益或整个主线失败。
- 完成自身粗簇移除/远处信息加入的归因诊断，结果不能唯一解释风险。它仅为非部署反事实，不生成被禁残差变体。
- 独立候选完整原生反向、0/4worker，以及仅原backbone的新Network冷初始化均通过；实际attention和粗层FFN/norm有有限非零loss梯度。冷初始化构建AdamW/PolyLR但均0步骤/optimizer状态0，未复用M95诊断头。
- 同输入、原FVCore计数器、bs1/warmup20/repeat100：CPA9.769168428G vs M959.762532428G，增加0.006636G；延迟35.9614 vs35.3617ms(+1.696%)；推理峰值显存+1.288%，匹配原生反向峰值+0.329%至+0.706%。无fulloptimizer峰值及原无clusterbaseline资源数据，记未知；不改变10G或15%规则。
- 新算子的排列等变/键值联合排列不变、padding输出/梯度/扩展、相同key均值退化及有限差分通过；不是重复旧整网padding/内核审计。原CPU夹具两次接口失败和候选装载注册冲突均保留；后者以独立进程直接加载修复，未覆盖注册表。
- 实际20次原生前向/20反向，242次资源predict、59次source-interface、69次suffix/criterion、39次suffix梯度探针；只有1候选/1结构修订，8个物理TRAIN场景；计数不是独立模型或训练实验数。训练、准入、验证选型、optimizer/scheduler更新均0。
- 错误点定位读数被guard400在剩余366.735992秒时拒绝，未启动CUDA；不是资源阻塞或科学失败。deferred_error_protocol.json已保存，仍在同一ID的validation阶段，先执行首2场景，再余6；不重做已通过的资源/反向或已完成旧审计。
- 资源授权仅server4物理GPU0与server3物理GPU1；06:13后者为外部占用18354MiB/100%，之后未知。最终GPU0实际占用和三个锁释放可用性见final_environment.json。未使用server4GPU1或触碰其他项目/调度。
- 本轮科学状态：有可执行待续候选，核心语义诊断未证实，不准入训练。执行状态等待实际finish；不宣称提前耗尽路线、资源阻塞或截止已过，不修改deadline或校验器。
- 用量仅以最终收据begin至receipt的可见响应窗口为准，数值在收据前未知；不含更早阅读、迟到记录及最终回复，不是账单；缓存是输入子集、推理是输出子集，不能重复相加。

## 5. Decisions Made
- 保留粗层语义直达点特征候选及一次key连接修订，现有独立实现、原生反向/冷初始化和资源证据有效；正确语义匹配的任务作用未稳定证实，诊断与准入仍不通过。
- 下一步仅续做已冻结错误点定位读数；八场景采样、原监督、seed1999/epochs50/max_iters70、预算和全部禁令不变。无优化器更新、无训练入队、无旧路线重开。
- 按真实deadline与规范finish结果收尾；若校验不通过，保留实际错误并abort释放。未执行读数不记失败或PASS，不以资源测试通过冒充科学成功。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
