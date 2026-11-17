# Research Pipeline Report - cluster_project
快照时间：2026-10-15T08:10:12.609019+00:00；生成报告时快照年龄：2331 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-15 16:10:12
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
================================================== 2026-10-15 16:10 : cluster_project ==================================================

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
- 研究储备 4 / 2；储备准备预算 0，不增加训练并发或启动授权。
- 候选累计记录 99：rejected=91 / complete=4 / blocked=4。
- 否决范围：unclassified=91；实现修订累计 0；收据文件 5（含修订或重试，不代表成功率）。

## 4. This Tick's Actions
- cluster_project；快照2026-10-15T08:10:12.609019Z，design。依最新用户主线先登记稳定候选并完成12项源码断言；CTF为分尺度FFN、HCG为层级广播/融合，不把已有骨架说成新层间注意力。
- 原模块构造CPU样本：padding有效特征delta0.093810439、固定query logits delta0.043136418。两次严格跨形状控制FAIL保留；后续同形状4项路径控制通过，不能替代旧FAIL或当作真实TRAIN特征伤害。
- 实际原生CPU取样4群组/4场景/16表达式，两次重复一致；8次getitem/32表达式出现不是32独立样本。预注册两对超点长度667/2329和406/1441支持padding触发条件，未捕获学习特征。
- 16:36+08核验M95冻结checkpoint fe5e4a5f...与配置a18f2c6f...；原生适配器CPU构造和严格装载847参数tensor、两项序列化缓冲区通过，CUDA未初始化，网络forward/backward均未执行。
- 后快照资源16:24:50+08：server-4 GPU0 free11994MiB，NVML2634704占20016MiB，原训练flock held；另两诊断锁可得。未达既有30000MiB/无其他NVML/原flock守卫，未分配GPU。
- 4个旧监督候选仅转辅助范围暂停，保留原状态、证据、失败和历史门槛，不因到期/空槽恢复M201。新主线候选六门槛均未通过；新增候选1，准入/训练/科学否决/GPU测试/优化器步数均0。
- 执行状态待finish/收据核验；科学状态blocked/inconclusive。用量仅begin到收据可见本地窗口，不含先前读取、延迟记录和最终回复；缺失未知，缓存含于输入而非重复相加，不是账单。

## 5. Decisions Made
- 按已授权主线继续同一m95-hierarchical-mask-feature-path-audit；原生捕获协议和CPU准备已完成，下一步在新租约下重新核实资源后捕获真实M95特征，再决定结构机制。
- 以真实资源证据作external_resource_blocked收尾，不宣称路线穷尽；主要候选一小时后可重查，旧监督范围暂停仅在新授权或主线匹配对照需求下解除。未改目标/调度/队列/训练代码或准入标准。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
