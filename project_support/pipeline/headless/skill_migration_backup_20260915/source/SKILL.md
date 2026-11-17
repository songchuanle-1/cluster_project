---
name: songcl_research_pipeline
description: Multi-project research iteration pipeline — Windows Task Scheduler triggers unified Codex ticks for monitoring, early-stop, GPU queue execution, autonomous experiment design, and crash self-repair.
---

# songcl_research_pipeline

## Executable Closure (2026-09-15)

Projects opting in through `pipeline/closure_policy.json` use
`references/closure.md`: persistent candidate stages, hashed admission receipts,
safe ff-only synchronization, candidate-only YAML adaptation, native training
progress checks and postflight validation. `pipeline/research_work.json` pending
actions resume in event mode without waiting for a new design cycle.
Existing running experiments are not retroactively gated. Other projects keep
their existing deployment behavior until explicitly enabled.
Reconcile-only success does not clear an unsuccessful research tick.
Tests: `python -m unittest test_closure test_tick_context` from this skill directory.

研究迭代流水线，跨平台支持 Linux（`/home/songcl/3dres/project/`）和 Windows（`D:/project`）。

> 链条定位：`songcl_research_bootstrap`(0→1 调研/复现/首批实验) → `songcl_deploy_project`(接入平台) → **本 skill**(1→N 自动迭代闭环)。全新任务从 bootstrap 进入，移交前用其 `bootstrap_check.sh` 验收。

## 文件地图（按需加载，不要一次全读）

| 文件 | 内容 | 什么时候读 |
|---|---|---|
| 本文件 | 触发规则、核心脚本、queue/goal schema、硬性规则、跨平台差异 | 总是 |
| `references/formats.md` | 全部 7 套文档模板（tick 报告/终态分析/实验设计/动机审查/消融方案/决策/bugfix） | 生成任何 pipeline 文档前 |
| `references/autonomous_design.md` | 自主实验设计 Phase 0-4、crash 自修复、Phase 2 消融流程、决策日志示例 | 队列深度不足 / champion 达标时 |
| `references/manual_ops.md` | 手动干预话术表、循环衔接行为、研究路线调整、模式切换 | 用户前台提出 kill/改队列/换方向等要求时 |

## 触发规则 — Windows Task Scheduler 统一调度（2026-08-12 起）

**一个 tick 完成全部**：Task Scheduler 每小时触发 `tick_full.bat <project>` →
`headless_tick_local.sh`。入口先确定性执行监控、早停、GPU 队列推送和目标检查，
再生成 compact context。无变化的 `steady` tick 直接生成报告，不调用模型；
只有 `event/design` tick 才调用 `codex exec` 完成终态分析、研究设计和 crash
自修复。与 Linux crontab 行为等价。

**用户必须指明项目名**（如"启动 cluster 流水线"）。只说"启动流水线"不指明项目 → 反问"哪个项目？"

**启动**（用户说"启动流水线"时直接执行）:
1. `schtasks /query` 检查是否已有 `Pipeline-<project>` 任务
   - **有** → 告知现有调度，不重复添加
   - **无** → `schtasks /create` 新建。分钟位错峰（首个 :07，后续 +20），`/sc HOURLY`
2. 汇总: 任务名 + 分钟位 + 日志位置 `<project>/pipeline/headless/tick_*.log`

**停止**: `schtasks /delete /tn Pipeline-<project> /f`

**查看**: `schtasks /query /tn Pipeline-<project>`，或直接看日志 `<project>/pipeline/headless/tick_*.log`

- 调度跑在**本机 Windows Task Scheduler**（系统级，关机不影响，开机自动恢复）
- `codex exec` 是独立进程，不依赖交互会话
- 默认决策模型为 `gpt-6-astra`；可通过 `CODEX_PIPELINE_MODEL` 覆盖
- 默认模型不可用时自动降级到 `deepseek-flash`（DeepSeek V4.1 Flash）；可通过 `CODEX_FALLBACK_MODEL` 覆盖，设为空字符串即禁用降级
- 定时 tick 默认每轮使用新的 Codex 线程（`CODEX_FRESH_THREAD=1`），避免长会话上下文无限增长；研究状态由项目文件与 `codex_memory.md` 跨轮传递
- 三个项目会话保留为状态通知入口，不再承载每小时的完整研究 tick
- 关键研究状态同时写入 `<project>/pipeline/codex_memory.md`；项目文件始终高于线程记忆
- **不要**扫描 SERVERS.yaml 自动给所有项目建调度 — 只建用户明确提到的项目

