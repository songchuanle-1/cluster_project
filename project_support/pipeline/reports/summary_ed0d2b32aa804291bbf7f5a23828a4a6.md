# Research Pipeline Report - cluster_project
快照时间：2026-10-18T14:09:37.742682+00:00；生成报告时快照年龄：3566 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-18 22:09:37
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
================================================== 2026-10-18 22:09 : cluster_project ==================================================

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
- 快照2026-10-18 22:09:37上海/design；begin预检仅一次，原owner核实。只用server4GPU0，未使用GPU1/server3，未改变目标/调度/训练协议。
- 两次实际原生M95调用补全所选算法/索引：坐标对齐输出0，fwd/bwd连接相同。最初mask存储误读已保留；反解argsort并用8邻居位图语义控制证明mask实际一致。有限数值审计完成，不为唯一内核原因无限延期主线。
- 新增主线条件通道秩诊断：2场景8表达24固定读出；原生前缀完整重建0，24自身粗簇VJP活跃/其他粗簇精确0；48CPUJacobian测均值上下文秩2、自身粗簇255。梯度平方投影中位数0.0292466，固定同秩DCT0.00347453；不是训练loss改善或整网表达力上限。
- 关键负面结果：原生null对照在第三个固定读出超过既定1e-6门槛后停止，累计10接口前向；基线重建0。具体失败幅度因原脚本未先保存部分记录而未知，不能写0。保留原始源码、manifest和失败；一次固定失败读出复查已预注册，但安全窗口guard失败，实际未启动/GPU调用0。
- 本轮实际3次原生整网前后向、24原生接口VJP、11接口前向含失败尝试、48CPUJacobian；新训练/VAL/model/准入/优化步骤0。final_environment核实冻结资产未变、GPU0无上下文、三锁释放。
- 用量仅begin至收据可见窗口，具体值待helper收据；缺失未知，缓存属于输入/推理属于输出子集，不重复相加、不当账单。实际产出为本轮上述诊断和失败证据，不是token量。

## 5. Decisions Made
- 没有新mIoU提升：目标0.5100、历史最佳0.5020、差0.0080；缓存FLE早停23/50最佳0.48853156不重启。主线研究未改为单纯显存或数值修复。
- 新候选保持validation/证据不确定，未完成科学准入，不新建训练变体。条件秩测量不证明整网瓶颈、效果或新颖性；原生null失败不能靠放宽阈值记PASS。四个辅助保留不自动重开。
- 当前实际剩余33秒，真实末180秒按tick_deadline_near保留同一失败读出的具体下一步；本轮执行状态仍待finish校验，失败则保留证据并abort核实释放。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
