---
name: songcl_research_pipeline
description: Multi-project research pipeline with visible Codex task ticks or legacy background scheduling, monitoring, gated experiments, autonomous design, and crash recovery.
---

# songcl_research_pipeline

## Canonical Installation

Runtime migrated on 2026-09-15 to
`C:/Users/chuanle song/.codex/skills/songcl_research_pipeline`.
Use this directory for all scripts and references. Older examples below containing
`D:/project/.claude/skills/songcl_research_pipeline` are historical paths, not the
current executable location. Shell launchers resolve their own directory.
The `.agents/skills` installation is a synchronized discovery copy.

## Experiment-First Opt-In (2026-10-21)

The approved `pipeline/closure_policy.json` experiment_first policy is frozen
into each new foreground snapshot. When enabled, use
`references/experiment_first.md` instead of the legacy scientific admission,
reserve/cooldown and exhaustive design rules below. Keep the foreground lease,
current resource/data/budget/bans, native YAML task configuration, version/evidence
integrity and verified launch contract. Old in-flight snapshots remain legacy.
The ordinary loop is observe/dispatch, implement when the ready backlog is short,
native smoke and admission, then report/finish. Scoped project operations reuse
one explicit authorization; training efficacy is measured after training.

## Executable Closure (2026-09-15)

Projects opting in through `pipeline/closure_policy.json` use
`references/closure.md`: persistent candidate stages, hashed admission receipts,
safe ff-only synchronization, candidate-only YAML adaptation, native training
progress checks and postflight validation. `pipeline/research_work.json` pending
actions resume in event mode without waiting for a new design cycle.
Admission requires diagnosis, controls, native backward execution, resources,
independence and goal constraints. Full derivation and literature review are
recommended support but are not dispatch blockers.
Existing running experiments are not retroactively gated. Other projects keep
their existing deployment behavior until explicitly enabled.
Reconcile-only success does not clear an unsuccessful research tick.
Tests: `python -B -m unittest test_foreground_tick test_closure test_tick_context test_closure_multiview` from this skill directory.

## Research Throughput And Local Revisions

Due work is ordered by executable stage, nearest admission/deployment first;
authorization/evidence rechecks come after runnable candidates. Keep advancing
the selected candidate in this tick instead of spreading one stage over each tick.
Due held IDs do not suppress independent design when bounded preparation has room.
Evidenced `numerical_control_failure` holds with implementation/inconclusive scope
are parked as research holds, not runnable reserve or new human permission requests.
Unknown/malformed blocks still require review; all holds still count toward the
pending limit. Revision archives may distinguish frozen inputs from fresh test
outputs using `result_evidence`; no completed outcome or original evidence is erased.
Postflight closes against this tick's receipt-backed admission budget, not the
whole capacity target, and rejects excess new admissions. After quota completion
or near the real deadline, an exact current `tick_handoff` can preserve untouched
executable backlog for the next tick; genuine progress elsewhere and all integrity
checks remain required. Do not spread token/evidence edits across every candidate
just to satisfy bookkeeping. See closure.md's Focused Work And Carryover.
Same-tick successful archives retain their receipt and launch proof and count
once toward the admission quota; incomplete or unverified archives do not.
Historical rejection requires reopen authorization even without revisions, checked
before dispatch as well as at finish. An unchanged completed revision and its
snapshot-bound grant remain historical evidence after goal/owner changes; this
never authorizes a new revision, stage transition or launch.

For closure-enabled projects with `research_on_capacity_gap=true`, context now
prepares a bounded research reserve even while training is full. The default
`research_reserve_target` is 2, independently of the unchanged training admission
budget. `reserve_only=true` allows preparation, not queue additions or launches;
phase holds, explicit project limits and GPU permissions still apply. Set the
target to 0 in project policy to disable reserve preparation.
Evidenced human/resource holds are parked separately, including
`human_revision_authorization`; they do not fill the actionable reserve.
`research_pending_limit` bounds all unfinished candidates plus waiting/claiming
tasks, deduplicated by experiment ID (default max(8, 2 * reserve target)).
It prevents unlimited replacement candidates without making one held route
freeze unrelated authorized work. Existing records and permissions are unchanged.

An unsuccessful realization is not automatically a falsified mechanism.
Distinguish `failure_scope=implementation`, `inconclusive`, and `hypothesis`.
Evidence-backed local changes may use the same stable ID with at most two
pre-registered implementation revisions by default. Preserve all negative
evidence; retest affected gates and bind a new receipt to the tested revision.
Small layer/connection changes need not be independently novel when repairing
the original mechanism. This does not authorize tuning, validation-based
selection, or reopening banned/historically rejected work. See
`references/closure.md` sections Research Reserve and Implementation Revisions.

