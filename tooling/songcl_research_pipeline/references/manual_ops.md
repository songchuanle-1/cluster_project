# 手动干预手册 — songcl_research_pipeline

闭环并不意味着你只能旁观。任何时候你都可以手动介入，**流水线会自动感知你的操作并在下一个 tick 无缝衔接**。

## 核心原则

> 流水线每次 tick 都从文件系统重新读取状态（queue.json / running.json / GPU 进程），不做内存缓存。所以你的任何手动改动，下一次 tick 都会自然生效，不需要"通知"流水线。

## 常见手动操作及触发词

对着 Codex 说以下话术即可执行，无需自己敲命令：

| 你想做的事 | 对 Codex 说 | 实际执行 | 循环如何衔接 |
|---|---|---|---|
| 提前终止某个实验 | "kill cluster 的 C1-layerscale" | ①kill ②立刻拉日志生成终态分析 ③更新 queue.json ④推送下一个 waiting ⑤depth不足则自主设计入队 | 不依赖 cron tick，一条龙闭环 |
| 查看实验详细指标 | "C1-layerscale 现在多少了" | SSH 远端 tail 日志 | 不影响循环 |
| 查看所有项目状态 | "服务器状态" / "pipeline 报告" | 默认只读，按 visible_reporting.md 给中文简报；指定母版时按要求展开 | 不改流水线；另获保存授权且无写入冲突时才写 `_manual.md` |
| 调整队列顺序 | "把 B5-residual 排到队列第一个" | 编辑 `pipeline/queue.json` 移动顺序 | 下个 tick 按新顺序 FIFO 推送 |
| 新增一个实验到队列 | "把 xxx config 加入 cluster 队列" | 追加到 `pipeline/queue.json` 队尾 | 下个 tick 出现在 waiting 列表 |
| 从队列移除一个实验 | "把 seed2026 从队列里删掉" | 从 `pipeline/queue.json` 删除该条目 | 下个 tick 不再出现 |
| 修改实验的 patience | "把 C1 的 patience 改成 15" | 修改 `pipeline/queue.json` 中任务级 patience | 下个 tick 用新 patience |
| 跳过依赖强制推送 | "不等 B5 了，直接推 PosA-seed2026" | 删除 depends_on 字段 → 保存 | 下个 tick 依赖检查通过即可推送 |
| 暂停某项目流水线 | "暂停 cluster 流水线" | `CronDelete` 该项目的 cron | 不再 tick，GPU 上的实验继续跑但你手动管理 |
| 恢复流水线 | "恢复 cluster 流水线" | `CronCreate` 重建 cron | 从下个 tick 继续自主运行 |
| 暂停所有流水线 | "暂停所有流水线" | 全部 `CronDelete` | 全部进入手动模式 |
| 在指定卡上临时跑一个实验 | "在 server-4 GPU1 上跑 xxx config" | `pl.sh train`（白名单检查，越界需 `FORCE=1`）| 下个 tick 检测到进程 → 纳入 running 监控 |
| 重新 sync 代码到某台服务器 | "sync cluster 代码到 server-4" | `pl.sh sync server-4` | 下次推送前 check_code_sync 自动通过 |
| 批量对比所有实验结果 | "对比 cluster 所有实验" | 分析 `experiments.csv` + `pipeline/analyses/` | 不影响循环 |

## 手动操作必须落日志

每次手动干预后，Codex 自动调用 `log_decision.sh` 记录，类型使用 `manual`：

```bash
# 通用形式（自动适配 Linux/Windows PROJECT_ROOT）:
bash "${PROJECT_ROOT:-/home/songcl/3dres/project}/.claude/skills/songcl_research_pipeline/log_decision.sh" \
  cluster_project manual \
  "手动 kill C1-layerscale" \
  "pl.sh kill server-4 C1-layerscale" \
  "LayerScale 最高 0.4868 < baseline 0.5012" \
  "C1-layerscale final best: 0.4868"
```

## Kill 实验 — 立刻闭环（不依赖 cron tick）

用户说 "kill" 后，**不等 cron tick，立刻一条龙执行**：

```
你说 "kill"
  → ① pl.sh kill   (终止远端进程)
  → ② 立刻拉日志   (pl.sh pull --logs-only, 不依赖 10min 防抖)
  → ③ 终态分析     (读取 pulled log → 写 pipeline/analyses/<id>_done_earlystop_<ts>.md)
  → ④ 更新队列     (queue.json: running→done_earlystop, 写入 final_best + finished_at)
  → ⑤ GPU 空闲     → 立刻推送下一个 waiting (pl.sh train)
  → ⑥ capacity 检查 (running+claiming+waiting < capacity → 按缺口自主设计结构变体 → 入队)
```

### 手动干预时循环的行为

```
你手动 kill 一个实验
  → 立刻: 终态分析 + GPU 释放 + 队列推送 (+ 自主设计如需)
  → 下次 cron tick: 读到终态状态, 继续监控

你手动编辑了 queue.json
  → 下个 tick: load_queue() 读到新内容
  → 按新顺序/新 patience/新 depend_on 执行
  → 无需额外操作
```

```
你手动启动了一个实验（不在队列中）
  → 下个 tick: 检测到进程（匹配 config）→ 自动创建 experiment JSON
  → 更新 running.json
  → 开始监控早停
  → 如果卡被占满 → 队列不推送
```

## 安全边界

