# Research Pipeline Report - cluster_project
快照时间：2026-10-27T16:10:56.900706+00:00；生成报告时快照年龄：1933 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-28 00:10:56
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
================================================== 2026-10-28 00:10 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  无训练进程
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aef] 进程未见 (deathwatch 1/3) — 暂不处置

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
| M216-AEF | configs/Quard/ctf_hcg_csort_aef/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aef.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 2。
- 研究储备 2 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 6、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 2；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 144：complete=37 / rejected=94 / blocked=10 / training=1 / validation=2。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 22（含修订或重试，不代表成功率）。
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
- 上海00:12:33核原AEF PID消失、精确earlystop23/50标记/noimprove10且无异常尾标、source8/YAML/runtime56不变；完整原log本远大小/SHA0294c920一致，canonical archive ad76后research complete/辅助training_status对齐。23次native logger best0.495597243309021，打印/canonical0.4956，未读checkpoint指标冒充精确值。
- 本轮CREd585与HPC2f7分别现有包prepare/stage通过并真实执行独立首M95 control；各终态rc1，均0loss/0backward/0optimizer，模型构造前导入失败。CRE regex TypeError、HPC Lark transformer AttributeError，原request分别reconcile，无worker。各剩余三臂NOT_RUN，无推广或准入。
- 有范围CPU诊断保留全部负结果/采集障碍；独立regex及省略用户transformer的原grammar构造通过，其条件不等完整原import。R2/R3的loaded/source代码相同只限本进程，不证明原worker或修复。独审0528056c确认两原生失败与根因UNKNOWN；未改依赖/stdlib/全局缓存或原模型图。
- 上海00:38:35 GPU0 fresh probe idle41MiB/util0/无context/三锁available、runtime56/UUID匹配；GPU1未查/禁用。当前无新训练，障碍是原生导入就绪。主线28/status/index及非AEF12生命周期账保持；0新候选/模型修订/源码提交/同步/准入/正式训练。

## 5. Decisions Made
- AEF本次实现best0.495597低M95 0.5020约0.006403，已正常结束；不调参重跑、不将该结果扩张为整个机制的证伪。目标0.5100/项目最佳0.5020/gap0.0080仍未改变。
- CRE和HPC各自独立尝试，挂起一条未阻断另一条。两候选图均未执行、资源均未测试，不能签PASS/入队/启动，也不把CPU软件对照当原生通过或缺授权。
- 当前根因UNKNOWN；下一步先做有范围的同环境依赖导入复现与包/加载代码定位，获得证据后才能提出具体兼容修复、原生重测及同轮准入。保持原失败及源码/原YAML/data/seed1999/50-70/禁用项；不盲重放、删缓存、改shared环境或扩大资源。
- 本轮存在实质终态和原生检查失败，应通知当前无新训练及具体阻塞；无需新的常规操作授权。M206继续暂停，BFC/M201恢复与PCE/RSTR预算边界保持，不改其他项目或调度。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