Unchanged recognized external blocks receive bounded rechecks (resource: one
hour; human evidence/authorization: four hours). Goal/server changes, resource
queue changes and candidate `wake_paths` changes wake them earlier. These are
research wakeups, never evidence of free GPUs or scientific PASS. The compact
context/report includes cumulative stage and failure-scope counts, explicitly
not an acceptance or success rate.
When queued work fills preparation capacity or the total pending limit is reached,
and only evidenced external holds remain, validate waiting in event mode, then
use steady polling. A due blocked retry is an evidence check, not a demand for
new research. With spare preparation budget, continue independent authorized
work; a candidate-only cooldown must not freeze that work. Scientific no-gain
cooldowns and project/phase holds remain in force. Reuse actual scoped permission;
ask once only for a missing operation, never treating a timer as authorization.
Connection/deployment failures are visible separately from candidate shortages.
Archived successful dependencies now resolve without remaining in the queue.
Interrupted dispatches retain durable phase/PID evidence: known pre-launch work
can recover, while uncertain launches require reconciliation, never blind retry.
Deployment also verifies actual runtime source, not just a commit or marker;
only configured deterministic YAML path adaptation is exempted. Observation,
admission, dependency, claim and launch failures appear separately in reports.
Dispatch holds are rechecked inside multi-GPU loops, and uncertain launches keep
their concurrency slot. Stop confirmation and interrupted archival are explicit
recovery states: preserve live tasks, replay frozen local archive journals under
lock, and never turn a busy monitor or read-only query into successful mutation.
See foreground.md and visible_reporting.md for the handoff contract.
Foreground ticks require an enabled closure policy before mutating preflight.
Missing/disabled policy is reported as `CLOSURE_NOT_ENABLED`, never as a PASS.
Do not create or enable a policy blindly: review the project's ledger/schema,
launcher and deployment mappings first. Existing training is not stopped.

研究迭代流水线，跨平台支持 Linux（`/home/songcl/3dres/project/`）和 Windows（`D:/project`）。

> 链条定位：`songcl_research_bootstrap`(0→1 调研/复现/首批实验) → `songcl_deploy_project`(接入平台) → **本 skill**(1→N 自动迭代闭环)。全新任务从 bootstrap 进入，移交前用其 `bootstrap_check.sh` 验收。

## 文件地图（按需加载，不要一次全读）

| 文件 | 内容 | 什么时候读 |
|---|---|---|
| 本文件 | 触发规则、核心脚本、queue/goal schema、硬性规则、跨平台差异 | 总是 |
| `references/foreground.md` | 前台 tick 的唯一执行契约、模式分支、锁恢复、收尾与报告 | 项目 execution_mode 为 foreground 时 |
| `references/visible_reporting.md` | 面向用户的中文简报：结论、实验进展、本轮成果、下一步 | 向用户展示研究进展时；完整六段仍留档 |
| `references/heartbeat_prompts.md` | 四个前台定时任务的完整提示词、绑定参考及同步规则 | 创建、检查或更新前台定时提示词时；仅加载相关项目 |
| `references/formats.md` | 全部 7 套文档模板（tick 报告/终态分析/实验设计/动机审查/消融方案/决策/bugfix） | 生成任何 pipeline 文档前 |
| `references/autonomous_design.md` | 自主实验设计 Phase 0-4、crash 自修复、Phase 2 消融流程、决策日志示例 | 队列深度不足 / champion 达标时 |
| `references/manual_ops.md` | 手动干预话术表、循环衔接行为、研究路线调整、模式切换 | 用户前台提出 kill/改队列/换方向等要求时 |

## 触发规则 — 按项目执行模式选择

**前台接管优先规则（2026-09-27）**：若项目
`pipeline/execution_mode.json` 的 `mode` 为 `foreground`，本节下方旧版
Windows 后台启动规则不适用。读取 `references/foreground.md`，由绑定任务的
heartbeat 直接执行研究 tick，用 `foreground_tick.py` 完成接管检查、preflight
和 postflight；实验设计与证据必须在任务中可见。不得重新启用该项目的
`Pipeline-<project>` 后台调度，不得调用嵌套 `codex exec`。尚在运行的旧 tick
自然结束后再接管，不终止远端训练。未迁移项目保持原来的启停状态。

