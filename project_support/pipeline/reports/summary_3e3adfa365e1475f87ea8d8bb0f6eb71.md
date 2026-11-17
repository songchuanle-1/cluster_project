# Research Pipeline Report - cluster_project
快照时间：2026-10-21T02:08:12.177619+00:00；生成报告时快照年龄：190 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-21 10:08:11
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
| server-4 | 1 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-21 10:08 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc] Best=0.4741 9/50 no_improve=0/10 gpu=0 ? 序列: 0.4370, 0.4486, 0.4531, 0.4717, 0.4741
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca] Best=0.4462 7/50 no_improve=0/10 gpu=1 ? 序列: 0.3808, 0.4165, 0.4208, 0.4314, 0.4462

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=2 withdrawn=6
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M205-MDC | configs/Quard/ctf_hcg_csort_mdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |
| M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | server-4 | 1 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 2（运行 2 / 认领 0 / 等待 0）；目标 5；准入预算 2。
- 研究储备 1 / 3；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 1；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 133：complete=28 / rejected=94 / blocked=8 / training=2 / validation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 12（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |

## 4. This Tick's Actions
- 上海2026-10-21 10:08 begin完成监控、目标和已有合格队列派发检查；无终态/运维问题、waiting0。M205-MDC Best=.4741、第9/50轮，M206-CGCA Best=.4462、第7/50轮，均no_improve0/10。持续训练，收敛和最终收益尚未确定。
- 10:08:52核验pinned server4主机/授权两卡UUID、memory/util/context与必要锁：GPU0 PID3842306约18643MiB、GPU1 PID3873690约19751MiB仍有CUDA contexts，两卡均非idle，既有训练未动。
- HAP本轮1次真实资源检查blocked，绑定当前tick_attempt/新证据并更新资源wake条件。已准备的HAP源码/原YAML/完整包/已审worker_v2证据复用；未重复staging、busy guard、控制测试或torch/model/data/GPU执行。
- 旧8个blocked到期，委托一次有界只读复核：4项辅助监督scope hold、2项数值测量实现hold、PCE/RSTR修订耗尽仍保持；本轮未见解锁授权或新修复证据，全部未重开，旧记录未改。
- 0新候选、0模型源提交、0原生执行、0准入/队列/启动。当前没有新增用户动作或可用资源。

## 5. Decisions Made
- 两项现有训练遵循原seed/schedule/验证/早停协议继续，不因低util或旧flock可用共享运行卡，不按当前训练中指标断言最终效果。
- HAP真实授权空卡出现后，用下个owned tick fresh token/lease/stage和已审tick_73e1f420/worker_v2.py及精确f51823bb源/原YAML/资产，核验UUID/contexts/locks后执行实际TRAIN两步/配对资源，实测PASS才准入/安全同步/派发。
- 旧hold到期只复查证据，不产生重开、额外历史修订或新批准；实验优先授权不越过历史限制。挂起项不阻断HAP，当前真正阻塞仍是两卡运行占用。
- 无目标/资源边界/禁用项/调度变更、无新用户决定。当前为健康运行和同一资源等待，按通知约定静默；不凑配额、不重复已有诊断。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
