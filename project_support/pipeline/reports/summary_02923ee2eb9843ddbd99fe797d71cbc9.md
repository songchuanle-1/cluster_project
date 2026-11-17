# Research Pipeline Report - cluster_project
快照时间：2026-11-07T09:04:34.955916+00:00；生成报告时快照年龄：162 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-11-07 17:04:34
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
================================================== 2026-11-07 17:04 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  无训练进程

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 waiting=2 withdrawn=6
    待推: [M206-CGCA] configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml gpu=1
    待推: [M227-LFT] configs/Quard/ctf_hcg_csort_lft/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_lft.yaml gpu=1
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| 无 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 队列无登记运行；远端进程须另核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
| 2 | M227-LFT | configs/Quard/ctf_hcg_csort_lft/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_lft.yaml | waiting | - | server-4 |
- 活跃 0（运行 0 / 认领 0 / 等待 2）；目标 3；准入预算 2。
- 研究储备 0 / 3；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 7、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 0；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 158：complete=51 / rejected=94 / blocked=13。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 13；收据文件 37（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |
| hierarchy-parent-butterfly-token-composition | Preserve original BFC crash and verified epoch19 last checkpoint; exact checkpoint best .4992169439792633 is distinct from rounded terminal-log .499. Diagnose failing data tensor overlap, then complete concrete source-compatible recovery plan and BFC-specific human resume authorization. Only GPU0 is now allowed; do not use GPU1, cold restart or borrow HAP/M206 grants. This hold never blocks CTS. | 2026-10-26T09:04:54.984472+00:00 |
| hierarchy-nonlinear-lifting-analysis-synthesis | Preserve LFT manually paused checkpoint22, original source4457, receipt and paused_run. No resume, migration or cold start until later explicit human authorization; GPU1 remains excluded. WFC alone continues GPU0. Paused research stage is blocked/human_authorization. | 2026-11-04T08:16:35.222364+00:00 |

## 4. This Tick's Actions
- 09:04:34Z begin为design，monitor/goal正常，无新增终态、项目training/claiming或ready待跑；实际所属会话与禁用的Pipeline-cluster_project已核验。
- 09:04:36Z实际只读核验固定server4/GPU0 UUID/runtime0ccc、/proc、三锁和显存。free16740<原20000MiB，外部PID3508948占15766MiB保留；无项目trainer，原三锁可用。仅真实预算不足，不以context/util拒绝共享。
- NSD保存本轮实际resource_check/blocked证据；无新owner release/binding/intent/manifest/lease/request/stage、GPU/native执行或完整模型资源测量。复用原已审包与有效证据，不重制或重跑旧套件。
- 原f74前执行拒绝/reconcile、旧部署整体false和后续禁用成对指针软件补件审计保持。实核主线0ccc、28用户文件/index/WFC/LFT源、固定配置与受保护生命周期账本不变，NSD未部署。
- 独立代理只读确认当前owner六字段、时间窗口/主机/runtime/GPU0 UUID/白名单/共享政策/原预算全部匹配；16740<20000、缺3260MiB支持resource挂起，无项目trainer与三锁可用不解除预算，未建立新操作授权或模型资源PASS。

## 5. Decisions Made
- NSD继续resource blocked/resume validation，retry2026-11-07T10:04:36Z。fresh GPU0free>=20000/项目max1/原三锁/原1020秒run余量满足后，另存受审真实currentowner/source/runtime/root/UUID/producer/baseconda绑定；不续旧lease、补旧NULL或盲重放拒绝意图。
- 原YAML/数据seed/loss/commoninit/自然TRAIN2有限backward/整core更新/完整同口径成对资源与独立实测审查实际通过才准入入队、授权槽启动并核步数。当前native/Torch/autograd/完整资源/真实归一化/部署仍NOT_RUN。
- 本轮新candidate/准入/入队/启动均0，不为配额新增变体或制造准备事项。保持全部holds/bans、M206/M227人工暂停、PSC/HVD归档不重启、GPU0原预算/共享条件与调度。
- report/finish、context提交/lease释放由随后真实命令和收据确认，不预称成功。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
