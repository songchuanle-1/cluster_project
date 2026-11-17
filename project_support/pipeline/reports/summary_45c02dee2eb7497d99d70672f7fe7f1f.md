# Research Pipeline Report - cluster_project
快照时间：2026-10-02T06:42:46.694870+00:00；生成报告时快照年龄：2930 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-02 14:42:45
================================================================================
  Target: cluster: 面向 ScanRefer 三维语言定位的具体错误，研究有核心新颖性、可推导且可证伪的轻量结构机制，目标 mIoU ≥ 0.51。多尺度 cluster context 是已有研究基础，不再把变更 pooling、selector、回写位置或变体数量当作研究主线。先诊断候选覆盖与边界、同类目标辨别与关系绑定、多尺度证据重复等问题，再依据证据选择一个核心机制；覆盖机制对照、泛化稳健性和效率验证。共享参照物一致性仅为待验证候选，不预设为最终方向。既有 context/routing 结果是历史证据，不等于新机制已获验证。

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
| server-6 | 7 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-02 14:42 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.137) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-6 (100.64.3.28) ---
  无训练进程

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
- 活跃 0（运行 0 / 认领 0 / 等待 0）；目标 2；准入预算 2。

## 4. This Tick's Actions
- 本轮design租约45c02dee2eb7497d99d70672f7fe7f1f，begin快照2026-10-02 14:42:46北京时间，deadline15:42:46；后台保持Disabled。
- 只在server-6 GPU7执行：首次安全检查因外部进程出现退出，未启动Python、未驱逐任务；外部进程自然退出后复查并取得flock。
- 完成三组原生诊断，各两次重复：31表达/2场景任务Jacobian；121对不同物理目标联合占用；102表达/28场景扩展Jacobian，保留原生loader伴随表达。
- 扩展Jacobian：referent/semantic余弦0.57143，mask/referent0.00634；总query梯度受损referent0/102、mask1/102。重建误差最大3.73e-9；旧M95诊断不是新模型后向。
- 联合占用与独立BCE对121/121对同向纠正，梯度余弦0.99738，目标共占用2/121；普通categorical实现无新纠正信息。
- 严格1e-6数值重复性FAIL保留：31表达最大3.42e-6；扩展1.89e-5；ownership6.15e-6。输入绑定及离散结果一致，方向重复102/102及121/121，未放宽门槛。
- 新增契约测试14项通过（本地6/server6 CPU8）；脚本定向传到server6，未提交或同步训练模型。新准入0/入队0/训练0；资源、新独立包、候选原生后向均未完成。
- 15:21北京时间确认诊断结束、GPU7利用率0%、显存0MiB、flock释放；0-3事实表为begin快照，后续变化以本段实测时间为准。
- 报告生成时postflight未执行，以finish及收据为准；产出是两路线三捕获及哈希分析，不是训练收益。用量窗口及数量在finish后补述，缺失记未知。

## 5. Decisions Made
- 20261002-152303_route_change：拒绝本轮普遍任务冲突实现，不准入PCGrad/权重改写；保留严格重复性FAIL。
- 20261002-152303_other：拒绝普通categorical ownership实现，不冒充创新、不入队；不否决未来有独立信息路径的联合结构。
- 按两条独立路线实际反证no_information_gain冷却至2026-10-02 17:25北京时间；新独立证据或到期触发重评，监控/目标照常，不宣称全部方向穷尽。
- M197-PIRS仍stopped_unknown，不自动重启；不改goal/banned/GPU分配，不操作其他项目或调度。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
