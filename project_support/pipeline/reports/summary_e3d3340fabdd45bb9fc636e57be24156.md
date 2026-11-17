# Research Pipeline Report - cluster_project
快照时间：2026-10-09T02:04:09.536488+00:00；生成报告时快照年龄：2865 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-09 10:04:08
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
================================================== 2026-10-09 10:03 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.194) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-4 (192.168.1.115) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-6 (100.64.3.28) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pdc] 1/50 尚无验证 - gpu=7

--- 队列: cluster_project ---
  server-4: done_earlystop=24 withdrawn=6
  server-6: done_earlystop=4 running=1
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M198-PDC | configs/Quard/pdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pdc.yaml | server-6 | 7 | 未知 | 未知 | 未知 | 未知 | 未知 | running |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 1（运行 1 / 认领 0 / 等待 0）；目标 2；准入预算 1。

## 4. This Tick's Actions
- 执行状态：研究与准入动作已执行，尚未运行本轮 postflight；只有 finish 成功且匹配租约释放后才称 COMPLETED。科学状态：M199-BEI training，收益未知；caption-window 候选 rejected。
- 固定 TRAIN 32场景/128表达，123个表达有原生目标切边，789/74768表达边；保留 XOR 方向歧义与不确定零梯度的负证据。同一稳定ID改为预注册定向事件 softplus(-(y_i-y_j)*(z_i-z_j))，不新增参数、推理图或查询选择。
- M199 算子 gradcheck/方向/置换/空集no-op通过；原生独立组及真实batch2反向、重复、端点placebo和bypass通过。首个原生重复2.2888e-5 FAIL保留；候选内归约修复后完整mask/loss重复差异0，严格门槛仍1e-6。
- baseline/champion/BEI同一原始VAL样本predict，bs1/warmup20/repeat100：9.700876364/9.762532428/9.762532428G；BEI相对champion新增参数0，显存+3.36%，median+14.264ms；相对baseline显存+2.89%，median+106.968ms。共享GPU延迟不是独占测速结论；fvcore未支持算子沿用历史同口径，训练资源收益尚未知。
- 独立文本候选真实CPU诊断：36665/36665原生TRAIN字幕被完整保留，实际tokenizer无截断；20条超过78，最大137，超过256为0。拒绝该具体截断假说，不泛化成所有文本机制失败。
- motivation_review、exp_design、18约束/11禁项逐项审查、正式next_batch日志和6项真实证据收据完成。仅提交测试过的BEI物理model/config/诊断脚本；本次10个远端测试文件核hash后归档保存，ff-only同步85d47eb4526ae635ffdcc5789bf99ee5411e8cb7，不改其他文件。
- 预检之后的新状态：M199于2026-10-09 10:46:30+08:00由现有gated dispatcher启动；10:47:52+08:00捕获PID630864原生epoch1步42->45，M198 PID225589步2801->2804，均launch_verified=true。GPU7只含这两个匹配进程，98%，27829/81559MiB；远端GPU时钟与本地相差约3分19秒，未强行对齐。活跃2/容量2，等待0。
- 收据用量仅begin至receipt本地日志窗口，早期读取/晚到记录/最终回复不含；具体数值在finish后读取，当前未知。缓存属于输入，不重复加总，不视为账单。实际研究产出为2个新稳定候选、1个拒绝、1个准入并验证启动；停止于准入目标达成。
- 首次finish发现8个历史拒绝候选仍引用地址更新前SERVERS.yaml哈希，租约保留。仅逆转已记录的.137->.115文本变更即精确复现旧SHA256 4da92203...，将原字节归档并迁移这8个旧引用；哈希、科学阶段和结论不变，当前SERVERS.yaml/资源授权不改，不访问server4。历史引用修复不计为新科学进展。

## 5. Decisions Made
- 仅准入1个 M199-BEI（m95-native-mask-boundary-incidence）；全部实际门槛与稳定ID证据绑定，训练改善和完整新颖性未知，原生NLL/seed1999/epochs50/max_iters70不变。
- 拒绝 m95-native-caption-window-loss 的实际截断假说；保留全量原生诊断，不制造文本变体，不修改现有caption协议。
- 两个授权槽位已占用，停止本轮设计；不宣称路线穷尽，不凑后继变体，不改调度。server4新IP192.168.1.115仍禁用/白名单空；Windows后台仍Disabled。
- 继续监控M198和M199自然训练；按冻结ScanRefer VAL总体、切边/无切边、同类对象子集及场景不确定性评价。噪声下限未知，数据不足记inconclusive；保留显存+15%需训练mIoU+.003及既有收敛停止规则。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