### 跨平台路径

所有脚本通过 `PROJECT_ROOT` 环境变量适配，Windows: `D:/project`，Linux: `/home/songcl/3dres/project`。`tick_full.bat` 自动设置。

### GPU 资源分配（无冲突）

| 项目 | 服务器 | GPU 卡 | 容量 |
|------|--------|--------|------|
| cluster_project | server-4 [0,1], server-6 [7] | 5090×2 + H100 GPU7 | 4 |
| lighttext_project | server-2 [0,1], server-3 [0,1] | 3090×4 | 4 |
| multiview_project | server-6 [1,2] | H100 GPU1+2 | 2 |

**不要**扫描 SERVERS.yaml 自动给所有项目建调度 — 只建用户明确提到的项目。

## 项目列表

```bash
ls -d "$PROJECT_ROOT"/*/SERVERS.yaml | xargs -I{} dirname {} | xargs -I{} basename {}
# 或 Windows: dir D:\project\*\SERVERS.yaml
```

## 核心脚本

所有脚本通过 `PROJECT_ROOT` 环境变量定位项目根目录（默认 `/home/songcl/3dres/project`）。
Windows 上**必须**设置 `PROJECT_ROOT=D:/project`，且使用 `python`（非 `python3`）。

### `pipeline_monitor.py <project>` — 通用流水线监控（主引擎）

```bash
PROJECT_ROOT=D:/project python .claude/skills/songcl_research_pipeline/pipeline_monitor.py cluster_project
```

功能：
1. 从 `SERVERS.yaml` 获取所有 GPU 服务器，SSH 检查训练进程（匹配 `tools/train.py`）
2. 从日志提取 mIoU 序列，计算「连续未刷新 best」计数
3. **早停**：达到 patience 自动 kill（优先级：`--patience` > 队列任务级 `patience` > 队列全局 `patience` > 10）
4. **GPU 队列**：空闲 GPU（**util<10% 且显存<1GB** 且在白名单内）自动推送下一实验
5. **白名单**：`SERVERS.yaml` 每台 gpu_server 的 `allowed_gpus` 限定可操作卡号，白名单外进程只展示不处置
6. **终态跟踪**：队列中 running 但进程消失 → 判定 `done_complete` / `crashed` / `stopped_unknown` 写回队列
7. **终态结果分析**：自动读取 pulled log + checkpoint 指标序列，生成 `pipeline/analyses/<id>_<state>_<ts>.md`
8. **结果归档**：终态时拉取日志到 `<project>/Checkpoints/`（**checkpoint 留在远端**），追加 `pipeline/experiments.csv` 台账
9. **决策日志**：早停/队列推送自动写 `pipeline/decisions/<ts>_<type>.md` + `_index.md`
10. **并发锁**：整轮持有 `<project>/.pipeline.lock`，多会话同时监控只有一个生效，防双推
11. **Windows 兼容**：已内置 UTF-8 补丁（stdout + open()），无需额外配置

### `check_goal.py <project>` — 目标/相位判定

读 `pipeline/goal.json` + `experiments.csv` → 输出 champion、gap、Phase 1/2 状态（`PHASE1_REACHED` / `GOAL_REACHED`）。每个 tick 在自主设计前必须运行。

### `log_decision.sh` — 决策日志（所有自主决策必须记录）

```bash
PROJECT_ROOT=D:/project bash .claude/skills/songcl_research_pipeline/log_decision.sh \
  <project> <type> "<问题>" "<决策>" "<依据>" "<证据>"
```

- **type**: `early_stop` | `queue_push` | `next_batch` | `route_change` | `question` | `manual` | `manual_batch` | `other`
- 写入 `pipeline/decisions/<YYYYMMDD-HHMMSS>_<type>.md` + `_index.md`（索引表）
- `early_stop` / `queue_push` 由监控脚本**自动记录**；`next_batch` / `route_change` / `question` 由 Codex 在做研究决策时**手动调用**（要求与示例见 `references/autonomous_design.md`）
- 查看历史：`cat <project>/pipeline/decisions/_index.md`

