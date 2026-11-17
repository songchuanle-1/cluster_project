# Research Pipeline Report - cluster_project
快照时间：2026-10-15T13:12:25.693487+00:00；生成报告时快照年龄：496 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-15 21:12:25
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
================================================== 2026-10-15 21:12 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  无训练进程

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| 无 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 快照内无运行任务 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 0（运行 0 / 认领 0 / 等待 0）；目标 1；准入预算 1。
- 研究储备 5 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 100：blocked=5 / rejected=91 / complete=4。
- 否决范围：unclassified=91；实现修订累计 0；收据文件 5（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- 快照2026-10-15T13:12:25.693487+00:00，design；running/claiming/waiting均0，容量1、准入预算1；储备5/目标2/准备预算0。begin的监控/目标检查各一次。归属已核实，旧后台Disabled，目标20约束/11禁令与唯一server-4 GPU0授权不变。
- 主线到期资源实测：2026-10-15T21:16:08.049667+08:00 total32607/used23415/free8687MiB/util42%; PID2634704 uses20016MiB; PID3507231 uses3300MiB。固定主机dl04-MS-7E06及GPU UUID一致；原训练锁持有，另两诊断锁取得后释放。无其他NVML上下文、至少30000MiB及原三锁全部取得三项守卫均false，未执行GPU捕获或触碰现有进程。
- 按ID及分页核对全部5个due候选。四个旧监督候选仍为human_authorization/auxiliary_scope_hold；当前goal仍明确点云特征更新优先，没有新的用户恢复授权或已证实的机制匹配辅助需求。仅追加授权核验绑定并将fallback设为四小时；历史科学门槛、失败证据、恢复条件和next_action原样保留，尤其不清除BPS历史通过项。
- 同一主线追加4条真实资源证据，primary六项准入仍false，科学状态blocked/inconclusive。CPU源码/固定TRAIN输入/严格checkpoint装载及构造对照前轮已完成，未重复；实际学习特征的层级互补/冗余、任务伤害、独立新颖性及训练收益仍未知。
- 其余95条记录不变；本轮新增候选/变体/准入/GPU分配/原生forward/backward/训练/优化器步数均0。5个既有记录的资源或授权核验更新不代表5个科学进展。执行状态待finish及实际释放核验。
- 收据仅为begin至receipt之间可见的本地部分用量，缺失记未知；缓存已包含于输入、推理已包含于输出，不重复相加或作账单。产出为一次到期资源测试与四项范围核验，不是新性能结果。

## 5. Decisions Made
- 按真实external_resource_blocked收尾，不等到截止凑时长、不降独占/显存/科学准入门槛、不为填槽制造监督或归一化变体，也不恢复M201。历史M95仍0.5020，目标0.5100，本轮无新增性能结果。
- 主线资源fallback为2026-10-15T22:16:08.049667+08:00，辅助授权fallback为2026-10-16T01:20:20.725856+08:00；新鲜资源/目标/授权证据可提前唤醒，但定时到期不能解除范围暂停。原生特征捕获仍须原始身份/显存/NVML/三锁全部通过。上述为候选条件，不是保存的自动化触发时间，准确下轮调度未知。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
