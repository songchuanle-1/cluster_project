# Research Pipeline Report - cluster_project
快照时间：2026-10-16T16:13:54.499367+00:00；生成报告时快照年龄：1679 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-17 00:13:53
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
================================================== 2026-10-17 00:13 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  无训练进程
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1] 进程未见 (deathwatch 2/3) — 暂不处置

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
- 否决范围：unclassified=91；实现修订累计 2；收据文件 8（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 实际后续观测时间 2026-10-17T00:40:40.590502+08:00（上海时间）。初始0-3段仅为begin快照；本段记录之后发生的变化。
- 实证归档原PID216566已退出、TypeError异常及第8/50轮2998/4686步；原始日志10,070,812字节和epoch7 last.pth均有SHA256，标准finalizer已纠正旧running映射，所有失败保留。
- 冻结模型/config、tools/train.py及cuda_cast未修改。实际gorilla.resume恢复epoch7/best0.47346487641334534/patience0；1163当前模型state项、642优化器state及调度器逐项精确匹配，两个原生provider已知额外非持久text buffer仍按原strict=False协议处理。
- 一次有正式结果的恢复测试：48次原样model.cuda，参数对象身份保留；固定TRAIN两组/四场景/16表达的loss与backward通过，24个点云路径参数梯度均有限非零；优化器step为0。仅恢复可执行性，不证明TypeError根因、长期稳定性或精度收益。
- 经标准门控dispatcher对同一M202执行1次原生--resume。实际PID1592337/server4物理GPU0；第8/50轮步数 278→284/4686已增长，正确UUID和原始三把生命周期flock保持，无新异常。epoch8从头接续，不冒充丢失的中间batch/RNG精确重放。
- 本轮产出：1个通过的检查点恢复诊断、1次同实验续训与进度核验、4项到期human scope hold复核；新增模型/候选/结构修订/验证轮次均为0。第一次诊断结果序列化失败及前置UTF-8问题保留，不计科学反证或修订。
- 科学状态：当前M202最佳0.4735仍低于baseline0.4894/champion0.5020，目标0.5100；没有本轮新增验证结果。历史故障根因、全程峰值显存、场景配对置信区间和最终效果仍未知。
- 收据用量仅覆盖本轮begin至receipt本地日志窗口，缺失/此刻最终值记未知，最终原始记录见收据；cache已含在input、reasoning已含在output，不重复相加，不是账单。

## 5. Decisions Made
- 保持同一稳定主线ID/M202、恰好2次已通过实现修订、原seed1999/batch2/workers4/50epochs/max_iters70、验证边界和精确源码FLOPs例外；没有扩大授权、改调度或恢复M201。
- 不将本次原样恢复称为修复根因。若TypeError再次出现，保留新现场并调查，不盲目重启或绕过精确源码/修订限制；当前无需用户增加授权。
- 余下4个辅助候选仍受human_authorization主线优先级hold；本轮外部阻塞收尾只指这些真实scope holds，不声称GPU耗尽或独立路线已穷尽。当前主线已确认训练，储备4/2、预算0，不凑新变体。
- 完整六段报告与七段记忆在租约内保存；本段写入时postflight尚未运行，只有随后finish成功且核实匹配租约不存在，才能称本轮执行完成。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