### `tick_full.bat <project>` — Windows Task Scheduler 入口

参数化批处理，由 Task Scheduler 每小时触发。调用 `headless_tick_local.sh` → `codex exec` 完成全流程。

### `headless_tick_local.sh <project>` — 统一 tick 脚本（核心）

被 `tick_full.bat` 调用。先在 Codex 外执行一次 monitor + goal check，再由
`build_tick_context.py` 生成紧凑状态快照，最后按 `steady/event/design` 模式调用
`codex exec`。与 Linux `headless_tick.sh` 功能等价。

### `build_tick_context.py` — Token 节流与事件分层

- 输出 `<project>/pipeline/headless/.tick_context.json`
- `steady`: 无结构状态变化，只读快照和当前运行证据，不扫描历史
- `steady` 由 `render_steady_report.py` 直接生成六段报告，不启动 Codex，
  因此该轮模型 token 消耗为 0
- `event`: 只展开新增终态、crash、队列/目标/研究 gate 变化相关文件
- 新增或更新 decisions/analyses/designs/reviews/bugfixes 中的研究产物也会
  触发 `event`；每小时例行 summary 报告不作为变化源，避免自触发循环
- `design`: 队列不足且连续 2 个健康 tick 无进展，并满足深度审查冷却时间后，
  才读取有限分析清单并执行完整实验设计
- 默认深度审查冷却时间为 6 小时，可用 `CODEX_DESIGN_INTERVAL_HOURS` 覆盖
- 项目可通过 `goal.json.pipeline_policy.design_interval_hours` 覆盖全局冷却时间；
  空队列且需要持续研究的项目可设为 1 小时
- 正常 tick 禁止读取 `pipeline/headless/tick_*.log`；只在不健康恢复时使用

### `codex_tick_exec.sh` — Codex 上下文执行器

Windows 与 Linux 的 headless tick 共用该执行器：

1. 默认 `CODEX_FRESH_THREAD=0` 时，若存在 `<project>/pipeline/headless/.codex_target_thread_id`，恢复该固定 Codex App 会话
2. 默认模式下首次运行创建项目专属 Codex 线程，并将 `thread_id` 保存到
   `<project>/pipeline/headless/.codex_thread_id`
3. 后续运行通过 `codex exec resume <thread_id>` 恢复同一研究上下文
4. `tick_full.bat` 默认导出 `CODEX_FRESH_THREAD=1`，定时 tick 忽略固定会话和旧线程，每轮从项目文件创建干净线程
5. 每次 tick 先读 `.tick_context.json` 和 `<project>/pipeline/codex_memory.md`；
   只按 context manifest 定向读取项目文件。磁盘项目状态是唯一事实源
6. `event/design` 成功后替换更新 `codex_memory.md`，限制在 120 行以内；
   `steady` 且事实未变化时不重写 memory
7. 默认模式下自动创建的线程默认每 48 个 tick 轮换一次；固定目标线程不轮换
8. resume 或执行失败时不在同一 tick 自动重跑，防止重复副作用：
   自动线程清除失效 ID，下一 tick 从项目文件创建新线程；固定目标线程保留并在下一 tick 重试
   **唯一例外**：默认模型不可用（错误信息匹配模型不存在/无权限，且线程尚未启动）时，允许在同一 tick 内用 `CODEX_FALLBACK_MODEL` 重试一次

可配置环境变量：

| 变量 | 默认值 | 说明 |
|---|---:|---|
| `CODEX_PIPELINE_MODEL` | `gpt-6-astra` | 后台决策模型 |
| `CODEX_FALLBACK_MODEL` | `deepseek-flash` | 默认模型不可用时的降级模型；留空则禁用降级 |
| `CODEX_THREAD_MAX_TICKS` | `48` | 单个 Codex 线程最多承载的成功 tick 数 |
| `CODEX_FRESH_THREAD` | `0`（脚本）/ `1`（`tick_full.bat`） | 为 `1` 时忽略固定/旧线程，每轮创建干净后台线程 |
| `CODEX_DESIGN_INTERVAL_HOURS` | `6` | 队列持续不足时，两次完整研究设计审查之间的最短间隔 |
| `CODEX_FORCE_DESIGN` | `0` | 手动设为 `1` 时，只要存在容量缺口，本次 tick 立即进入 design；不跳过任何科学准入、实现或测试门槛 |

