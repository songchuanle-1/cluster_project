# Research Pipeline Report - cluster_project
快照时间：2026-10-16T06:27:02.723217+00:00；生成报告时快照年龄：328 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-16 14:27:02
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
================================================== 2026-10-16 14:26 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1] 1/50 尚无验证 - gpu=1

--- server-4 (192.168.1.115) ---
  无训练进程

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4
  server-3: running=1
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M202-HDS | configs/Quard/ctf_hcg_csort_hds_canon_r1/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1.yaml | server-3 | 1 | 未知 | 未知 | 未知 | 未知 | 未知 | running |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 2；准入预算 1。
- 研究储备 4 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 100：training=1 / rejected=91 / complete=4 / blocked=4。
- 否决范围：unclassified=91；实现修订累计 2；收据文件 7（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 本轮快照2026-10-16 14:27:02+08，design；begin已完成唯一一次监控和目标检查，1运行/0认领/0等待、容量2、准入预算1、储备4/目标2、储备新增预算0。变化是前一轮真实授权和启动的状态延续，本轮没有新目标或资源授权，也没有新终态。
- 14:29:48+08仅对原PID40465做连续性核验：server3物理GPU1、固定UUID、同一代码目录，原生Train[1/50]从1426增至1430/4686，三项原始GPU1 flock文件描述符仍在，采样日志无Traceback/OOM/RuntimeError。尚无VAL结果，不把历史champion、训练步数或初始化best当新收益。
- 实时NVML样本GPU1总24268MiB、用24110MiB、余158MiB、util29%，PID占24105MiB。该值含上下文/缓存，进程内allocated/reserved区分与未来峰值未知；不叠加GPU1测试，不凭低余量即认定OOM，也不承诺全程可行。server4 GPU0未额外探测，其占用未知。
- 仅按ID读取4个被目标/队列变化唤醒的辅助候选，核验最新10.034588748G特例只绑定当前HDS实现，未解除任何辅助方向冻结。保留各自human_authorization、原retry/unblock条件、科学门槛、负证据和实现修订；没有重跑旧诊断、恢复M201或修改方向。
- 当前M202-HDS准入收据v2与goal/commit/revision2仍通过哈希校验。本轮记录一个训练连续性与权限核验事实文件，绑定到原稳定候选；新增候选、准入、模型修订和实验启动均为0。容量空槽不等于新增训练许可，不复制正在运行的实验或制造占位变体。
- 按external_resource_blocked收尾仅指剩余4个真实human scope holds，不是GPU阻塞、路线穷尽或新的无信息增益科学结论。下一动作是沿原冻结方案观察HDS验证结果；辅助候选只在明确方向授权或由主线新证据提出必要匹配测试时续做。执行状态以实际finish为准；收据窗口/产出在最终读取，缓存不重复相加，不作账单。

## 5. Decisions Made
- 无新的研究路线、资源配置或科学门槛决策；沿用当前用户授权，保持M202-HDS训练和四条辅助scope hold。
- 没有需要用户处理的新故障或新的验证结果时按静默heartbeat契约收尾；完整六段事实报告保存在本轮summary中，不为日常训练步数增长重复通知。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