前台定时提示词维护在 [references/heartbeat_prompts.md](references/heartbeat_prompts.md)。
修改提示词时同步更新对应应用自动化并核对保存结果；只改 skill 文档不会自动更新
已保存的定时任务。普通 tick 按 `references/foreground.md` 执行，不必加载四份提示词。

**前台 token 效率规则**：前台普通 tick 读到本节后转入 foreground.md，不加载下方
旧后台操作及无关 schema。begin 使用 `--auto-steady`，模型先读至多 12KB 的
`.tick_model_view.json`，候选按 ID / 分页查；完整快照仅供程序校验。已证实无信息增益
可按 closure.md 提前收尾与短期冷却，不为了耗尽 deadline 重复设计。事实表由脚本生成，
模型只补研究动作/决策，完整六段报告留档；会话展示 `references/visible_reporting.md`
的中文简报，不粘贴原始日志和内部校验字段。每轮收据保留可见用量及实际产出。

### 旧版后台模式（仅非 foreground 项目）

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
- 默认决策模型为 `gpt-6-sol`；可通过 `CODEX_PIPELINE_MODEL` 覆盖
- 默认模型不可用时自动降级到 `deepseek-flash`（DeepSeek V4.1 Flash）；可通过 `CODEX_FALLBACK_MODEL` 覆盖，设为空字符串即禁用降级
- 定时 tick 默认每轮使用新的 Codex 线程（`CODEX_FRESH_THREAD=1`），避免长会话上下文无限增长；研究状态由项目文件与 `codex_memory.md` 跨轮传递
- 三个项目会话保留为状态通知入口，不再承载每小时的完整研究 tick
- 关键研究状态同时写入 `<project>/pipeline/codex_memory.md`；项目文件始终高于线程记忆
- **不要**扫描 SERVERS.yaml 自动给所有项目建调度 — 只建用户明确提到的项目

### 跨平台路径

所有脚本通过 `PROJECT_ROOT` 环境变量适配，Windows: `D:/project`，Linux: `/home/songcl/3dres/project`。`tick_full.bat` 自动设置。

### GPU 资源分配（历史示例，不作为授权）

以下表格可能过时。任何模式均以当前项目 `goal.json`、`SERVERS.yaml`、
用户最新授权和实时占用/租约核验为准；白名单不代表空闲，也不代表独占。

| 项目 | 服务器 | GPU 卡 | 容量 |
|------|--------|--------|------|
| cluster_project | server-6 [7] | H100 GPU7 | 2 |
| lighttext_project | server-2 [0,1], server-3 [0,1] | 3090×4 | 4 |
| multiview_project | server-6 [4] | H100 GPU4 | 2 |

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
PROJECT_ROOT=D:/project python "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/pipeline_monitor.py" cluster_project --read-only
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
PROJECT_ROOT=D:/project bash "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh" \
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
- 若存在待续候选且同时满足容量缺口设计条件，本轮为 `design`：先续做候选，
  再在本 tick 内反复诊断和筛选独立假设；一次未准入不意味着等待下轮。
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
| `CODEX_PIPELINE_MODEL` | `gpt-6-sol` | 后台决策模型 |
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
- 候选预算只限制新增准入数量，不限制本轮不同证据路线的诊断尝试；
  合格候选不足时允许留空并记录已试测试、反证或外部阻塞

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
    allowed_gpus: [4]              # server-6 专用卡
    max_tasks_per_gpu: 2           # H100 80GB: 单卡可同时跑 2 个任务
    max_tasks: 2                   # 可选: 该服务器本项目总并发上限
    dispatch_enabled: false        # 继续监控已有任务，但不计容量、不推送新任务