项目可在 `goal.json.pipeline_policy` 中结构化配置容量补齐策略：

```json
{
  "pipeline_policy": {
    "steady_ticks_before_design": 2,
    "design_interval_hours": 6,
    "fill_to_capacity": true,
    "design_buffer": 0,
    "max_candidates_per_design_tick": 4
  }
}
```

- 活跃任务数 = `running + claiming + waiting`
- `design_interval_hours` 是该项目两次完整研究设计审查的最短间隔，优先于
  `CODEX_DESIGN_INTERVAL_HOURS`
- 目标活跃数 = `capacity + design_buffer`
- 本轮候选预算 = `min(max_candidates_per_design_tick, max(0, 目标活跃数 - 活跃任务数))`
- 候选预算是上限和补齐目标，不降低科学准入门槛；合格候选不足时允许留空并记录原因

## 白名单配置（SERVERS.yaml）

每个项目在自己的 `SERVERS.yaml` 中为 gpu_server 声明可操作的卡号：

```yaml
servers:
  server-2:
    role: gpu_server
    allowed_gpus: []       # [] = 本项目流水线整台跳过
  server-4:
    role: gpu_server
    allowed_gpus: [0, 1]   # 只允许操作 0/1 卡；卡上白名单外进程只展示，不早停不推送
  server-6:
    role: gpu_server
    allowed_gpus: [1]              # server-6 专用卡
    max_tasks_per_gpu: 2           # H100 80GB: 单卡可同时跑 2 个任务
```

- **`max_tasks_per_gpu`（可选，默认 1）**：该服务器每张卡最多同时承载多少个本项目任务。H100 80GB 等大卡显存有富余（单任务 ~20GB），可设 >1 让单卡跑多个训练。
  - `=1`（默认）: 一卡一任务，**整卡空闲**（util<10% 且显存<1GB 且无本项目进程）才推
  - `>1`: 单卡多任务，该卡本项目任务数 < max **且** 显存余量 > 单任务需求(~20GB) 即可再推，同一 tick 可连续推满槽位
  - 现有配置：cluster server-6 GPU7 = 3，multiview server-6 GPU1 = 2
- 未写 `allowed_gpus` = 不限制（兼容旧项目）；跳板机在服务器项配 `jumphost: user@host`，SSH/scp 自动走 `-J`
- **各项目当前的白名单、主训练服务器、IP 等一律以该项目 `SERVERS.yaml` 为唯一事实源**（本文件不维护快照）；跨项目总览用 `songcl_server_status` skill
- skill 本体已纳入 git 版本控制（`.claude/` 仓库），改坏可回滚。Windows: `D:/project/.claude/`；Linux: `/home/songcl/3dres/project/.claude/`

## 项目流水线队列文件 — `pipeline/queue.json`

```json
{
  "patience": 10,
  "min_epochs": 0,
  "gpu_queues": {
    "server-4": [
      {
        "id": "B1-seed2026",
        "config": "configs/Quard/seed2026/model_base1_quard2_c2f_enc_lite_posA_l1.yaml",
        "status": "waiting",
        "patience": 15,
        "label": "B1 stability seed2026",
        "depends_on": ["other-id"]
      }
    ]
  }
}
```

字段说明：
- `gpu`（可选，不再强制）: 偏好卡号。**用队列顺序驱动**: 哪张卡先空闲就推下一个 waiting 任务。
  - **不写 `gpu`** → 任意白名单内空闲卡都接收，队列 FIFO 顺序分配
  - **写 `gpu`** → 只有该卡号空闲时才推送（强绑定，适合需要特定显存/型号的场景）
- `min_epochs`（可选，默认 0）：epoch 未达此值不触发早停，防 warmup 期误杀。
- 任务级 `patience`（可选）：覆盖全局 patience，适合收敛慢的变体。
- 任务级 `depends_on`（可选）：`["id1", "id2"]`，所列任务全部正常终结（done_complete/done_earlystop）后才允许推送，跨服务器生效。
- 任务级 `requires_exclusive_ownership`（可选，默认 `false`）：仅用于需要独占
  GPU ownership 生命周期证明的诊断任务。普通训练不得设置此字段，仍由白名单、
  GPU 空闲/显存检查、流水线锁、代码同步和启动后 PID 验证保护。
