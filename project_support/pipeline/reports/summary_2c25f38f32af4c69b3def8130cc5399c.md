# Research Pipeline Report - cluster_project
快照时间：2026-10-23T06:18:00.269793+00:00；生成报告时快照年龄：1136 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-23 14:17:59
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
================================================== 2026-10-23 14:17 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psbr] 1/50 尚无验证 - gpu=0

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
| M209-PSBR | configs/Quard/ctf_hcg_csort_psbr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psbr.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 1 | M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | waiting | - | server-4 |
- 活跃 1（运行 1 / 认领 0 / 等待 1）；目标 3；准入预算 2。
- 研究储备 0 / 2；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 5、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 0；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 136：complete=31 / rejected=94 / blocked=10 / training=1。
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
- canonical实际owner/target、最新memory/授权、goalSHA0441/SERVERS未变和WindowsDisabled核验；前b96c收据FINALIZED released且无lock/pending，原deadline不延长。begin一次monitor/goal/已有派发，PSBR1/50运行，无新operationalissue；HRC终态前轮已通知。
- 2026-10-23 14:19:58上海只读精确PSBR2372658/start35234267/原argv/cwd/74f/UUID与GPU0原context，两样本1/50 1296→1304/4686，无error。唯一授权GPU0忙，GPU1不查不用，M206继续暂停，PSNC现成51项完整工具不重造。
- 按预算新增且仅新增M211-BTC：父组真实支持middle几何平衡二叉树inside/outside补集组合，保留M95原cf skip/fine/coarse/rawbanks/CSORT/HCG/单inst，原YAML逐字不变。589静态断言42标签及独立11+22生产纯树案例通过，两源码独审无确定bug；无torch/native/梯度/资源实测。
- 通过standing grant普通本地isolated commit00e2b18接43，仅冻结9新文件，actual staged/final blob匹配；main74f/index/28原文件及原queue/running/experiment/receipt保持，原PSNC43保留。首次版本helper误拒绝defaultLFS在写worktree前停止，限定exactdefault+skip-smudge/无相关attrs后成功，未更改共享config或科学阈值/源码。
- 新候选stageblocked/exclusive_gpu_slot/resumevalidation，native_execution仍null；current tick_attempt是实际implementation_test静态passed且证据归属新候选。已备PSNC+BTC两具体准备，0新准入/queue/launch/remote sync，不以compact blocked排除后的reserve0继续无限造候选。
- 七段memory和完整六段report按真实证据更新，原tokenfinish及receipt/lock释放核验后才确认。当前bestM95.5020/目标.5100差.0080；下一步保持PSBR原run，真实GPU0空槽后freshbinding依序推进PSNC和BTC真实原YAML TRAIN2/原资源。

## 5. Decisions Made
- 保留BTC一个独立可证伪结构储备，与已完成准备的PSNC合计两项；不凑预算、重复审旧hold/655、或重造PSNC工具。
- 版本仅普通本地独立保存，不改活跃PSBR源码/原配置、资源/调度/禁用项。原生和资源尚未执行，不准入；不提出已有授权覆盖的重复权限问题。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