```

- **`max_tasks_per_gpu`（可选，默认 1）**：该服务器每张卡最多同时承载多少个本项目任务。H100 80GB 等大卡显存有富余（单任务 ~20GB），可设 >1 让单卡跑多个训练。
- **`max_tasks`（可选）**：该服务器上本项目并发任务总数上限。适合“任意卡都可选，但整台服务器最多同时跑 N 个任务”的策略；容量计算会按此值截断，避免把多卡白名单误算成很多槽位。
  - `=1`（默认）: 一卡一任务，**整卡空闲**（util<10% 且显存<1GB 且无本项目进程）才推
  - `>1`: 单卡多任务，该卡本项目任务数 < max **且** 显存余量 > 单任务需求(~20GB) 即可再推，同一 tick 可连续推满槽位
  - 现有配置示例：multiview server-6 GPU4 = 2；cluster 以项目 `SERVERS.yaml` 为准
- 未写 `allowed_gpus` = 不限制（兼容旧项目）；跳板机在服务器项配 `jumphost: user@host`，SSH/scp 自动走 `-J`
- `dispatch_enabled: false` = 监控/早停已有任务，但该服务器不计入设计容量，也不接收新队列任务。用于迁移期间让旧任务自然结束。
- **各项目当前的白名单、主训练服务器、IP 等一律以该项目 `SERVERS.yaml` 为唯一事实源**（本文件不维护快照）；跨项目总览用 `songcl_server_status` skill
- 不假定正式 skill 已纳入 Git；修改前核对实际版本管理状态，不能用旧 `.claude` 仓库覆盖正式入口。

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

**项目研究产物必须在所属项目的 `<project>/` 目录内。**
共享 skill 的维护文件只写正式 skill 目录，不混入其他项目。

| 文件类型 | 允许路径 | 示例 |
|---|---|---|
| 项目文档/tick报告/决策/设计 | `<project>/pipeline/` | 现有结构不动 |
| 项目代码/配置 | `<project>/Cluster/` 或 `<project>/lighttext/` 等 | 代码仓 |
| 训练产物（checkpoint/日志） | `<project>/Checkpoints/` | `pl.sh pull` 的落盘位 |
| 跨项目工具/脚本 | 正式 `.codex/skills/` 对应 skill 目录 | `foreground_tick.py` 等 |
| 临时文件 | `$TMPDIR` / `%TEMP%`（确认可清理） | 编译中间产物 |

**禁止**：
- 在项目根目录直接创建文件
- 在任意路径（如 `/tmp/` 等）写入持久化产物
- 在服务器远端（server-2/3/4/5/6）的 `/tmp/` 或 `$HOME` 下创建不属于该项目的文件

跨项目管理工具（如 `cluster_dashboard.py`）归入正式对应 skill 目录或独立脚本目录（`<project>/scripts/`）。

## 代码同步规则（硬性规则）

**仅向该候选已获授权、实际需要运行的目标服务器同步**，不向所有可用服务器广播。
纯设计或只读查询不触发同步。部署前核对代码、配置、提交与准入凭据的一致性；
只提交本次候选已测试且属于本次工作的改动，不自动提交用户其他改动。
closure 项目使用 `references/closure.md` 的候选限定配置处理和安全 fast-forward
同步，由门控调度器验证后启动。冲突、分叉或同步失败须记录并阻断部署，
不得用 reset、clean、stash 或忽略退出码来绕过。

## 统一输出格式 — Tick 报告（硬性规则）

- 已取得写权限和本轮租约的研究 tick 写 `pipeline/reports/summary_<YYYYMMDD-HHMMSS>.md`。
- 只读状态查询、未取得锁或 preflight 失败时只在任务中报告，不写报告、记忆或队列。用户明确指定 `songcl_project_status` 的 0-4 母版时遵循该母版。
- **留档报告保持完整六段格式（0-5）**，模板与逐段强制检查见 `references/formats.md#1-tick-报告`，不修改机器校验结构。
- **会话默认展示中文易读简报**：一句结论、实验进展、本轮成果、下一步或需确认事项，见 `references/visible_reporting.md`。不要求用户阅读六段原始报告；用户要求明细或特定母版时再按要求展开。
- 报告清理只能在拥有写权限和租约时按保留策略执行；不得在只读查询或锁冲突时清理。

## 输出产物（每项目 `pipeline/` 目录下）

```
<project>/pipeline/
├── queue.json                          # 队列（仅 waiting 排队，FIFO，按服务器分组）
├── codex_memory.md                     # 跨 tick 持久研究记忆（线程失效时的恢复源）
├── tick_receipts/<token>.json          # 前台收尾收据：校验结果、快照哈希、提交与释放状态
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
SKILL_DIR="C:/Users/chuanle song/.codex/skills/songcl_research_pipeline"

PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> sync   <server>                                 # 推送代码
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> train  <server> <config> [gpu_ids] [num_gpus]   # 启动训练
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> resume <server> <config> <gpu_ids> [ckpt]       # 恢复训练
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> log    <server> [config]                        # 查看日志
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> kill   <server> [config]                        # 终止任务(不带 config 则列出)
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> pull   <server>                                 # 拉取产物
PROJECT_ROOT="$PROJECT_ROOT" bash "$SKILL_DIR/pl.sh" <project> status <server>                                 # 详细状态
```