- **白名单守卫**始终生效：`pl.sh train` 的目标卡不在 `allowed_gpus` 会被拒绝
- **并发锁**始终生效：手动操作和 cron tick 同时运行时，后到达的会跳过
- **不会双推**：running.json + .pipeline.lock 双重保护
- 手动操作不会破坏队列数据：queue.json 随时可回滚（git）

---

# 调整实验实现与研究路线

以上是操作层面的手动干预。以下是你作为研究者对**实验方向和代码实现**做结构性调整的场景。

## 修改实验配置或代码

| 场景 | 对 Codex 说 | 执行流程 |
|---|---|---|
| 修改队列中某个实验的 config | "把 C1 的 config 里的 XXX 参数改成 YYY" | Codex 直接编辑 YAML → commit → sync 到服务器 → 下个 tick 推送用的是新 config |
| 修改已运行的实验代码（热更新） | "把 layerscale 的实现改成 XX，重启 C1" | edit 代码 → commit → sync → `pl.sh kill` 停旧进程 → 手动 `pl.sh train` 或回 waiting 等推送 |
| 新增一个变体实现 | "加一个 cosine_annealing gate 变体，叫 C3" | 写新 model 代码 + config → commit → sync → 入队 → 下个 tick 推送 |
| 回滚某次改动 | "C1 的 layerscale 代码回滚到上一版" | `git revert` → commit → sync → 如果已在跑则 kill 重跑 |
| 改完代码后跑一个验证实验 | "sync 代码到 server-4，然后跑 xxx config 试一下" | sync → train（不走队列，临时占卡验证） |

**关键规则**：任何代码或 config 修改，必须 **commit + sync 到所有服务器**，确保下次推送时远端跑的是最新代码。check_code_sync 会在推送前验证，不一致则拒绝推送。

## 调整研究方向

| 场景 | 对 Codex 说 | 执行流程 |
|---|---|---|
| 暂停自主实验设计（保留监控） | "先不要自动设计新实验了" | Cron 保留，但下次队列深度不足时不触发自主设计，只报告"队列不足"让用户决定 |
| 恢复自主设计 | "可以继续自动设计实验了" | 恢复正常闭环 |
| 改变研究方向 | "不要继续搞 gate 了，换成探索 position encoding" | Codex 记录路线变更（`log_decision type=route_change`）→ 更新 `docs/roadmap.md`（如有）→ 下次自主设计基于新方向 |
| 指定下一批实验 | "下一批跑这三个: C3-cosine-gate, C4-residual-v2, D1-posD" | Codex 跳过 Phase1/2 分析，直接实现 + 入队 |
| 设定baseline/champion | "用 B1 posA_l1 (0.5012) 作为 champion，新实验对比它" | 写入 `pipeline/queue.json` 的 `champion` 字段或项目约定 → 后续终态分析的 comparison 段自动使用 |
| 看一下当前 roadmap | "cluster 的 roadmap 是什么" | 读 `docs/roadmap.md` 或 `pipeline/designs/` 最新设计文档 → 输出当前方向 + 已完成/待做 |
| 更新 roadmap | "更新 cluster roadmap: Phase2 加一个 cosine schedule 消融" | 编辑 `docs/roadmap.md` → commit |
| 放弃某条路线并归档原因 | "放弃 gate 路线，结论是 XXX" | `log_decision type=route_change` → 更新 roadmap → 清理队列中该路线的 waiting 任务 |

## 手动标记完成 / 修改目标

用户随时可以说 **"cluster 实验完成了"** / **"目标达成了"**，Codex 执行：

1. 运行 `check_goal.py` 输出当前状态
2. 生成 `goal_reached_<ts>.md` 证据链报告
3. 生成 `docs/paper_outline.md` 论文大纲
4. cron 保留仅监控

如果用户说 **"cluster 目标改成 mIoU ≥ 0.53"**，直接编辑 `pipeline/goal.json` 的 target 字段。

## 自主设计与手动设计的协作规则

当用户指定了下一批实验，Codex **不再触发 Phase1/2 分析**，直接进入 Phase3（实现+入队），但要：

1. 校验 config 是否存在（不存在则创建）
2. 检查是否有代码依赖（新 model 包等）
3. commit + sync 到所有服务器
4. 追加到 `pipeline/queue.json` 队尾
5. 记录 `log_decision type=manual_batch`：谁设计的、为什么要跑这些

**不会出现的错误**：用户指定了实验但流水线又自动设计了另一批 → 因为用户指定实验入队后队列深度≥3，不会触发自主设计。

## 手动与自动的状态切换

```
┌──────────────┐     "暂停自主设计"     ┌──────────────────┐
│  全自主闭环   │ ──────────────────→  │  监控+手动决策    │
│  (cron tick)  │                      │  (cron 继续跑,     │
│  监控+推送+   │ ←────────────────── │   但不自主设计      │
│  自主设计     │   "恢复自主设计"      │   新实验)          │
└──────────────┘                      └──────────────────┘
        │                                      │
        │   "暂停流水线"                         │   "暂停流水线"
        ↓                                      ↓
┌──────────────────────────────────────────────────┐
│                  完全手动                         │
│    (无 cron, GPU 上实验继续跑但无监控,            │
│     用户完全手动管理 kill/推送/设计)               │
└──────────────────────────────────────────────────┘
```

三种模式切换通过 Codex 对话即可，不涉及改配置文件。
