# Research Pipeline Report - cluster_project
快照时间：2026-10-16T05:09:54.450975+00:00；生成报告时快照年龄：492 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-16 13:09:53
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
================================================== 2026-10-16 13:09 : cluster_project ==================================================

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
- 候选累计记录 100：blocked=5 / rejected=91 / complete=4。
- 否决范围：unclassified=91；实现修订累计 2；收据文件 5（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 快照北京时间2026-10-16 13:09:54，design，原deadline14:09:54；begin已唯一执行监控和目标检查，均返回0。授权server3 GPU1+server4 GPU0，各1槽，活跃0、准入预算2、储备5/2、准备预算0；没有重复preflight。
- 续做主线已登记的环境准备。严格已知主机密钥和hostname核验后上传项目专用server4入口，远端SHA256=6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0。首次核验因Windows文本管道CRLF失败，完整原样归档；改为UTF8字节传输后13:13:07+08核验通过。
- 实际Conda解释器/home/songcl/.conda/envs/project_cluster/bin/python、PyTorch2.8.0+cu128正常加载，CUDA未初始化。通过后才把SERVERS的server4 conda_source绑定到项目独立入口；未改共享Python/依赖/模型、seed或schedule。此项仅证明部署和导入，不是完整原生模型、GPU计算、准入或训练。
- 按ID及分页处理全部5项到期记录。主线保留原诊断/对照/原生反向/独立性4项通过和资源/约束2项失败：10.034588748G超过10G、实现修订2/2已用完。其余4项辅助路线的范围冻结未解除，只归档当前授权检查并将人工授权复查设为四小时后；所有100项科学阶段、门槛和修订历史不变，95项记录完全未动。
- 当前科学状态blocked/human_authorization，执行状态POSTFLIGHT_PENDING。真实剩余前置条件是外部人工授权，不是显卡占用；用external_resource_blocked记录这一明确种类，不声称GPU不足、路线穷尽或deadline到达。未收到额外修订授权，不开启revision3，不制造新候选或填卡变体。
- 本轮实际产出为项目专用环境入口部署与加载核验、1条传输失败留证、5项授权/操作记录更新；新候选/核心实现修订/原生前后向/优化步数/准入/训练全部0。实时GPU占用未知，不重复旧资源探针。收据用量此时未知，仅统计begin至收据的局部日志；缓存含于输入、推理含于输出，不重复相加，不视为账单。

## 5. Decisions Made
- 维持server3 GPU1和server4 GPU0两槽，只在现有科学准入门槛全部满足后派发。保留原始失败、四项辅助范围冻结及M201不自动恢复约束；环境编排修复不计为第三次模型实现修订。
- 所有五项人工授权阻塞使用四小时复查和原goal/SERVERS/授权文件wake_paths；实际新授权可提前唤醒，计时本身不授予权限。不修改自动化或系统调度，不把操作记录数量当科研进展或成功率。
- 运行finish，以真实postflight及租约释放核验决定是否COMPLETED；若不接受这一明确的人为授权阻塞，保留所有证据并abort，不改检查器、不假装GPU被占用、不等待截止。下次自动化精确触发时间未知。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