**白名单守卫**：`train`/`resume` 的目标卡不在该项目 SERVERS.yaml `allowed_gpus` 内会被拒绝；自主 tick 不得使用 `FORCE=1` 绕过。资源变更须用户明确授权。以上是手动入口参考，不能绕过 closure 的准入凭据和门控调度。

## 典型工作流

1. 只读查询使用正式 `pipeline_monitor.py <project> --read-only`。
2. 前台研究按 `references/foreground.md` 执行 begin、研究、finish/abort，不直接重复 preflight。
3. 定时任务的创建和维护按 `references/heartbeat_prompts.md`，绑定现有原任务。
4. 停止前台流水线时暂停对应 heartbeat，保留队列与远端训练；停止训练是另一项需明确授权的操作。

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
python "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/send_mail.py" '<邮件正文>' '主题'
```

### 可选邮件自动化

只在用户明确要求时用应用自动化工具维护；频率、时区、项目范围、收件人和
通知方式以保存配置为准，不因加载 skill 自动创建邮件任务。只读检查使用正式
`pipeline_monitor.py <project> --read-only` 与 `check_goal.py`，不用旧 shell
入口。发送前核对授权与凭据来源，报告实际成功/失败，不泄露凭据；不假定
固定到期时间或关机时仍能执行。

## 手动干预 — 在闭环中插入人工决策

用户随时可手动介入（kill 实验/改队列/换方向/热更代码等），流水线每次 tick 从文件系统重读状态，下个 tick 自动衔接。**完整话术表、循环衔接行为、研究路线调整、模式切换图见 `references/manual_ops.md`**。硬性要点：

- 每次手动干预后自动 `log_decision.sh` 记录（type=`manual`；用户指定下一批实验用 `manual_batch`，跳过 Phase1/2 分析直接实现+入队）
- 安全边界始终生效：白名单守卫、`.pipeline.lock` 并发锁、running.json 防双推
- 代码/config 的部署遵循上述候选限定同步规则，只操作获授权的实际目标服务器。

## 研究决策指南 — 全自主闭环（硬性规则）

tick 会话中 Codex 自主决策，核心原则：**不等用户、直接执行、全量落文档**。

- 容量补齐目标：**running + claiming + waiting ≥ 可用容量槽位数**；不足时按缺口触发自主实验设计（完整 Phase 0-4 流程、动机推导三问、crash 自修复见 `references/autonomous_design.md`）
  - **可用卡数 = 该项目 SERVERS.yaml 中 `dispatch_enabled != false` 的 gpu_server 容量槽位总和** = Σ(白名单卡数 × `max_tasks_per_gpu`)，固定值，≠ 当前空闲卡数。当前 cluster: server-6 [7]（max=2）→ 2；server-4 已从本项目白名单移除，容量 0。multiview: server-6 [4]（max=2）→ 2。始终以项目 `SERVERS.yaml` 为准，不使用本文快照做调度。
  - 设计按总活跃任务缺口预算，不等卡实际空出来；"空闲卡"（util<10% 且显存<1GB，或单卡多任务下槽位未满）只用于**推送时机**判断，不用于设计预算。
  - 触发: `running + claiming + waiting < capacity + design_buffer`。本轮最多生成 `candidate_budget` 个通过全部硬性准入门槛的结构变体；完整理论推导与文献新颖性检索只作为建议项。硬性门槛验证机制诊断、匹配对照、原生后向、资源、独立性和 goal 约束，不要求训练前达到固定任务收益阈值（如 +0.05/+0.02）。启动前预注册训练后指标、对照、重复/场景聚类不确定性和有害子组规则；证据不足标为不确定，不凭单个场景自动否决或宣布收益。旧拒绝仅在同一稳定 ID 下重审，不自动翻案（见 `references/closure.md` Gate Calibration）。
  - 同一批变体必须针对可区分的因果假设或机制分支，不得把同一机制的数值扫描、seed 重复、改名副本或纯消融计为多个候选。
  - 合格候选不足时不强行占满 GPU；记录未通过原因，并在下一次冷却窗口后重新审查。
- 每次决策先 `log_decision.sh` 再更新队列；未拍板的问题用 `type=question` 留痕
- 纯 steady 监控不是新的研究决策，不重复写 `type=other`；只有终态、队列、
  策略、路线或实验设计发生变化时才新增决策记录
- **目标：持续提升模型性能，形成完整论文创新证据链。**
