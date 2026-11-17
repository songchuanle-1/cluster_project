# Research Pipeline Report - cluster_project
快照时间：2026-10-13T18:09:42.565182+00:00；生成报告时快照年龄：3604 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-14 02:09:42
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
================================================== 2026-10-14 02:09 : cluster_project ==================================================

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
- 科学状态validation：本轮先续做3个来源候选的AST信息流检查，再新建1个BETWEEN诊断候选。3次远端CPU诊断、3次GPU原生诊断，24组完成读数，去重8组32表达；无优化器步、新模型、准入或训练。
- 全TRAIN36665表达：literal BETWEEN2157、root BETWEEN1511、双直接节点675。初始宽松节点枚举混入非BETWEEN节点，归属已撤回；typed样本另行冻结，不用缺失类别或未知身份当作负证据。
- typed物理控制100个不同ID候选对：80正间隙、20重叠未知；5组连续读数分离、3组成员状态分离。对照通过不表示真实参照物已标注。
- 中心间隙原型8组全部零损失/零query梯度。支持质量分布原型4组梯度有限非零，6条可解释GT自损失0；2条事件不可用。362个原始参数张量在4组非零有限，同次捕获重复最大差0；不替代独立模型或历史全forward严格失败。
- 已核对原始NS3D/EDA并归档原文哈希；三元关系/文本解耦不是创新声明。与碎片化参照、非参照物配对和GT径向形状控制的原生梯度不同，仍不证明训练收益或整体新颖性。
- 最新资源核验本地2026-10-14T03:09:46.579642+08:00，远端时钟单列：2026-10-13T19:13:11+00:00 GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a, 943, 80137, 81559, 0 262355, python, 928; 退出0。峰值allocator3684.29MiB/reserved3974，不是独占效率或进程峰值。
- 执行状态以finish/abort及租约释放验证为准，本报告尚未postflight。收据尚未生成，用量窗口/统计未知；收尾后只在任务内补充，不重复相加缓存，不当账单。

## 5. Decisions Made
- 保留旧严格双锚路线拒绝状态及3条来源角色假设；新候选保持validation，六项准入未完整通过，不填槽训练。
- 下一步实现独立包/config与完整元数据覆盖，再做原生完整重复、匹配控制和统一效率；不能把本轮原始checkpoint参数读数直接当作候选准入。
- 真实截止未修改。当前接近截止时保留具体可执行下一步，不伪造资源阻塞/全局穷尽/无信息增益冷却。不操作其他项目或调度，下一计划时间未知。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
