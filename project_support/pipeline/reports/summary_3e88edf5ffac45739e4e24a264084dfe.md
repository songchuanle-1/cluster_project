# Research Pipeline Report - cluster_project
快照时间：2026-10-11T21:09:11.501923+00:00；生成报告时快照年龄：827 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-12 05:09:10
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
================================================== 2026-10-12 05:09 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
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
- 本轮快照2026-10-12 05:09:11+08:00，design/bootstrap required；原始截止06:09:11+08:00未更改，begin已监控/核对目标一次，无重复preflight。
- 先登记m95-native-scale-target-distractor-alias，再执行固定M95/seed1999/32场景128表达两次原生遍历：68表达26场景有同类干扰物，全尺度支持完全重合0；分尺度相等0/2/16。29条原生类别缺失、31条无同类干扰物，不能视为负例。自身份对照68/68相等，55条有不同远端干扰物对照。
- 首项输入与配对读数重复一致，但4条层级ID重复漂移；整体logit最大差1.2636e-5、mask1.2398e-4仍FAIL，保留绝对1e-6门槛，不把离散读数稳定当成完整模型重复PASS。
- 独立登记m95-native-support-faithful-csort并捕获128表达、256尺度对：原稀疏对应9216边/40960细支持，有12边不在实际父簇；真实支持平均与原生粗特征最大差1.6689e-6原样记录。仅替换为真实支持后，耦合损失近似恒1、最大梯度5.2042e-18；原对应/父簇旋转对照256/256分离且有非零梯度，算子重复差0。
- 两项均只淘汰测试过的具体解释，科学状态rejected；无新模型/config、optimizer、准入、训练或mIoU增益。脱离原生特征的float64算子梯度不冒充完整新模型backward。
- 诊断只在授权server-6 GPU7运行，每次取得独占锁并实时核验UUID/占用；远端审计2026-10-11T21:22:12.686062Z、本地核验05:20:06+08分别保留，时钟不对齐。GPU7审计时0%/0MiB、无计算进程，诊断锁可取得；两份结果和源码本地/远端SHA一致，既有用户Git修改未动。
- 按closure的no_information_gain对重复这两条已反证方案短期冷却，retry_after07:25+08；这不是本轮没有科学信息、全局路线穷尽、假资源阻塞或永久暂停。执行状态待finish，只有明确postflight PASS/COMPLETE并核实租约消失才称完成；收据用量及实际产出在收尾后说明。

## 5. Decisions Made
- 实际route_change已记录为pipeline/decisions/20261012-052216_route_change.md，证据引用覆盖两项原生测试、六段动机审查及哈希核验。
- 不为填满两个槽位把全尺度重合不存在或恒定自比较损失包装为训练实验；两条稳定ID的反证、缺失数据和限定恢复条件已保存。
- 保留局部粗尺度重复及原生数值重复FAIL作为未解决问题；Champion0.5020、目标0.5100、18约束11禁令和server4禁派保持不变。
- 下一定时触发时间未知；07:25为证据冷却到期条件，不是承诺启动时间。新队列/研究证据或有依据的独立因果机制可提前唤醒。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
