# Research Pipeline Report - cluster_project
快照时间：2026-10-18T12:12:32.466710+00:00；生成报告时快照年龄：3546 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-18 20:12:31
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
================================================== 2026-10-18 20:12 : cluster_project ==================================================

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
- 研究储备 5 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 117：complete=21 / rejected=91 / blocked=4 / validation=1。
- 否决范围：unclassified=91；实现修订累计 3；收据文件 10（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 快照为2026-10-18 20:12:32上海时间/design；按唯一到期稳定候选续做，无重复preflight。全部诊断保持原生权重、参数requires_grad、seed1999及batch2/clip0.1；未操作其他项目、调度或GPU1。
- 两模型各一对原生跟踪定位最早原始分叉为unet.conv.2的输出与稀疏坐标行序。按坐标对齐后，M95固定输入跨进程特征仍有3.3378601e-6差异，FLE该层对齐为0；未将行重排直接认定为算术错误。
- FLE两次额外原生捕获定位第一个训练态BN数值分叉9.5367432e-7；一次原生cotangent及A/A/B只改行排列对照，A/B分别重建原生结果0，A重复输出/全部VJP0，零cotangent全部0，B复现该差异。仅证明该固定批次局部行序数值原因，不证明整网训练差距或收益。
- M95两次只读所选算法观察均为相同Simt描述、输出哈希相同，TF32关闭；并未解释此前那对进程的算术差异，具体后端原因保留未知。不改缓存、强制算法、换种子或重试至匹配。
- 本轮实际11次原生整网前向/11次原生整网反向，另15次固定输入算子前向、15次普通VJP、7次零VJP；新训练、VAL、新模型、准入及优化步骤均0。严格阈值和全部负面证据保留，单步诊断显存不是全训练峰值。
- 用量窗口仅为begin至收据，数值待helper收据，缺失为未知；缓存属于输入子集、推理属于输出子集，不重复相加，也不是供应商账单。实际产出为本轮上述测试和留档，而非token数量。
- 最终资产核验见final_environment.json：生产源码/配置/权重哈希未变，GPU0无上下文，三锁释放。Git Bash路径假设故障已按实际安装路径修正，未重跑实验。当前实际剩余53秒，真实进入末180秒，按tick_deadline_near保留具体待续动作。

## 5. Decisions Made
- 科学状态：没有新的mIoU提升或训练准入证据；目标0.5100、历史最佳0.5020、差0.0080；缓存M203-FLE早停23/50最佳0.4885315597不重启。重复性诊断不替代用户的分层点云特征更新主线。
- 同一native-train-prefix-repeatability-audit保持validation，下一项为实际原生首层选择描述/indice表与坐标对齐算术差异的绑定测试；M95具体机制未知，不伪造穷尽或外部资源阻塞。四个未到期人工/范围保留不重开。
- 执行状态在finish前为待校验，不提前称完成。按真实剩余时间保留具体待续动作；只有实际进入末180秒才登记tick_deadline_near，否则不能伪造截止或冷却。finish失败则保留证据并abort核实释放，不在释放后改报告。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
