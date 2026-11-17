# Research Pipeline Report - cluster_project
快照时间：2026-10-22T20:07:24.856321+00:00；生成报告时快照年龄：1168 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-23 04:07:24
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
================================================== 2026-10-23 04:07 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hrc] Best=0.4795 12/50 no_improve=1/10 gpu=0 ? 序列: 0.4589, 0.4728, 0.4790, 0.4795, 0.4732

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=1 waiting=2 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=1
    待推: [M209-PSBR] configs/Quard/ctf_hcg_csort_psbr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psbr.yaml gpu=0
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M208-HRC | configs/Quard/ctf_hcg_csort_hrc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hrc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
| 2 | M209-PSBR | configs/Quard/ctf_hcg_csort_psbr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psbr.yaml | waiting | - | server-4 |
- 活跃 2（运行 1 / 认领 0 / 等待 2）；目标 3；准入预算 1。
- 研究储备 1 / 2；储备准备预算 1，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 5、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 1；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 136：complete=30 / rejected=94 / blocked=10 / training=1 / deployment=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 15（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |

## 4. This Tick's Actions
- actual thread/target一致；canonical SKILL/experimentfirst/foreground及goal/SERVERS/当前memory已核，goalSHA0441/onlyserver4GPU0/max1/GPU1释放/M206paused/WindowsDisabled保持。前d6 FINALIZED released且无headless lock/pending才begin；原20:07:24.856321UTC/deadline21:07:24.856321不改。
- begin先monitor/已有队列派发/goal各一次，operationalissues空、新终态0；1running/0claiming/1readyPSBRwaiting，M206paused waiting另计。10旧blocked notdue不重审655/旧8，不重复授权问题或造新候选。
- 2026-10-23 04:08:04上海额外只读精确HRC原PID2780804/start29604100/原argv/cwd/remoteHEAD74f/GPU0 UUID核，native12/50两次3582→3592/4686、无error；仅GPU0原HRC context，未查询GPU1。begin04:07partial best.4795/noimprove1，非终态结果，champion仍M95.5020距目标.0080。
- 既有PSBR74f/c85ae4fe receipt与3summary/readonly admission有效，仍waiting无hold/PID；主74f/index空/28status与小字节hash保持、PSNC独立43单亲74f且9blob同冻结302。HRC/M206人工pause/HAP自然earlystop原记录不变，无活跃checkout改动。
- 继续同一PSNC完成完整operational adapter/remote_ops/native包，原worker/原YAML/TRAIN2/资源协议及双idle/3锁不变。离线模拟检查和独审实际结果留档，不声称真实模型路径/backward/效率已测。旧d6 disabled准备与9源hash不改，本轮0新candidate/commit/sync。
- 独审通过后root仅copy已审static release并外部hash锚定；它仅批准确切工具module/version，不是freshlease/GPU空闲/执行授权证明。candidate resumevalidation而stage仍blocked。静态准备provenance可跨tick复用，实际运行需操作时freshowner/context/deadline/exactsource/assets/allowedGPU0/locks，禁止重放旧binding。
- root实际本项目Adapter.prepare(0)注入NoTransport，真实registered GPU0 HRC busy guard提前Refused，transport_calls0/SSH或GPU事件0/torch未导入/production执行dir与manifest/lease/binding均未创建，既有台账和module/staticreleasehash不变；不是实际原生或资源结果。
- 当前tick_attempt是真resource_check blocked，当前HRC进展/新完整工具及guard证据全部同归PSNC。0新native/资源profile/标准summary/receipt/queue/launch；后续空GPU0且PSBR版本派发边界安全才可真实原YAML四进程pair，按实际结果review/准入/派发，不为本轮检查通过冒称方法有效。
- 七段memory/六段report后按原token finish，真实返回/FINALIZED released/headless lock+pending消失才确认完成；释放后不回写。GPU1给别人/M206不恢复、不变资源白名单/原失败/修订上限/目标/调度，无需新用户处理事项。

## 5. Decisions Made
- canonical other决策已保存：完成已有PSNC完整检查编排与静态外锚并验证真实busy拒绝；等待实际GPU0和受保护版本条件，不新建重复候选、不把模拟/静态当科学准入。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
