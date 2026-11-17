# Research Pipeline Report - cluster_project
快照时间：2026-10-20T21:20:07.870596+00:00；生成报告时快照年龄：546 秒；模式：design

## 0. Goal Status
- 目标：mIoU / 0.51；数据集：ScanRefer
- 目标检查返回码：0
- Champion / Gap / Phase：以下为本轮目标检查原始结果，缺项为未知。
```text
================================================================================
  Goal Check Report — 2026-10-21 05:20:07
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
| server-4 | 1 | 未知 | 未知 | 未知 |
- 可用 GPU：未做实时占用确认，不能据此分配。
- 监控摘要（begin 已执行，不再重复探测）：
```text
================================================== 2026-10-21 05:20 : cluster_project ==================================================

--- local (192.168.1.175) ---
  无训练进程

--- server-2 (192.168.1.163) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- server-3 (192.168.1.120) ---
  无训练进程

--- server-4 (192.168.1.115) ---
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc] 1/50 尚无验证 - gpu=0
  [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca] 1/50 尚无验证 - gpu=1

--- server-6 (100.64.3.28) ---
  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机

--- 队列: cluster_project ---
  server-4: done_earlystop=24 running=2 withdrawn=6
  server-6: done_earlystop=4
  server-3:
```

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|---|---|---|---|---|---|---|---|---|---|
| M205-MDC | configs/Quard/ctf_hcg_csort_mdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc.yaml | server-4 | 0 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |
| M206-CGCA | configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml | server-4 | 1 | 未知 | 未知 | 未知 | 未知 | 未知 | 登记运行；实时进度须核实 |

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|---|---|---|---|---|---|
| 未知 | 无 | 未知 | 无排队 | 未知 | 未知 |
- 活跃 2（运行 2 / 认领 0 / 等待 0）；目标 5；准入预算 2。
- 研究储备 0 / 3；储备准备预算 2，不增加训练并发或启动授权。
- 储备只计可推进候选及已排队项；另有待人工 4、待资源 0、数值诊断待解 4、未分类阻塞 0。
- 非终态候选与排队项合计 0；总上限 4。阻塞不授权重开旧路线；其他合法独立工作按剩余预算推进。
- 候选累计记录 132：complete=28 / rejected=94 / blocked=8 / training=2。
- 否决范围：unclassified=91 / hypothesis=3；实现修订累计 12；收据文件 12（含修订或重试，不代表成功率）。
- 待人工确认（列出动作不代表已授权）：
| ID | Required Confirmation | Retry After |
|---|---|---|
| m95-native-relation-other-sign-conflict | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-main-role-weight-precedence | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-secondary-positive-mass | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |
| m95-native-between-pair-support | Preserve original evidence, failures and historical gates. Do not resume/promote this supervision route or recover M201 merely because retry is due/GPU opens. Resume the primary point-feature-path diagnosis first. | 2026-10-20T00:38:18.296045+00:00 |

## 4. This Tick's Actions
- 先完成项目归属、最新版experiment_first授权和Disabled后台调度核验；canonical begin监控显示M205/M206均在server4运行，无新终态/故障/验证结果，waiting0。没有重启、迁移、暂停或占用现有训练卡。
- 按快照准备一个独立储备M207-HAP：用已更新parent截距加几何子空间中的原child变化，coarse→middle→fine；新增0参数，保留原三层FFN/CSORT/HCG/inst_feats路径。occupied由真实点逐层传播，几何detached、特征RHS与detail保留梯度，不构造N²矩阵。
- 独立八份模型源码和一份原生YAML已本地保存版本f51823bb；Python3.10语法/compile不exec、相对导入、配置数值与M95一致、champion源码哈希未变均通过；独立只读源码审查未发现确定接口/梯度连接阻断。未执行本地torch、合成行为或原生数据训练。
- 原生最小训练检查和全部资源指标尚未执行。05:26:39上海时间新鲜UUID/CUDA上下文核验确认server4两卡仍被M205/M206占用；锁文件可用不能抵消活跃CUDA上下文，因此HAP保留validation/native_pending_resource，不生成收据、推送、入队或启动。明确原生2步/输入输出梯度/pinv谱秩有限性/同口径资源协议，待真实空卡续做。
- 截至05:27:26上海时间，M205为第1/50轮2982/4686步，M206为第1/50轮1395/4686步，原生日志均持续增长。尚无新验证mIoU；本轮新增1静态准备候选，0准入/0排队/0启动。

## 5. Decisions Made
- 沿用新版流程，旧8项挂起与所有失败/修订上限保留，不以它们阻止独立准备，也不以静态检查代替工程准入。HAP与已核CCP残差/GEO位置投影并非同一计算图，但新颖性和任务收益未知。
- 显式保留HAP退化与风险：单child或零几何差异只有parent；至多4个独立子中心可能仅替换组均值；不宣称所有组几何低秩平滑或pointmass守恒。FP32 normal equations条件数平方、pinv unsupported及小矩阵延迟均须实测，不添加ridge/改精度/调数值来绕过失败。
- 无需用户新增常规授权；待已授权server4卡真正空闲后，先复核精确版本/原生YAML与资产，再执行真实TRAIN至少2步和配对资源检查，通过才准入派发。现有训练按原数据、seed1999、50epochs/maxiters70和patience继续；无全局冷却或耗尽声明。

Next tick: 以已保存自动化为准；本脚本未读取调度时间。