- `status` 生命周期：`waiting → claiming → running → done_complete | done_earlystop | crashed | stopped_unknown`。终态任务会带 `final_best` / `finished_at`。
- 防误归档：running 但进程消失时，若日志 10 分钟内仍在更新则跳过终态判定（可能是重启/瞬时抖动）；终态先判"正常完成"再判崩溃关键字。
- 推送成功以**远端实际出现进程**为准（等 6s 后 ps 验证），不信任 remote_train.sh 的 stdout。
- resume 进程（命令行含 `--resume`）自动聚合该 config 的全部历史日志计算 Best/no_improve，防止新日志重置早停计数；从头重跑只看最新一段日志。

不需要 `pipeline/queue.json` 时，监控器仍执行早停检查，只是不自动推送新实验。

## 研究目标与闭环终点 — `pipeline/goal.json`

闭环不是无限循环。研究分两个阶段：**先追指标，再验证故事**。

```
Phase 1: 追求指标（主阶段）
  ├─ 目标: champion mIoU ≥ target；自主实验设计全部服务于提升指标
  ├─ 不强制消融，不强制特定模块
  └─ champion 达标 → PHASE1_REACHED → 进入 Phase 2

Phase 2: 验证故事（仅在 Phase 1 达标后启动）
  ├─ 消融实验证明"每个设计选择都是必要的" + 多 seed 稳定性
  └─ 故事闭环 → GOAL_REACHED → 生成论文大纲
```

最简形式只需要 `metric.target`：

```json
{
  "metric": {"name": "mIoU", "target": 0.514, "dataset": "ScanRefer"},
  "baseline_experiment_id": "model_base1",
  "description": "cluster_project: 聚类路由机制在3D视觉语言定位任务，目标 mIoU ≥ 0.514"
}
```

| 字段 | 说明 | 必填 |
|---|---|---|
| `metric.name` | 指标名称（mIoU / Acc@50 等） | 是 |
| `metric.target` | 量化阈值。champion 超过此值 → Phase 1 达标 | 是 |
| `metric.dataset` | 评测数据集名（用于论文描述） | 否 |
| `baseline_experiment_id` | baseline 实验 ID（用于 +γ 比较和论文 Motivation） | 推荐 |
| `description` | 项目目标的一句话描述（自主设计的动机出发点） | 否 |
| `constraints` | 硬约束数组（FLOPs 上限/协议条款/判定阈值等）。设计变体前逐条校验 | 否 |
| `banned` | 禁区数组（已证伪/明令暂停的方向）。入队前逐条排除 | 否 |

- 不创建 `goal.json` = 早期自由探索模式，流水线照常运行但不自动收敛。不需要 `auto_stop` 字段。
- 每个 tick 自主设计前先跑 `check_goal.py` 判相位；**PHASE1_REACHED 后停止自主设计，出消融方案与用户讨论**（完整流程见 `references/autonomous_design.md`）。
- 用户手动标记完成 / 修改 target 的处理见 `references/manual_ops.md`。

## 文件存放规则（硬性规则）

**所有 pipeline 操作创建的文件，必须在所属项目的 `<project>/` 目录内。**

| 文件类型 | 允许路径 | 示例 |
|---|---|---|
| 项目文档/tick报告/决策/设计 | `<project>/pipeline/` | 现有结构不动 |
| 项目代码/配置 | `<project>/Cluster/` 或 `<project>/lighttext/` 等 | 代码仓 |
| 训练产物（checkpoint/日志） | `<project>/Checkpoints/` | `pl.sh pull` 的落盘位 |
| 跨项目工具/脚本 | `.claude/skills/` | `headless_tick_local.sh`、`tick_runner.bat`、`cluster_dashboard.py` 等 |
| 临时文件 | `$TMPDIR` / `%TEMP%`（确认可清理） | 编译中间产物 |

**禁止**：
- 在项目根目录直接创建文件
- 在任意路径（如 `/tmp/` 等）写入持久化产物
- 在服务器远端（server-2/3/4/5/6）的 `/tmp/` 或 `$HOME` 下创建不属于该项目的文件

