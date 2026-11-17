# Research Pipeline Report - cluster_project
快照时间：2026-10-31T02:12:31.415190+00:00；生成报告时快照年龄：292 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-31 10:12:30
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
================================================== 2026-10-31 10:12 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_sfc] Best=0.4966 24/50 no_improve=3/10 gpu=1 ? 序列: 0.4960, 0.4966, 0.4938, 0.4937, 0.4897
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_elc] Best=0.5015 23/50 no_improve=1/10 gpu=0 ? 序列: 0.4943, 0.4941, 0.4981, 0.5015, 0.4948

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
| M224-SFC | configs/Quard/ctf_hcg_csort_sfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_sfc.yaml | server-4 | 1 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |
| M225-ELC | configs/Quard/ctf_hcg_csort_elc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_elc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 2（运行 2 / 认领 0 / 等待 1）；目标 4；准入预算 2。
- 研究储备 2 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 6、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 2；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 153：complete=45 / rejected=94 / blocked=10 / training=2 / validation=2。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 31（含修订或重试，不代表成功率）。
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
- 本轮2026-10-31T02:13:19.477632+00:00核实原SFC TRAIN[24, 1966]→[24, 1972]、部分best 0.49663493037223816；原ELC TRAIN[23, 3188]→[23, 3193]、部分best 0.5015384554862976。原PID/start/source/YAML/UUID、两日志增长和观测尾部无异常均核，未读checkpoint体。
- 实际物理查询 2026-10-31T02:13:15.132484+00:00 核实GPU0/1仍由原两训练占用；原始hostname/NVML inventory/compute PID及canonical validated_state结果绑定本轮owner/context和两储备候选，busy[0,1]/idle[]。
- 预算reserve2/creation0；已备WFC/LFT静态工具保持，未重复旧suite/改实验源码/新候选/原生检查/准入/正式启动。仅更新例行部分进度和资源证据，原冻结包/科学状态保持。
- 复用两套已审运行相位观察器，源字节与前轮相同；本轮两原任务实际TRAIN增长且VAL flags为false，不能以rc0或VAL代证TRAIN。未改模型、native-smoke/新launch TRAIN门或既有静态工具。

## 5. Decisions Made
- 本轮健康在训/资源等待，未完成、无新科学结论或用户动作；依通知策略静默。冠军M95 .5020/目标 .5100保持，部分指标随原训练推进不用于替换冠军或宣称效力。
- 现有两储备保validation，native/resources NOT_RUN；下一合法真实空槽先核实际source兼容/授权/owner/三锁，执行既有原生YAML TRAIN2和完整资源检查，通过才准入入队。不开新路线填额度，不重开旧holds或暂停任务，不更改资源/参数/调度。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
