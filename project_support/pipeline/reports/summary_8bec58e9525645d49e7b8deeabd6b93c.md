# Research Pipeline Report - cluster_project
快照时间：2026-10-21T15:28:12.135717+00:00；生成报告时快照年龄：121 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-21 23:28:11
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
================================================== 2026-10-21 23:27 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc] Best=0.4872 26/50 no_improve=9/10 gpu=0 ? 序列: 0.4784, 0.4755, 0.4803, 0.4723, 0.4655

  >>> 队列推送: [M206-CGCA coarse conditioned fine channel attention] on server-4 gpu1
  >>> 已推送，队列已更新
  [日报] 1 条事件 → D:/project\cluster_project\pipeline\monitoring\2026-10-21.md

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
- 活跃 2（运行 2 / 认领 0 / 等待 0）；目标 4；准入预算 2。
- 研究储备 2 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 2；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 133：complete=28 / rejected=94 / blocked=8 / training=1 / deployment=1 / validation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 12（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |

## 4. This Tick's Actions
- 最新人类“gpu1可以使用”已按server4上下文记录，恢复allowed[0,1]/每卡1任务；GPU0 M205保留，server3/server6仍禁用。手动事务在.pipeline.lock下保存beforeimages、新资源授权及同M206 GPU1 resume双proof，原GPU0-only证明保留。
- 启动前严格SSH核dl04-MS-7E06、两张GPU UUID、GPU1无context/显存空闲、M205原PID/argv/cwd/starttime；固定epoch8完整checkpoint SHA新重核一致，原898ff远端源码精确核验通过，无同步或YAML更改。
- 续训入口最小支持当前白名单内server4 GPU0/1，任务和双hash证明须同卡；人类授权/完整state/精确source/checkpoint/禁止冷启动守卫保持。相关116离线回归及独立22专门测试通过，独立复核无阻断，未修改实验模型代码。
- 上海23:27 canonical begin已通过原准入和新GPU1证据派发M206，launch_verified=true。23:29:03额外实测GPU1 PID732137、exact --resume argv/原cwd及native Train9/50步骤102→103；日志明确恢复start_epoch9、best .4751223027706146、no_improve0，并载入optimizer/scheduler。GPU0 M205原PID3842306/starttime保持，monitor26/50、Best.4872、no_improve9/10。
- 当前双卡running2/waiting0，M206 deployment→training/resumed记录及三账对齐。HAP储备保留native UNKNOWN且双卡均忙，reserve/creation0；无新模型候选/准入，旧hold范围与修订限制不变。

## 5. Decisions Made
- 新GPU1授权覆盖此前GPU0-only对server4GPU1的限制；后续server4GPU0/1每卡1任务，旧server3/server6禁用及科学/数据/seed/schedule/bans/调度保持。M206完整续训已实际核验，不重复启动或冷重训。
- 保留M205原patience10，不因新GPU1可用而停机或迁移。M206后续按原协议训练；当前保存的Best为checkpoint历史值，不称新验证收益。
- 当前人类请求已完成；HAP真实native检查待授权卡实际空闲，使用fresh lease/匹配卡UUID/query/locks/env和reviewed worker_v2。资源授权不重开任何旧scope/数值hold或额外修订。完整审计按当前token收尾，不预写PASS。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