跨项目管理工具（如 `cluster_dashboard.py`）归入对应的 skill 目录（`.claude/skills/songcl_server_status/`）或独立脚本目录（`<project>/scripts/`）。

## 代码同步规则（硬性规则）

**每次设计新变体或入队前，必须将最新代码推送到所有可用服务器**：

```bash
cd "$PROJECT_ROOT/<project>"     # Windows: cd D:/project/<project>
git status                      # 1. 确认本地改动已 commit
git push 2>/dev/null || true    # 2. push 到远端 git（如有）
# 3. sync 到所有 role=gpu_server 且 allowed_gpus 非空的服务器
SKILL_DIR="$PROJECT_ROOT/.claude/skills/songcl_research_pipeline"
for srv in <server-list>; do PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> sync $srv; done
```

**每次 tick 推送训练前检查本地-远端代码一致性**：已内置于 `pipeline_monitor.py` 的队列推送逻辑（对比 commit hash，不一致先 sync 再推送）。

## 统一输出格式 — Tick 报告（硬性规则）

- 每次 tick 写 `pipeline/reports/summary_<YYYYMMDD-HHMMSS>.md`；**用户前台询问状态**时现场输出同样格式并**必须同步写入** `summary_<ts>_manual.md`。
- **完整六段格式（0-5：Goal Status / GPU Overview / Running Experiments / Queue Status / This Tick's Actions / Decisions Made），禁止精简合并为单行**，模板与逐段强制检查见 `references/formats.md#1-tick-报告`。
- 删 24h 前旧 summary。

## 输出产物（每项目 `pipeline/` 目录下）

```
<project>/pipeline/
├── queue.json                          # 队列（仅 waiting 排队，FIFO，按服务器分组）
├── codex_memory.md                     # 跨 tick 持久研究记忆（线程失效时的恢复源）
├── running.json                        # 实时 running/claiming 映射 {server: {gpu: exp_id}}
├── experiments/<exp_id>.json           # 每个实验独立 JSON（全生命周期）
├── experiments.csv                     # 台账
├── decisions/                          # 决策记录
│   ├── _index.md                       #   索引表（时间/类型/问题/决策）
│   └── <YYYYMMDD-HHMMSS>_<type>.md     #   单次决策详情
├── reports/                            # 监控报告（六段格式；手动查询带 _manual 后缀）
│   └── summary_<YYYYMMDD-HHMMSS>[_manual].md
├── monitoring/<YYYY-MM-DD>.md          # 日报（仅在有事件时追加）
├── analyses/<id>_<state>_<ts>.md       # 终态结果分析（后续实验设计的数据源）
├── reviews/motivation_review_<ts>.md   # 动机审查（每次自主设计前的上游分析）
├── designs/exp_design_<ts>.md          # 实验设计方案（7 段）；消融方案 ablation_plan_<ts>.md
├── bugfixes/bugfix_<ts>.md             # Crash 自修复记录
└── Checkpoints/<server>/<model>/<ts>/  # 终态时 remote_pull.sh --logs-only 拉到本地
    └── <cfg>_<state>_<ts>.log
```

各文件的完整模板统一见 `references/formats.md`。

## 变体配置系统（通用模式）

所有项目共享同一套配置驱动变体机制。

### 硬性规则 — 变体独立性（2026-07-19 起）

**每个模型变体必须互相独立，且有属于自己的唯一 yaml（basename 全局唯一）。**

`resolve_network()` 按 config basename 映射到 `framework.model.<proj>.<basename>` model 包。因此：
- **basename = model 包名 = kill/PID/log 目录的区分键**
- 多个变体共享同一 basename（如 champion / F1-2layer / F2-init00 都叫 `..._posA_l1`）会导致 `pl.sh kill` 无法区分、`.pid_*` 文件冲突、log 目录互相覆盖

**正确做法**：每个变体（即使是纯 config 超参变体，代码与父模型完全一致）也要：
1. 复制父 model 包到独立目录 `<父包名>_<变体标记>/`（代码可 100% 相同，但物理独立，便于将来单独改）
2. config 文件 basename = 新包名（如 `..._posA_l1_2layer.yaml`）
3. 放子目录组织（`configs/Quard/2layer/...`）仅用于归类，basename 仍全局唯一

