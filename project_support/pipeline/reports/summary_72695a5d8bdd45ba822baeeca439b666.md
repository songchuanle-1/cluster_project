# Research Pipeline Report - cluster_project
快照时间：2026-10-19T01:17:16.761031+00:00；生成报告时快照年龄：1221 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-19 09:17:16
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
================================================== 2026-10-19 09:17 : cluster_project ==================================================

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
- 候选累计记录 121：complete=25 / rejected=91 / blocked=4 / validation=1。
- 否决范围：unclassified=91；实现修订累计 5；收据文件 10（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T00:42:31.100493+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T00:42:31.100493+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T00:42:31.100493+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-19T00:42:31.100493+00:00 |

## 4. This Tick's Actions
- 本轮快照北京时间2026-10-19 09:17:16，design，原始表格的运行0/队列0仅指该preflight时点；以下记录随后发生的授权和启动。
- 用户在所属会话明确回复授权：仅CPA-R1一次固定配置探索性训练。授权绑定八个已测模型文件及一个配置、server4物理GPU0、seed1999/batch2/workers4/epochs50/max_iters70；不是科学PASS或通用门槛放宽。
- 限定提交c31f45994f8d68b78dfe8bb4fef3f9aaefabe86e，九个Git blob与已测字节哈希逐项一致；远端采用安全快进，不reset/clean/stash，不带入PDC/BCCA脏文件。只适配候选自身部署路径。
- M204-CPA于北京时间09:29:58单次启动，09:30:53已验证原生Train[1/50]从0增长至107，进程存活、目标UUID正确、无Traceback或不稳定损失跳步；最新状态见final_training_state.json。没有重跑上轮诊断和资源测试。
- 训练使用原始backbone而非M95头部，原生AdamW/PolyLR和训练循环不变；外层运行时在任何CUDA初始化前核对主机/GPU空闲，并全程持有training/diagnostic/exclusive三锁，禁止共享、驱逐、reset及重复启动。
- 训练已登记queue/running/experiments并标注人工探索授权、launch_verified=true、scientific_admission=false。旧diagnosis/semantic controls未通过及revision1 inconclusive全部保留。当前没有新验证集mIoU结果，提升未知。
- 其余四个候选到期只核对授权作用域：此次授权未恢复旧监督主线，维持原有人工作用域冻结并按四小时窗口复查；不是显卡阻塞，不为填槽复活旧路线或生成替代变体。收尾枚举external_resource_blocked在本轮具体指人工授权冻结，明细已留档。
- 收据用量为begin至收据写入的本地可见窗口，排除前置读取和最终回复；当前统计未知，以收据为准，不把缓存重复相加或用量当账单。实际产出为一份限定授权、一项九文件提交、一次安全同步和一次已核实训练启动，不是新增科学结论。
- 报告生成时尚未声称本轮收尾完成。finish及租约释放另行核验；远端训练获准跨tick继续，不在编排收尾时终止。

## 5. Decisions Made
- 仅执行已获授权的M204-CPA；所有其他候选的准入、禁止路线、资源卡号、调度和全局目标不变，不改共享checker。
- 按原生ScanReferVAL观察首次验证和后续收敛，再按既有baseline/champion、场景相关性和相对资源条件评价；在足够证据前不声称新颖性或收益。
- 正常收尾只表示操作记录完整，不表示科学验证通过；若真实校验失败，保存证据并abort，不停止已授权远端训练。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
