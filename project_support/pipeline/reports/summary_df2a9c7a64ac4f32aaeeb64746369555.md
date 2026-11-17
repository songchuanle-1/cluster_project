# Research Pipeline Report - cluster_project
快照时间：2026-10-12T17:09:04.233414+00:00；生成报告时快照年龄：1173 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-13 01:09:03
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
================================================== 2026-10-13 01:08 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-6 (100.64.3.28) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr] Best=0.4953 19/50 no_improve=5/10 gpu=7 ? 序列: 0.4878, 0.4909, 0.4858, 0.4859, 0.4889

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4 running=1
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M200-TMR | configs/Quard/ctf_hcg_csort_tmr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr.yaml | server-6 | 7 | 未知 | 未知 | 未知 | 未知 | 未知 | running |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 2；准入预算 1。

## 4. This Tick's Actions
- 本轮为 design；快照北京时间2026-10-13 01:09:04，原截止02:09:04未修改。实际任务归属已核实，取得租约后先登记稳定诊断候选；begin 的监控与目标检查仅执行一次。
- 原生CPU全量扫描36,665条TRAIN表达/562场景/7,875目标：未映射10,115条的物理类别全部未知；本假设可检验的已知类别遗漏为0。原生词循环有词/无词对照可区分。选中0，因此第一项原生配对getter没有运行；空列表exact_repeat不是重复性PASS。
- 独立短分组测试：原生9,372组保留全部36,665条表达，无遗漏/重复/跨场景/顺序变化。预测盲选8组20条表达，原生getter及8次正序/逆序collate两轮seed1999一致，错配0；6次短分组均检出故意固定4条的错误对照。
- 两次远程CPU诊断均退出0，证据哈希已保存；只否决所测前提，未验证训练收益、全模型前后向、资源或新方法独立性。本轮新增准入0、训练启动0；M200自然训练，生产脏文件、旧FAIL、目标、白名单和调度均未改变。
- 本报告生成时尚未postflight，执行状态待finish/abort及锁释放核实；最终答复会补充实际执行结果、收据窗口及实际产出。远程观测与本地核实时间分开记录，用量缺失标未知，不当账单。

## 5. Decisions Made
- m95-native-physical-context-coverage只否决未映射子集中存在已知物理类别的词面排除前提；未知类别不是已证正确，也不是可直接改标签的依据。
- m95-native-short-group-loss-input只否决原生分组/collate至loss输入的遗漏错配前提，不认证下游FPS/decoder/完整backward。
- 两项独立前提重复测试无新增信息，采用有证据的局部no_information_gain冷却，保留空槽，不造重复变体。03:00仅是研究重试资格，下一次实际调度未知；新物理类别/输入错配/独立结构/队列目标变化可提前唤醒。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