| 方法 | 适用场景 | 是否复制 model 包 |
|---|---|---|
| YAML 配置标志 | 功能已实现，只需改参数 | **是** — 复制父包到新 basename，config 指过去 |
| seed 变体 | seed 变化、超参扫描 | **是** — 同上 |
| 新 model 包 | 结构性 forward/attention 变更 | 是（本来就是新包） |

> ❌ 旧做法「子目录 + basename 不变 → 共用父 model 包」已废弃：它让多个变体在 kill/PID/log 上无法区分，曾导致误杀（`posA_l1` 的 kill 匹配到 `posA_l1_residual` 等）。

### 创建变体（通用模板）

```bash
cd "$PROJECT_ROOT/<project>/<code_dir>"   # Windows: cd D:/project/<project>/<code_dir>
PARENT=<父 model 包名>          # e.g. model_base1_quard2_c2f_enc_lite_posA_l1
VARIANT=<父包名>_<变体标记>      # e.g. model_base1_quard2_c2f_enc_lite_posA_l1_2layer

# ① 复制父 model 包 → 独立变体包 (代码可不变, 物理独立)
cp -r framework/model/Quard_model/$PARENT framework/model/Quard_model/$VARIANT
rm -rf framework/model/Quard_model/$VARIANT/__pycache__
# 检查并删除 cp 可能产生的同名嵌套目录
[ -d framework/model/Quard_model/$VARIANT/$PARENT ] && rm -rf framework/model/Quard_model/$VARIANT/$PARENT

# ② 创建 config (basename = 新包名, 放子目录归类)
mkdir -p configs/<路径>/<变体标记>
cp configs/<路径>/$PARENT.yaml configs/<路径>/<变体标记>/$VARIANT.yaml
sed -i 's/<旧参数>/<新参数>/' configs/<路径>/<变体标记>/$VARIANT.yaml

# ③ 验证 basename 唯一性 (全项目不能有同名 yaml)
git add -A && git commit -m "Add $VARIANT variant (independent model pkg, unique basename)"
```

**关键**：config basename 全局唯一 → `resolve_network()` 映射到独立包 → kill/PID/log 天然隔离。

## 手动操作 — `pl.sh` 统一入口

推送/训练/恢复/日志/终止/拉取/状态全部通过 skill 内的 `pl.sh` 跨项目执行（转发到各项目 `scripts/` 下的同名脚本）：

```bash
SKILL_DIR="${PROJECT_ROOT:-D:/project}/.claude/skills/songcl_research_pipeline"

PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> sync   <server>                                 # 推送代码
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> train  <server> <config> [gpu_ids] [num_gpus]   # 启动训练
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> resume <server> <config> <gpu_ids> [ckpt]       # 恢复训练
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> log    <server> [config]                        # 查看日志
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> kill   <server> [config]                        # 终止任务(不带 config 则列出)
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> pull   <server>                                 # 拉取产物
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> status <server>                                 # 详细状态
```

**白名单守卫**：`train`/`resume` 的目标卡不在该项目 SERVERS.yaml `allowed_gpus` 内会被直接拒绝（exit 2）；确需越界用 `FORCE=1` 前缀。（等价的项目内原始脚本仍在 `<project>/scripts/`，`songcl_remote_train` skill 亦可用。）

## 典型工作流

```bash
# 1. 检查项目运行状态（或用 songcl_server_status 一次看全部服务器）
PROJECT_ROOT=D:/project python .claude/skills/songcl_research_pipeline/pipeline_monitor.py cluster_project

# 2. 设置自主流水线：写好 pipeline/queue.json → 说"启动 cluster 流水线"
#    → Codex 创建 Task Scheduler 定时任务（tick_full.bat → headless_tick_local.sh → codex exec）
# 3. 终止流水线：说"停止 cluster 流水线"
#    → schtasks /delete（保留队列文件）
```

## 每日状态汇总邮件（可选，每天 23:05）

将三个流水线项目（cluster / lighttext / multiview）的当日状态汇总定时发送到用户邮箱。

### 脚本与凭据

| 文件 | 位置 | 说明 |
|---|---|---|
| `send_mail.py` | 本 skill 目录 | 邮件发送脚本（读凭据，不含敏感信息，随 skill git 版本控制） |
| `smtp_config.json` | `~/.claude/smtp_config.json`（**不进 git**） | SMTP 凭据 |

