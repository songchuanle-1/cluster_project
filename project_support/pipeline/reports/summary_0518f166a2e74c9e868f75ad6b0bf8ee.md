# Research Pipeline Report - cluster_project
快照时间：2026-10-18T00:11:35.364634+00:00；生成报告时快照年龄：1588 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-18 08:11:34
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
================================================== 2026-10-18 08:11 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fle_r1] Best=0.4885 17/50 no_improve=3/10 gpu=0 ? 序列: 0.4771, 0.4885, 0.4847, 0.4820, 0.4862

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
- 研究储备 6 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 111：complete=13 / rejected=91 / blocked=6 / training=1。
- 否决范围：unclassified=91；实现修订累计 3；收据文件 10（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 本轮不可变快照为上海时间2026-10-18 08:11:35/design，原截止09:11:35不改；已核实实际会话身份、前台归属、旧后台禁用及原目标24约束/11禁止。第0-3段保留preflight时点，后续证据在此注明。bootstrap要求先登记一个诊断，已先登记fle-cutoff-tie-far-donor-continuity-audit后执行，不是训练变体。收尾待finish。
- 08:28:48只读确认M203-FLE在server4物理GPU0第17/50轮，原生步3370至3380/4686增长，已有16次原生VAL，早期最佳0.48853155970573425。仍低于baseline0.4894、历史M95 0.5020及目标0.5100；历史目标差距0.0080不变。未加跑VAL、选择新checkpoint或改变原训练。
- 实际执行一个新有限连续性诊断：40点dyadic人工叶，recipient及两个并列cutoff供体特征均0，严格远于top32的供体特征1。原源码在精确并列时取整叶均值，每分量0.025；两符号五个预注册精确微扰均取消并列、排除远点，输出0。20个微扰/精度条件的跳变不随微扰缩小而下降；不是只靠坐标舍入或并列候选内容不同才能发生。
- 共13种几何、float64/float32两口径26条件，56次CPU算子调用含4项CPU特征梯度检查。Fraction精确支持、独立NumPy、常值特征、保持并列的远点移动和公共平移对照一致；远点特征梯度在并列时每分量1/40，取消并列后为0。数据是构造特征与人工固定叶，不是原生FPS成员、训练mask伤害、泛化收益或新颖性证据。
- 已核实9个生产源文件及部署配置哈希未变；单线程server4 CPU执行，CUDA隐藏且未初始化。没有重跑旧旋转/精确距离数组，没有TRAIN预处理、checkpoint加载、FPS、原生网络前后向、optimizer步、模型修订、epsilon修复、准入或新启动。
- 08:28:48两张授权卡均占用：server4原M203持有training/diagnostic/exclusive三锁，server3 GPU1为外部任务。复用一次真实资源表续记两个既有原生诊断的等待，保留原冻结清单、checkpoint、cohort及容差；不共享、驱逐、reset或删锁。四个辅助授权hold本轮未到期，没有重复复查或因空槽重开。
- 初次沙箱apply_patch失败、批处理命令行过长、一次自动审批超时和只读猜测文件缺失均在科学执行前，已按实际编排情况保留；标准直接apply_patch入口及允许的一次审批重试解决。不是模型或科学测试失败，没有隐藏改门槛。
- 本轮产出为一个有限条件算子诊断及哈希证据、13几何/26精度条件、4项CPU特征梯度检查、两项资源等待核实和文档。收据用量窗口仅本轮begin至收据，排除更早读取、晚到记录和最终答复；生成前总量未知。缓存是输入子集、推理是输出子集，不重复相加、不作为账单或科学收益。

## 5. Decisions Made
- 有限问题标记complete仅表示该诊断已执行，不表示M203或新设计PASS。该结果细化既知synthetic分支风险，没有证明原生发生率或mask有害；不擅自改源、选择epsilon、停止或重启M203。
- 继续两个既有稳定ID的原生FPS/fine核及自身/非自身内容mask诊断；实际空闲授权卡、正确身份、目标资产、当前执行租约及三锁满足后沿用原协议执行。server3备选仍需目标运行时/数据核验。
- 本轮可执行有限控制均已实际完成，下一项原生测试有真实外部资源阻塞，以external_resource_blocked留档，不宣称路线耗尽，不凑新变体，不修改四个辅助hold、目标、授权或调度。
- 完整六段留档后执行finish并核实FINALIZED、context提交和租约/待提交文件释放；失败则按具体证据修复或abort，不提前声称收尾。当前无原生损害、终态收益、资源释放或用户动作需求等实质变化，保持例行心跳安静。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
