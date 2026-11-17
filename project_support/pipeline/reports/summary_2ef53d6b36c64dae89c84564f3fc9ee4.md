# Research Pipeline Report - cluster_project
快照时间：2026-10-28T20:08:32.616101+00:00；生成报告时快照年龄：1596 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-29 04:08:31
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
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-29 04:08 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_dce] Best=0.4697 9/50 no_improve=0/10 gpu=0 ? 序列: 0.4377, 0.4433, 0.4584, 0.4656, 0.4697

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=1 waiting=1 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=1
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M220-DCE | configs/Quard/ctf_hcg_csort_dce/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_dce.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 2。
- 研究储备 1 / 2；储备准备预算 1，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 6、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 1；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 148：complete=41 / rejected=94 / blocked=11 / training=1 / implementation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 26（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |
| hierarchy-parent-butterfly-token-composition | Preserve original BFC crash and verified epoch19 last checkpoint; exact checkpoint best .4992169439792633 is distinct from rounded terminal-log .499. Diagnose failing data tensor overlap, then complete concrete source-compatible recovery plan and BFC-specific human resume authorization. Only GPU0 is now allowed; do not use GPU1, cold restart or borrow HAP/M206 grants. This hold never blocks CTS. | 2026-10-26T09:04:54.984472+00:00 |

## 4. This Tick's Actions
- 截至UTC2026-10-28T20:34:43.394772+00:00，原DCE进程/源码/YAML/GPU0 context保持；最新第10/50轮2523/4686，已打印9次验证，partial best=0.4745844602584839。本轮开始时真实TRAIN9/4067→4074递增，最新短区间是否步增按原样记录。
- 优先推进已有AOC：原f7b85九源码不改，另存真实隔离0314单父PES9c，primary/runtime5c不提升，保留原NULL/ref5c。实际Git对象/字节/单父和24账/28用户/index经独审。
- 完成AOC native38软件核与条件op静态独审；正式DRAFTFalse但10执行字段NULL，无activebinding/manifest/lease、Torch/native/profile。mutation需要实际parent9c与PES技术receipt，当前primary5c实测本地拒绝、零transport；read-only观察能力保持。
- 旧10due hold仅元数据digest小核，边界未变，无新授权或人工事项。fresh canonical GPU0占用原DCE计算PID仍在，PES继续等待，无GPU1/停止/恢复/调度变更。

## 5. Decisions Made
- 项目最佳仍M95 .5020，目标.5100；DCE训练未完，不把早期验证作为收益或失败结论。
- 先PES、后AOC。GPU0自然释放且fresh owner/原deadline/实际source-assets-idle-三锁允许后，PES使用原YAML执行paired两步TRAIN与完整resources；实际通过当轮准入、派发并核步数增长。
- AOC0314只是以PES9c为父的条件源版本，不证明PES通过或可从5c直接提升18A。若PES未提升/main变动，保留全部原件并制作相同九源的真实兼容版本；不增PES训练完成或准确率门，不自动恢复旧任务。
- 本轮0新候选/模型修订/原生检查/准入/启动，已有PES+AOC继续准备，不为额度另造M223；常规操作沿用现有授权，无需用户再次确认。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
