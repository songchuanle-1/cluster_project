# Research Pipeline Report - cluster_project
快照时间：2026-10-24T00:03:32.596669+00:00；生成报告时快照年龄：908 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-24 08:03:31
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
================================================== 2026-10-24 08:03 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psnc] Best=0.4108 4/50 no_improve=0/10 gpu=0 ? 序列: 0.3405, 0.3756, 0.4108

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
| M210-PSNC | configs/Quard/ctf_hcg_csort_psnc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psnc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 2。
- 研究储备 0 / 2；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 5、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 0；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 137：complete=32 / rejected=94 / blocked=10 / training=1。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 16（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| hierarchy-coarse-conditioned-fine-channel-attention | Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others. | 2026-10-22T16:24:16.243554+00:00 |

## 4. This Tick's Actions
- 2026-10-24 08:05左右上海只读双核原PSNC PID2502712/start41082267/argv/cwd/fd1唯一log/HEAD43/GPU0UUID，真实Train4/50 1352→1361/4686增长，无error。GPU1未查未用，无signal/重启/源码变动。
- 复用既有BTC00e冻结9文件，逐字节匹配原c36b prep及Git00e/parent43；仅在本轮诊断目录准备专属nativeworker/runtime和完整guarded adapter/remote_ops，原模型源/YAML/seed/schedule/data不改。
- 实际10项AST/生产纯stdlib/observer stub边界检查通过，原resources/7安全函数AST保持；46项离线orchestration/mock测试全PASS、0真实Popen/socket/torch。11早期子集不重复计数，旧589不重跑。
- 冻结native14prepared/12diagnostic及outer26map，经43项独立只读整包审核无问题；root仅materialize同字节reviewed staticrelease和外部candidate锚，所有active执行字段仍null，无lease/真实GPU检查/receipt/queue。
- 实际root当前owner/context/pending/外锚guard通过；NoTransport prepare在registeredPSNC占GPU0时于probe/目录/lease之前拒绝，GPU1及deadline不足同样拒绝，0transport与共享文件变化。
- 前a4f已归档PSBR23/.4969虽再次列为快照new_terminal，此轮不重复归档/当新完成。M206暂停、GPU1让出、28保护/index/main43及原资源/目标/禁用项/调度保持；8旧hold未重读或重开。

## 5. Decisions Made
- BTC已从缺少专属native操作工具推进到完整静态准备并离线验收；实际TRAIN2/参数初始化配对/FP32/autograd/n>=3梯度/资源/效能仍NOT_RUN或UNKNOWN，不生成原生PASS/准入/排队。
- 未来仅在PSNC自然结束且实际授权GPU0空闲后，以freshowner/deadline/assets/UUID/双idle/三锁运行M95/BTC原TRAIN2及原资源pair；保持原source00e/protocol，挂起旧路线不获恢复/额外修订。
- 当前PSNC继续原生训练且无错误，本轮正式validation指标未采集；M95仍0.5020距目标0.5100差0.0080。不为了缺口调参、造重复候选或打扰现有训练。
- 完整BTC执行入口准备完成属于本轮实质变化，NOTIFY；无需用户新增确认。report/finish按原deadline真实收尾，不提前写成功。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
