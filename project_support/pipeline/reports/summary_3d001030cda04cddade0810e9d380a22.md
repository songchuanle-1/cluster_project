# Research Pipeline Report - cluster_project
快照时间：2026-10-26T10:05:37.308291+00:00；生成报告时快照年龄：757 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-26 18:05:36
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
================================================== 2026-10-26 18:05 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cts] Best=0.4797 9/50 no_improve=0/10 gpu=0 ? 序列: 0.4207, 0.4449, 0.4632, 0.4717, 0.4797

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
| M214-CTS | configs/Quard/ctf_hcg_csort_cts/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cts.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 2。
- 研究储备 2 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 6、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 2；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 141：complete=35 / rejected=94 / blocked=10 / deployment=1 / validation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 20（含修订或重试，不代表成功率）。
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
- 本轮只读核原CTS3505065/start61122472，nativeTRAIN[9, 50, 2041, 4686]→[9, 50, 2050, 4686]；source4e8/8源/YAML/UUID0/argv/cwd/fd1保持，当前独立复核无实质疑点；本轮新启动0。
- 复用原deadline内冻结且受审的R1 op/native/checker，只重绑新owner和fresh保护基线；审后static release bytecopy与existingBEC source026c外锚，完整旧9b两smoke成功/JIT资源失败及原null/禁用包保持，不继承为R1原生通过。
- 真实执行currentowner/new026c/external-anchor NoTransport guard：GPU0到达registered CTSbusy拒绝、GPU1按明确GPU0-only拒绝；0transport/process/network/Torch/active材料。该软件保护核验并非硬件idle或native资源PASS；R1仍pending/四原生臂NOT_RUN。
- CTS catalogue对齐真实训练；experiment只修辅助training_status waiting→running，queue/running/receipt/source保持。主线4e8/28用户文件/index及其他139候选/其他11受保护账不变，前对象/精确diff与保护audit留档。
- 旧10到期仅有界metadata复核：旧8记录及655声明ref/M206暂停与509e一致，原14授权metadata同、现15仅新增已知GPU0-only撤回；未读655目标/旧grant/checkpoint体，无新许可或可行动事项。证据held_boundary_check.json SHAed313bb0799275f8fe6e1bccae03196e1cd1b80d95b589983ec71f040cc08441。
- 0新候选/修订/Git/准入/入队/派发/训练启动，未超creation预算0；仅GPU0，M206暂停/BFC未恢复/调度Disabled保持。

## 5. Decisions Made
- CTS继续原GPU0训练，验证指标/效果本轮未知；目标.5100/M95.5020/gap.0080保持。
- BEC R1等待原CTS释放GPU0；fresh真实idle/UUID/assets/三锁/currentowner通过后，按原YAML跑固定M95/R1 TRAIN2与资源臂，不换样本/seed/阈值，不对原运行同步026c。
- 以当前真实resource_check/blocked留档收尾，不凑准入额度，不将NoTransport或静态工具当科学PASS。既有授权足够常规后续工作，无新增确认请求。
- 前e2e3中断收据为INCOMPLETE；本轮不预签postflight，最终以canonical finish和实际FINALIZED/released为准。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
