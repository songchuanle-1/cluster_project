# Research Pipeline Report - cluster_project
快照时间：2026-10-16T18:09:30.238169+00:00；生成报告时快照年龄：481 秒；模式：event

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-17 02:09:29
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
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-17 02:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1] Best=0.4735 9/50 no_improve=1/10 gpu=0 ?

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=1 withdrawn=6
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M202-HDS | configs/Quard/ctf_hcg_csort_hds_canon_r1/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | running |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 2；准入预算 1。
- 研究储备 4 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 102：training=1 / rejected=91 / complete=6 / blocked=4。
- 否决范围：unclassified=91；实现修订累计 2；收据文件 9（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 本轮event由ledger_changed触发，begin快照2026-10-16T18:09:30.238169+00:00；无新终态、无到期候选。四个human scope holds尚未到期，未重复审查；储备4/2，准备预算0。
- 后续只读采样时间2026-10-17T02:15:00.277591+08:00，同一M202/PID1592337/server4物理GPU0两次间隔7秒采样，原生['Train', '9', '50', '3140', '4686']→['Train', '9', '50', '3159', '4686']，确认实际进度增长。正确UUID、原三把生命周期flock及运行守卫保持，采样尾部无新异常。
- 同一模型9个Python文件、1个部署YAML及native train/utils共12项哈希与恢复前冻结值一致；无源码/config/优化器/seed/schedule/修订/准入变更。
- 当前run原生scalar日志精确mIoU序列[0.4731247127056122]，继承epoch7的best后当前best=0.47346487641334534。表达分母仅引用原生日志：[[9508]]；重复VAL不是独立场景样本，场景级置信区间/泛化和最终效益仍未知。
- 本轮实际产出为1份当前native连续性及scalar记录；没有新候选、新模型、结构修订、GPU诊断、重新启动或恢复测试。上一轮48次CUDA与反向测试仅作历史背景，不重复计入本轮成果。TypeError历史根因及全程峰值显存仍未知。
- 用量窗口仅为本轮begin至收据的本地可见记录，先前读取及最终回复不在内；当前最终值未知，以收据原始值为准，cache已含于input、reasoning已含于output，不重复相加，不当作账单。

## 5. Decisions Made
- 继续同一已准入主线训练及冻结评估方案，不因单轮VAL未刷新best而调参、停分支或把机制科学否定；早停仍按原协议。
- 未出现需用户处置的新故障、完成或实质状态变化，按既有心跳规则保持安静。保留原TypeError及所有失败证据，不宣称根治。
- 完整六段留档；写入时postflight尚未运行，必须finish成功并核实租约释放后才称本轮执行完成。不修改调度、通知策略、其他项目或恢复M201。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
