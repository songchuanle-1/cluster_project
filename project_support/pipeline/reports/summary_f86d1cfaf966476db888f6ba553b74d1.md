# Research Pipeline Report - cluster_project
快照时间：2026-10-25T20:07:28.056644+00:00；生成报告时快照年龄：1637 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-26 04:07:27
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
| server-4 | 0 | 未知 | 未知 | 未知 |
| server-4 | 1 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-26 04:07 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr] Best=0.4995 19/50 no_improve=1/10 gpu=1 ? 序列: 0.4915, 0.4940, 0.4955, 0.4995, 0.4963
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc] Best=0.4487 6/50 no_improve=0/10 gpu=0 ? 序列: 0.3245, 0.3793, 0.4063, 0.4208, 0.4487

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=2 waiting=1 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=1
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M212-BCR | configs/Quard/ctf_hcg_csort_bcr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bcr.yaml | server-4 | 1 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |
| M213-BFC | configs/Quard/ctf_hcg_csort_bfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 2（运行 2 / 认领 0 / 等待 1）；目标 4；准入预算 2。
- 研究储备 2 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 5、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 2；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 141：complete=34 / rejected=94 / blocked=9 / training=2 / validation=1 / implementation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 19（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |

## 4. This Tick's Actions
- 实际会话与target匹配，前6bdb已FINALIZED/released/锁状态消失后begin；snapshot2running/0ready、creation/reserve0，due仅CTS+BEC，旧9不due，无新终态/连接源故障。未改调度或重复preflight。
- 本轮有界双样本确认BFC GPU0第6/50轮4352→4360、BCR GPU1第19/50轮2731→2737；原PID/start/argv/cwd/log/8源/YAML77e/UUID/唯一context保持。公共runtime48fc和BCR科学11a分开核实，独审23项通过；当前best等实时指标UNKNOWN。
- 现有CTS静态catalog以本轮fresh owner/context/rawUUID/原deadline实际通过localguard，两registered卡prepare0/1均在transport前拒绝；14非法入口与deadline拒绝、0process/network/Torch/active。原51cbc/03329/7036/4e8与公共48fc均保持，非native或资源PASS。
- 准备CTS原M95/CTS四臂真实结果语义checker并完成实际本地软件检查/独审，针对03329原native schema核2TRAIN原loss/backward/optimizer、输入/common配对、3distinct/multiround/r1与3W块聚合grad/update、原资源口径与fullunsupported；未提供任何真实CTS raw结果，未造标准PASS/receipt。
- 为既有BEC原2d0606/6555准备禁用/无版本native observer、runtime、manifest/template，完整保留原resource函数AST与原数据/criterion/optimizer。实际本地生产AST/list-set载体与回调、合法零边界及disabled/null拒绝检查、独审完成；未Torch backward/GPU/SSH/Git/active。
- 0新模型候选/0准入/0queue/0启动/0训练终态，保护两原运行、M206pause、旧9与固定goal/资源/bans/data/seed/schedule/YAML。BFC48fc主线/index/28status+bytes、10运行归档账核保持，141候选IDs未增删。

## 5. Decisions Made
- 准备名额已满，不再扩展变体；优先填已有CTS真实结果检查与BEC未来原生观测缺口，卡忙期间仅做本地软件准备，不抢占或恢复既有实验。
- 所有软件fixture/AST/边界测试只证明工具准备，实际原TRAIN2、配对、梯度更新、同口径资源和收益仍未测。CTS使用已有源4e8；BEC code/source/未来parent均null，未来选择兼容实际tested main的版本再另建受审绑定copy，不回写历史null。
- 后续自然空出授权卡且fresh owner/deadline/UUID/liveidle/assets/三锁通过，再跑CTS原M95对照与真实检查；实际通过才准入并尝试派发。M95完成最佳.5020距目标.5100仍.0080，M206继续暂停，无新增用户授权项。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
