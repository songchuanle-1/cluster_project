# Research Pipeline Report - cluster_project
快照时间：2026-10-26T22:03:25.203343+00:00；生成报告时快照年龄：1613 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-27 06:03:24
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
================================================== 2026-10-27 06:03 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bec] Best=0.4879 13/50 no_improve=1/10 gpu=0 ? 序列: 0.4769, 0.4803, 0.4860, 0.4879, 0.4868

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
| M215-BEC | configs/Quard/ctf_hcg_csort_bec/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bec.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 2。
- 研究储备 1 / 2；储备准备预算 1，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 6、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 1；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 142：complete=36 / rejected=94 / blocked=10 / training=1 / validation=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 21（含修订或重试，不代表成功率）。
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
- 原BEC source026c/PID1558071/start64444390在唯一GPU0真实TRAIN13/50 4117→4126，sole19768MiB；当前7bbb观测和d642 peer核源8/YAML/收据/R1digest/三账，未动原进程。
- 新增唯一M217-CRE：c760冻结8独立model+原YAML，46实际stdlib接线/索引软件检查，独立源码审和实际隔离单父026c/恰9A/clean source版本审；无Torch/native/resource或效果实测。
- AEF复用已有完整工具，当前6771 NoTransport guard证实prepare0忙/1未授权，零transport/process/network/Torch/新GPU查询/active；硬件证据为另采本轮原BEC样本。

## 5. Decisions Made
- 1新候选/1隔离source commit、0revision/准入/入队/launch；CRE stageimplementation、native/resourcesNOT_RUN，AEF保持validation和resource_checkblocked，不增exclusive槽位hold。
- 原始22:03:25缓存Best.4879/13of50/noimprove1与稍后TRAIN增长分开；M95.5020/目标.5100/gap.0080不变，无新champion/最终效果。
- CRE静态参数差−1182720仅算式，真实FLOPs/latency/memory/梯度/common初始化/准确率未知；CPA r1的无投影点积softmax读取与CRE联合非线性向量消息的图区别已准确记录，不声称移除QKV创新。
- CRE与AEF56都是026c子版本；若main先推进，必须新兼容版本并实测，保留旧proof，不跨兄弟ff或重标旧raw。
- 继续原BEC，仅等待唯一GPU0真实可用时fresh currentowner/原deadline/UUID/资产/三锁运行现成AEF原生配对；CRE后续只做必要专属native工具。
- 其他140候选/14生命周期账/primary026c和28status+bytes/index保持；postflight/finish由root按实际执行，不预签成功，无新增人工权限请求。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