`~/.claude/smtp_config.json` 格式（QQ 邮箱为例）：

```json
{
  "smtp_host": "smtp.qq.com",
  "smtp_port": 465,
  "from_addr": "<QQ 邮箱>",
  "smtp_code": "<QQ 邮箱 SMTP 授权码>",
  "to_addr": "<收件邮箱>"
}
```

> 授权码（非登录密码）：QQ 邮箱网页版 → 设置 → 账户 → 开启「SMTP 服务」→ 生成 16 位授权码。获取后填入 from_addr + smtp_code 即可，**切勿将授权码写入 skill 内任何文件**。

### 手动发送

```bash
python "C:/Users/chuanle song/.claude/send_mail.py" '<邮件正文>' '邮件主题'
# 或 skill 内副本：
python "$PROJECT_ROOT/.claude/skills/songcl_research_pipeline/send_mail.py" '<正文>' '主题'
```

### 每日定时（会话内 CronCreate）

- 时间：每天 **23:05**（cron `5 23 * * *`），避开整点；recurring + durable 持久化
- 触发 prompt 步骤：① 运行三项目 `pipeline_monitor.sh` + `check_goal.py` ② 生成"当日状态汇总"（三项目 champion/目标/差距 + 当天关键事件 + 需关注事项，中文 Markdown，20-30 行）③ 调 `send_mail.py` 发送到收件邮箱 ④ 确认结果
- **注意**：
  - 系统机制限定 recurring 任务 **7 天自动过期**，到期需重建
  - 定时任务仅在**会话活跃**时触发；关机/会话关闭则当日不发送
  - 内容始终**只读**（只汇报，不决策不写文件），与只读监控模式一致

## 手动干预 — 在闭环中插入人工决策

用户随时可手动介入（kill 实验/改队列/换方向/热更代码等），流水线每次 tick 从文件系统重读状态，下个 tick 自动衔接。**完整话术表、循环衔接行为、研究路线调整、模式切换图见 `references/manual_ops.md`**。硬性要点：

- 每次手动干预后自动 `log_decision.sh` 记录（type=`manual`；用户指定下一批实验用 `manual_batch`，跳过 Phase1/2 分析直接实现+入队）
- 安全边界始终生效：白名单守卫、`.pipeline.lock` 并发锁、running.json 防双推
- 任何代码/config 修改必须 **commit + sync 到所有服务器**（check_code_sync 推送前验证）

## 研究决策指南 — 全自主闭环（硬性规则）

tick 会话中 Codex 自主决策，核心原则：**不等用户、直接执行、全量落文档**。

- 容量补齐目标：**running + claiming + waiting ≥ 可用容量槽位数**；不足时按缺口触发自主实验设计（完整 Phase 0-4 流程、动机推导三问、crash 自修复见 `references/autonomous_design.md`）
  - **可用卡数 = 该项目 SERVERS.yaml 各 gpu_server 的容量槽位总和** = Σ(白名单卡数 × `max_tasks_per_gpu`)，固定值，≠ 当前空闲卡数。当前 cluster: server-4 [0,1]（max=1）→ 2，server-6 [7]（max=2）→ 2，合计容量=4；multiview: server-6 [1,2]（max=1）→ 2。始终以项目 `SERVERS.yaml` 为准，不使用本文快照做调度。
  - 设计按总活跃任务缺口预算，不等卡实际空出来；"空闲卡"（util<10% 且显存<1GB，或单卡多任务下槽位未满）只用于**推送时机**判断，不用于设计预算。
  - 触发: `running + claiming + waiting < capacity + design_buffer`。本轮最多生成 `candidate_budget` 个通过全部准入门槛的结构变体。
  - 同一批变体必须针对可区分的因果假设或机制分支，不得把同一机制的数值扫描、seed 重复、改名副本或纯消融计为多个候选。
  - 合格候选不足时不强行占满 GPU；记录未通过原因，并在下一次冷却窗口后重新审查。
- 每次决策先 `log_decision.sh` 再更新队列；未拍板的问题用 `type=question` 留痕
- 纯 steady 监控不是新的研究决策，不重复写 `type=other`；只有终态、队列、
  策略、路线或实验设计发生变化时才新增决策记录
- **目标：持续提升模型性能，形成完整论文创新证据链。**
