# Research Pipeline Report - cluster_project
快照时间：2026-10-10T05:09:11.401410+00:00；生成报告时快照年龄：0 秒；模式：steady

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-10 13:09:10
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
================================================== 2026-10-10 13:08 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-6 (100.64.3.28) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pdc] Best=0.4897 12/50 no_improve=0/10 gpu=7 ? 序列: 0.4621, 0.4738, 0.4764, 0.4754, 0.4897
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bei] Best=0.4644 11/50 no_improve=0/10 gpu=7 ? 序列: 0.4255, 0.4538, 0.4571, 0.4614, 0.4644

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4 running=2
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M198-PDC | configs/Quard/pdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pdc.yaml | server-6 | 7 | 未知 | 未知 | 未知 | 未知 | 未知 | running |
| M199-BEI | configs/Quard/bei/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bei.yaml | server-6 | 7 | 未知 | 未知 | 未知 | 未知 | 未知 | running |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 2（运行 2 / 认领 0 / 等待 0）；目标 2；准入预算 0。

## 4. This Tick's Actions
- begin 已执行监控和目标检查；此表基于该快照，不代表 tick 结束时的实时状态。
- 本报告尚未执行 postflight，结果以 finish 命令及收据为准。
- 无新增可处理事件；直接生成报告，不重复设计或改写未变记忆。

## 5. Decisions Made
- 本轮无新决策。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
